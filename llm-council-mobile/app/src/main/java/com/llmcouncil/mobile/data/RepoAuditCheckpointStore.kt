package com.llmcouncil.mobile.data

import android.content.Context
import com.llmcouncil.mobile.model.*
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.zip.GZIPInputStream
import java.util.zip.GZIPOutputStream

class RepoAuditCheckpointStore(context: Context) {
    private val file = File(context.filesDir, "repo_audit_checkpoint_v5.json.gz")

    @Synchronized fun save(run: RepoAuditRun) {
        val bytes = encode(run).toString().toByteArray(Charsets.UTF_8)
        GZIPOutputStream(file.outputStream()).use { it.write(bytes) }
    }

    @Synchronized fun load(): RepoAuditRun? {
        if (!file.exists()) return null
        return runCatching {
            val text = GZIPInputStream(file.inputStream()).bufferedReader().use { it.readText() }
            decode(JSONObject(text))
        }.getOrNull()
    }

    @Synchronized fun clear() { if (file.exists()) file.delete() }

    private fun encode(run: RepoAuditRun) = JSONObject()
        .put("repo", run.repoFullName).put("ref", run.ref).put("commit", run.commitSha)
        .put("stage", run.stage.name).put("required", run.requiredFiles).put("excluded", run.excludedFiles)
        .put("chairman", run.chairmanModel).put("final", run.finalReport)
        .put("started", run.startedAt).put("finished", run.finishedAt ?: JSONObject.NULL)
        .put("errors", JSONObject(run.errors))
        .put("audits", JSONArray().apply { run.modelAudits.forEach { put(encodeAudit(it)) } })
        .put("peer", JSONArray().apply { run.peerReviews.forEach { put(encodeReview(it)) } })
        .put("aggregate", JSONArray().apply { run.aggregate.forEach { put(JSONObject().put("model", it.model).put("avg", it.averageRank).put("votes", it.votes)) } })

    private fun encodeAudit(a: ModelRepoAudit) = JSONObject()
        .put("model", a.model).put("report", a.report).put("complete", a.complete).put("error", a.error ?: JSONObject.NULL)
        .put("batches", JSONArray(a.batchReports))
        .put("coverage", JSONArray().apply { a.coverage.forEach { c -> put(JSONObject().put("path", c.path).put("model", c.model).put("covered", c.covered).put("batch", c.batchIndex).put("error", c.error ?: JSONObject.NULL)) } })

    private fun encodeReview(r: RankingReview) = JSONObject()
        .put("model", r.model).put("text", r.text).put("ranking", JSONArray(r.parsedRanking))
        .put("latency", r.latencyMs).put("error", r.error ?: JSONObject.NULL)

    private fun decode(o: JSONObject): RepoAuditRun {
        val audits = mutableListOf<ModelRepoAudit>()
        val aa = o.optJSONArray("audits") ?: JSONArray()
        for (i in 0 until aa.length()) audits += decodeAudit(aa.getJSONObject(i))
        val peer = mutableListOf<RankingReview>()
        val pa = o.optJSONArray("peer") ?: JSONArray()
        for (i in 0 until pa.length()) peer += decodeReview(pa.getJSONObject(i))
        val agg = mutableListOf<AggregateRank>()
        val ag = o.optJSONArray("aggregate") ?: JSONArray()
        for (i in 0 until ag.length()) ag.getJSONObject(i).let { agg += AggregateRank(it.getString("model"), it.getDouble("avg"), it.getInt("votes")) }
        val errorsObj = o.optJSONObject("errors") ?: JSONObject()
        val errors = buildMap<String, String> { errorsObj.keys().forEach { k -> put(k, errorsObj.optString(k)) } }
        return RepoAuditRun(
            repoFullName = o.optString("repo"), ref = o.optString("ref"), commitSha = o.optString("commit"),
            stage = runCatching { RepoAuditStage.valueOf(o.optString("stage")) }.getOrDefault(RepoAuditStage.IDLE),
            requiredFiles = o.optInt("required"), excludedFiles = o.optInt("excluded"), modelAudits = audits,
            peerReviews = peer, aggregate = agg, finalReport = o.optString("final"), chairmanModel = o.optString("chairman"),
            errors = errors, startedAt = o.optLong("started", System.currentTimeMillis()),
            finishedAt = if (o.isNull("finished")) null else o.optLong("finished")
        )
    }

    private fun decodeAudit(o: JSONObject): ModelRepoAudit {
        val batches = mutableListOf<String>()
        val ba = o.optJSONArray("batches") ?: JSONArray(); for (i in 0 until ba.length()) batches += ba.optString(i)
        val coverage = mutableListOf<FileCoverage>()
        val ca = o.optJSONArray("coverage") ?: JSONArray()
        for (i in 0 until ca.length()) ca.getJSONObject(i).let { c -> coverage += FileCoverage(c.optString("path"), c.optString("model"), c.optBoolean("covered"), c.optInt("batch"), if (c.isNull("error")) null else c.optString("error")) }
        return ModelRepoAudit(o.optString("model"), o.optString("report"), coverage, batches, o.optBoolean("complete"), if (o.isNull("error")) null else o.optString("error"))
    }

    private fun decodeReview(o: JSONObject): RankingReview {
        val ranking = mutableListOf<String>(); val a = o.optJSONArray("ranking") ?: JSONArray(); for (i in 0 until a.length()) ranking += a.optString(i)
        return RankingReview(o.optString("model"), o.optString("text"), ranking, o.optLong("latency"), if (o.isNull("error")) null else o.optString("error"))
    }
}
