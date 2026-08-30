package com.llmcouncil.mobile.domain

import com.llmcouncil.mobile.data.ModelHealthDb
import com.llmcouncil.mobile.data.OpenRouterClient
import com.llmcouncil.mobile.data.SecureSettings
import com.llmcouncil.mobile.model.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import kotlin.coroutines.coroutineContext
import kotlin.math.round

class RepoAuditEngine(
    private val ai: OpenRouterClient,
    private val settings: SecureSettings,
    private val healthDb: ModelHealthDb
) {
    companion object {
        private const val BATCH_CHAR_BUDGET = 30_000
        private const val FILE_PART_CHARS = 18_000
        private const val BATCH_OUTPUT_TOKENS = 1800
        private const val SYNTHESIS_OUTPUT_TOKENS = 2800
        private const val PEER_OUTPUT_TOKENS = 1800
        private const val VERIFY_OUTPUT_TOKENS = 2200
        private const val FINAL_OUTPUT_TOKENS = 4200
    }

    private data class AuditUnit(val path: String, val part: Int, val parts: Int, val category: String, val text: String)

    suspend fun run(snapshot: RepoSnapshot, onUpdate: suspend (RepoAuditRun) -> Unit): RepoAuditRun {
        val configured = settings.councilModels()
        if (configured.size < 2) return RepoAuditRun(
            repoFullName = snapshot.repo.fullName, ref = snapshot.ref, commitSha = snapshot.commitSha,
            stage = RepoAuditStage.ERROR, requiredFiles = snapshot.requiredFiles.size, excludedFiles = snapshot.excluded.size,
            errors = mapOf("Council" to "At least two council models are required for repository audit."), finishedAt = System.currentTimeMillis()
        ).also { onUpdate(it) }

        var run = RepoAuditRun(
            repoFullName = snapshot.repo.fullName,
            ref = snapshot.ref,
            commitSha = snapshot.commitSha,
            stage = RepoAuditStage.INDEPENDENT,
            requiredFiles = snapshot.requiredFiles.size,
            excludedFiles = snapshot.excluded.size
        )
        onUpdate(run)
        val units = buildUnits(snapshot)
        val audits = mutableListOf<ModelRepoAudit>()

        for (model in configured) {
            coroutineContext.ensureActive()
            val result = auditOneModel(model, snapshot, units) { partial ->
                val current = audits + partial
                run = run.copy(modelAudits = current)
                onUpdate(run)
            }
            audits += result
            run = run.copy(modelAudits = audits.toList())
            onUpdate(run)
        }

        val complete = audits.filter { it.complete && it.report.isNotBlank() }
        if (complete.size < 2) {
            return run.copy(
                stage = RepoAuditStage.ERROR,
                errors = run.errors + ("Audit" to "Fewer than two models completed 100% required-file coverage. Peer review was not allowed to start."),
                finishedAt = System.currentTimeMillis()
            ).also { onUpdate(it) }
        }

        run = run.copy(stage = RepoAuditStage.PEER_REVIEW); onUpdate(run)
        val labelToModel = linkedMapOf<String, String>()
        val reviewCorpus = buildString {
            complete.forEachIndexed { i, audit ->
                val label = "Audit ${('A'.code + i).toChar()}"
                labelToModel[label] = audit.model
                append("\n\n$label:\n${audit.report.take(14_000)}")
            }
        }
        val peerPrompt = """You are peer-reviewing independent exhaustive repository audits.
Repository: ${snapshot.repo.fullName}
Commit: ${snapshot.commitSha}
All admitted audits below reached 100% required-file coverage enforced by the application.

$reviewCorpus

Evaluate each audit for correctness, evidence quality, missed risks, false positives, architectural understanding, tests, security, concurrency/state, performance, dependencies, CI/deployment and documentation-code drift.
At the end output exactly:
FINAL RANKING:
1. Audit X
2. Audit Y
...
Do not use model identity as a quality signal."""

        val peer = complete.map { it.model }.map { model ->
            trackedReview(model, peerPrompt, PEER_OUTPUT_TOKENS, "peer-review")
        }
        val aggregate = aggregate(peer, labelToModel)
        run = run.copy(peerReviews = peer, aggregate = aggregate); onUpdate(run)

        run = run.copy(stage = RepoAuditStage.VERIFY); onUpdate(run)
        val verificationModel = chooseChairman(complete.map { it.model })
        val verifyPrompt = """You are the adversarial verification pass for a repository audit.
Repository: ${snapshot.repo.fullName}
Commit: ${snapshot.commitSha}

Independent exhaustive audits:
${complete.joinToString("\n\n---\n\n") { "MODEL AUDIT ${it.model}:\n${it.report.take(14_000)}" }}

Peer reviews:
${peer.filter { it.error == null }.joinToString("\n\n") { it.text.take(8_000) }}

Your job is NOT to add more speculative findings. Challenge the important claims. Identify which claims are strongly supported by concrete repository evidence, which are plausible but need confirmation, which conflict with other evidence, and which look like false positives. Do not treat model agreement as proof. Produce a verification memorandum with sections: Confirmed, Needs confirmation, Disputed/likely false positive, Evidence gaps."""
        val verification = trackedText(verificationModel, verifyPrompt, VERIFY_OUTPUT_TOKENS, "verification")

        run = run.copy(stage = RepoAuditStage.CHAIRMAN); onUpdate(run)
        val finalPrompt = """You are Chairman of an evidence-driven repository audit council.
Repository: ${snapshot.repo.fullName}
Ref: ${snapshot.ref}
Commit SHA: ${snapshot.commitSha}
Required files audited: ${snapshot.requiredFiles.size}
Explicitly excluded files: ${snapshot.excluded.size}

Independent 100%-coverage audits:
${complete.joinToString("\n\n---\n\n") { "${it.model}:\n${it.report.take(14_000)}" }}

Aggregate peer ranking:
${aggregate.mapIndexed { i, r -> "${i+1}. ${r.model} avg=${r.averageRank} votes=${r.votes}" }.joinToString("\n")}

Adversarial verification memorandum:
$verification

Produce the final repository audit. Requirements:
- separate Confirmed Findings from Hypotheses/Needs Confirmation;
- group duplicate findings rather than counting the same issue repeatedly;
- preserve file paths/symbol/evidence references from source audits;
- include severity and category;
- include architecture summary, correctness, concurrency/state, security, tests, dependencies, performance, CI/deployment, documentation-code drift and maintainability;
- include a Coverage section stating the exact commit SHA and required/excluded counts;
- explicitly state disagreements instead of hiding them;
- finish with a prioritised remediation plan.
Never claim a file was reviewed unless it was in the enforced coverage ledger."""
        val final = trackedText(verificationModel, finalPrompt, FINAL_OUTPUT_TOKENS, "chairman")
        run = run.copy(
            stage = RepoAuditStage.COMPLETE,
            finalReport = final,
            chairmanModel = verificationModel,
            finishedAt = System.currentTimeMillis()
        )
        onUpdate(run)
        return run
    }

    private suspend fun auditOneModel(
        model: String,
        snapshot: RepoSnapshot,
        units: List<AuditUnit>,
        onPartial: suspend (ModelRepoAudit) -> Unit
    ): ModelRepoAudit {
        val coverage = snapshot.requiredFiles.associate { it.path to false }.toMutableMap()
        val perPathParts = units.groupBy { it.path }.mapValues { it.value.size }
        val completedParts = mutableMapOf<String, Int>()
        val batchReports = mutableListOf<String>()
        val batches = pack(units)
        try {
            for ((batchIndex, batch) in batches.withIndex()) {
                coroutineContext.ensureActive()
                val prompt = batchPrompt(snapshot, batch, batchIndex, batches.size)
                val report = trackedText(model, prompt, BATCH_OUTPUT_TOKENS, "repo-batch")
                if (!isUsableReport(report)) throw IllegalStateException("Model returned an unusable/empty repository batch report")
                batchReports += report
                batch.forEach { unit ->
                    val done = (completedParts[unit.path] ?: 0) + 1
                    completedParts[unit.path] = done
                    if (done >= (perPathParts[unit.path] ?: 1)) coverage[unit.path] = true
                }
                val ledger = coverage.map { (path, ok) -> FileCoverage(path, model, ok, batchIndex) }
                onPartial(ModelRepoAudit(model, "", ledger, batchReports.toList(), complete = coverage.values.all { it }))
            }
            if (!coverage.values.all { it }) {
                val missing = coverage.filterValues { !it }.keys.take(10)
                throw IllegalStateException("Coverage incomplete; missing ${missing.joinToString()}")
            }
            val synthesis = hierarchicalSynthesis(model, snapshot, batchReports)
            if (!isUsableReport(synthesis)) throw IllegalStateException("Model completed file coverage but returned an unusable final audit")
            return ModelRepoAudit(
                model = model,
                report = synthesis,
                coverage = coverage.map { (path, ok) -> FileCoverage(path, model, ok, batches.lastIndex.coerceAtLeast(0)) },
                batchReports = batchReports,
                complete = true
            )
        } catch (e: CancellationException) { throw e }
        catch (e: Exception) {
            return ModelRepoAudit(
                model = model,
                report = "",
                coverage = coverage.map { (path, ok) -> FileCoverage(path, model, ok, -1, if (ok) null else e.message) },
                batchReports = batchReports,
                complete = false,
                error = e.message ?: e.toString()
            )
        }
    }

    private fun buildUnits(snapshot: RepoSnapshot): List<AuditUnit> = buildList {
        snapshot.requiredFiles.forEach { file ->
            val redacted = redactSecrets(file.content)
            val parts = if (redacted.isEmpty()) listOf("") else redacted.chunked(FILE_PART_CHARS)
            parts.forEachIndexed { index, text -> add(AuditUnit(file.path, index + 1, parts.size, file.category, text)) }
        }
    }

    private fun pack(units: List<AuditUnit>): List<List<AuditUnit>> {
        val out = mutableListOf<MutableList<AuditUnit>>()
        var current = mutableListOf<AuditUnit>()
        var chars = 0
        for (u in units) {
            val size = u.text.length + u.path.length + 200
            if (current.isNotEmpty() && chars + size > BATCH_CHAR_BUDGET) {
                out += current; current = mutableListOf(); chars = 0
            }
            current += u; chars += size
        }
        if (current.isNotEmpty()) out += current
        return out
    }

    private fun batchPrompt(snapshot: RepoSnapshot, batch: List<AuditUnit>, index: Int, total: Int): String = buildString {
        append("You are performing an EXHAUSTIVE engineering audit of repository ${snapshot.repo.fullName} at commit ${snapshot.commitSha}.\n")
        append("This is batch ${index + 1}/$total. Analyse every supplied file part; do not skip any. This batch is evidence, not a summary.\n")
        append("Review architecture, correctness, concurrency/state, security, tests, dependencies, performance, CI/deployment, documentation-code drift and maintainability where relevant.\n")
        append("Every finding must cite the exact file path and preferably symbol/line-context. Distinguish fact from hypothesis. Do not invent unseen code.\n")
        append("Return a concise but substantive batch audit with: Files inspected, Findings, Cross-file implications, No-finding files.\n\n")
        batch.forEach { u ->
            append("===== FILE ${u.path} [${u.category}] PART ${u.part}/${u.parts} =====\n")
            append(u.text).append("\n===== END FILE PART =====\n\n")
        }
    }

    private suspend fun hierarchicalSynthesis(model: String, snapshot: RepoSnapshot, reports: List<String>): String {
        var layer = reports.toList()
        while (layer.size > 1) {
            val next = mutableListOf<String>()
            layer.chunked(4).forEach { group ->
                val prompt = """Merge these repository batch-audit reports without dropping distinct evidence. Deduplicate repeated findings, preserve exact file paths, preserve disagreements and uncertainty, and keep coverage-relevant observations. Do not invent new findings.
Repository: ${snapshot.repo.fullName} @ ${snapshot.commitSha}

${group.joinToString("\n\n--- BATCH REPORT ---\n\n") { it.take(12_000) }}"""
                next += trackedText(model, prompt, SYNTHESIS_OUTPUT_TOKENS, "repo-merge")
            }
            layer = next
        }
        val seed = layer.firstOrNull().orEmpty()
        return trackedText(model, """Produce your independent FINAL exhaustive repository audit from the consolidated evidence below.
Repository: ${snapshot.repo.fullName}
Commit: ${snapshot.commitSha}
Required files: ${snapshot.requiredFiles.size}; excluded files: ${snapshot.excluded.size}.
The application has already enforced 100% processing of required files. Do not claim anything about excluded content.
Organise by severity/category, cite exact paths, include architecture and documentation-code drift, identify uncertainty, and finish with prioritised remediation.

CONSOLIDATED EVIDENCE:\n$seed""", SYNTHESIS_OUTPUT_TOKENS, "repo-final")
    }

    private suspend fun trackedText(model: String, prompt: String, maxTokens: Int, purpose: String): String {
        return try {
            val text = ai.chat(model, prompt, maxTokens)
            val ok = isUsableReport(text)
            withContext(Dispatchers.IO) { healthDb.record(model, ok, if (ok) null else "Unusable $purpose response") }
            if (!ok) throw IllegalStateException("Model returned an unusable $purpose response")
            text
        } catch (e: Exception) {
            withContext(Dispatchers.IO) { healthDb.record(model, false, "$purpose: ${e.message ?: e}") }
            throw e
        }
    }

    private suspend fun trackedReview(model: String, prompt: String, maxTokens: Int, purpose: String): RankingReview {
        val started = System.currentTimeMillis()
        return try {
            val text = trackedText(model, prompt, maxTokens, purpose)
            RankingReview(model, text, parseRanking(text), System.currentTimeMillis() - started)
        } catch (e: Exception) {
            RankingReview(model, "", emptyList(), System.currentTimeMillis() - started, e.message ?: e.toString())
        }
    }

    private fun chooseChairman(survivors: List<String>): String = settings.chairman().takeIf { it in survivors } ?: survivors.first()

    private fun parseRanking(text: String): List<String> {
        val source = text.substringAfter("FINAL RANKING:", text)
        return Regex("Audit [A-Z]").findAll(source).map { it.value }.toList().distinct()
    }

    private fun aggregate(reviews: List<RankingReview>, labels: Map<String, String>): List<AggregateRank> {
        val positions = linkedMapOf<String, MutableList<Int>>()
        reviews.filter { it.error == null }.forEach { r ->
            r.parsedRanking.forEachIndexed { i, label -> labels[label]?.let { model -> positions.getOrPut(model) { mutableListOf() }.add(i + 1) } }
        }
        return positions.map { (model, values) ->
            AggregateRank(model, round(values.average() * 100.0) / 100.0, values.size)
        }.sortedBy { it.averageRank }
    }

    private fun isUsableReport(text: String): Boolean {
        val clean = text.trim()
        if (clean.length < 80) return false
        val lower = clean.lowercase()
        if (lower in setOf("null", "nil", "none", "n/a", "ok")) return false
        if (lower.contains("no content") && clean.length < 200) return false
        val alpha = clean.count { it.isLetter() }
        return alpha >= 40 && alpha.toDouble() / clean.length.coerceAtLeast(1) > 0.18
    }

    private fun redactSecrets(text: String): String {
        var out = text
        val patterns = listOf(
            Regex("(?i)(api[_-]?key|secret|token|password)\\s*[:=]\\s*['\"]?[^'\"\\s]{8,}") to "$1=<REDACTED>",
            Regex("sk-[A-Za-z0-9_-]{16,}") to "<REDACTED_OPENAI_LIKE_KEY>",
            Regex("gh[pousr]_[A-Za-z0-9_]{20,}") to "<REDACTED_GITHUB_TOKEN>",
            Regex("AIza[0-9A-Za-z_-]{20,}") to "<REDACTED_GOOGLE_KEY>"
        )
        patterns.forEach { (regex, replacement) -> out = regex.replace(out, replacement) }
        return out
    }
}
