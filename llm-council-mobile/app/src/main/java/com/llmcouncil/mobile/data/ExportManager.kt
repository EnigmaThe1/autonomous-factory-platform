package com.llmcouncil.mobile.data

import android.content.Context
import android.net.Uri
import androidx.documentfile.provider.DocumentFile
import com.llmcouncil.mobile.model.CouncilRun
import com.llmcouncil.mobile.model.RepoAuditRun
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object ExportManager {
    fun exportRepoAudit(context: Context, treeUri: Uri, run: RepoAuditRun): String {
        val root = DocumentFile.fromTreeUri(context, treeUri) ?: error("Selected folder is no longer accessible")
        val councilRoot = dir(root, "LLM-Council")
        val project = dir(councilRoot, safe(run.repoFullName.replace('/', '_')))
        val stamp = SimpleDateFormat("yyyy-MM-dd_HHmmss", Locale.UK).format(Date(run.startedAt))
        val workspaceName = "${stamp}_Repository-Audit_${run.commitSha.take(8).ifBlank { "unknown" }}"
        val workspace = dir(project, workspaceName)
        val metadata = dir(workspace, "00_Audit-Metadata")
        val individual = dir(workspace, "01_Individual-Reviews")
        val peer = dir(workspace, "02_Peer-Reviews")
        val rankings = dir(workspace, "03_Rankings")
        val final = dir(workspace, "04_Final-Report")
        val evidence = dir(workspace, "05_Evidence")

        val summary = JSONObject()
            .put("application", "LLM Council Mobile")
            .put("audit_type", "Exhaustive Repository Audit")
            .put("repository", run.repoFullName)
            .put("ref", run.ref)
            .put("commit_sha", run.commitSha)
            .put("stage", run.stage.name)
            .put("required_files", run.requiredFiles)
            .put("excluded_files", run.excludedFiles)
            .put("chairman_model", run.chairmanModel)
            .put("started_at_epoch_ms", run.startedAt)
            .put("finished_at_epoch_ms", run.finishedAt ?: JSONObject.NULL)
            .put("models", JSONArray(run.modelAudits.map { it.model }))
            .put("errors", JSONObject(run.errors))
        write(context, metadata, "audit-summary.json", "application/json", summary.toString(2))

        run.modelAudits.forEachIndexed { index, audit ->
            val name = "%02d_%s.md".format(index + 1, safe(audit.model))
            val body = buildString {
                append("# Independent Repository Audit\n\n")
                append("- Model: `${audit.model}`\n")
                append("- Coverage: ${audit.coveredCount}/${audit.requiredCount}\n")
                append("- Complete: ${audit.complete}\n")
                audit.error?.let { append("- Error: $it\n") }
                append("\n## Report\n\n").append(audit.report.ifBlank { "No final report produced." })
            }
            write(context, individual, name, "text/markdown", body)
            val batchBody = buildString {
                append("# Batch Evidence — ${audit.model}\n\n")
                audit.batchReports.forEachIndexed { bi, report -> append("## Batch ${bi + 1}\n\n$report\n\n") }
            }
            write(context, evidence, "%02d_%s_batch-evidence.md".format(index + 1, safe(audit.model)), "text/markdown", batchBody)
        }

        run.peerReviews.forEachIndexed { index, review ->
            val body = "# Peer Review\n\n- Model: `${review.model}`\n- Error: ${review.error ?: "None"}\n\n${review.text}"
            write(context, peer, "%02d_%s_peer-review.md".format(index + 1, safe(review.model)), "text/markdown", body)
        }

        val rankingCsv = buildString {
            append("rank,model,average_rank,votes\n")
            run.aggregate.forEachIndexed { i, r -> append("${i + 1},\"${r.model.replace("\"", "\"\"")}\",${r.averageRank},${r.votes}\n") }
        }
        write(context, rankings, "aggregate-ranking.csv", "text/csv", rankingCsv)
        write(context, rankings, "aggregate-ranking.md", "text/markdown", buildString {
            append("# Aggregate Ranking\n\n")
            run.aggregate.forEachIndexed { i, r -> append("${i + 1}. `${r.model}` — avg ${r.averageRank}, ${r.votes} votes\n") }
        })

        val coverageCsv = buildString {
            append("model,path,covered,batch,error\n")
            run.modelAudits.flatMap { it.coverage }.forEach { c ->
                fun q(s: String) = "\"${s.replace("\"", "\"\"")}\""
                append("${q(c.model)},${q(c.path)},${c.covered},${c.batchIndex},${q(c.error ?: "")}\n")
            }
        }
        write(context, evidence, "file-coverage.csv", "text/csv", coverageCsv)

        val finalBody = buildString {
            append("# Final Council Repository Audit\n\n")
            append("Repository: `${run.repoFullName}`  \nRef: `${run.ref}`  \nCommit: `${run.commitSha}`  \n")
            append("Required files: ${run.requiredFiles}  \nExcluded files: ${run.excludedFiles}  \nChairman: `${run.chairmanModel}`\n\n")
            append(run.finalReport.ifBlank { "No final report produced." })
        }
        write(context, final, "Final-Council-Review.md", "text/markdown", finalBody)
        write(context, final, "Final-Council-Review.txt", "text/plain", run.finalReport)
        return "LLM-Council/${project.name}/$workspaceName"
    }

    fun exportCouncilRun(context: Context, treeUri: Uri, run: CouncilRun, projectName: String = "Council-Runs"): String {
        val root = DocumentFile.fromTreeUri(context, treeUri) ?: error("Selected folder is no longer accessible")
        val councilRoot = dir(root, "LLM-Council")
        val project = dir(councilRoot, safe(projectName))
        val stamp = SimpleDateFormat("yyyy-MM-dd_HHmmss", Locale.UK).format(Date(run.startedAt))
        val workspace = dir(project, "${stamp}_Council-Run")
        val individual = dir(workspace, "01_Individual-Reviews")
        val peer = dir(workspace, "02_Peer-Reviews")
        val final = dir(workspace, "04_Final-Report")
        run.stage1.forEachIndexed { i, a -> write(context, individual, "%02d_%s.md".format(i + 1, safe(a.model)), "text/markdown", "# ${a.model}\n\n${a.error ?: a.text}") }
        run.stage2.forEachIndexed { i, r -> write(context, peer, "%02d_%s.md".format(i + 1, safe(r.model)), "text/markdown", "# ${r.model}\n\n${r.error ?: r.text}") }
        run.chairman?.let { write(context, final, "Final-Council-Answer.md", "text/markdown", "# Final Council Answer\n\nChairman: `${it.model}`\n\n${it.error ?: it.text}") }
        return "LLM-Council/${project.name}/${workspace.name}"
    }

    private fun dir(parent: DocumentFile, name: String): DocumentFile =
        parent.findFile(name)?.takeIf { it.isDirectory } ?: parent.createDirectory(name) ?: error("Unable to create folder $name")

    private fun write(context: Context, parent: DocumentFile, name: String, mime: String, content: String) {
        parent.findFile(name)?.delete()
        val file = parent.createFile(mime, name) ?: error("Unable to create $name")
        context.contentResolver.openOutputStream(file.uri, "wt")?.bufferedWriter(Charsets.UTF_8)?.use { it.write(content) }
            ?: error("Unable to write $name")
    }

    private fun safe(value: String): String = value.replace(Regex("[^A-Za-z0-9._-]+"), "_").trim('_').take(100).ifBlank { "item" }
}
