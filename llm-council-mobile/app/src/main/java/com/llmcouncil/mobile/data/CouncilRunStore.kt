package com.llmcouncil.mobile.data

import android.content.Context
import com.llmcouncil.mobile.model.*
import org.json.JSONArray
import org.json.JSONObject

class CouncilRunStore(context: Context) {
    private val prefs = context.getSharedPreferences("llm_council_run_checkpoint", Context.MODE_PRIVATE)

    fun save(run: CouncilRun) {
        prefs.edit().putString("run", encode(run).toString()).apply()
    }

    fun load(): CouncilRun? {
        val raw = prefs.getString("run", null) ?: return null
        return try { decode(JSONObject(raw)) } catch (_: Exception) { null }
    }

    fun clear() { prefs.edit().remove("run").apply() }

    private fun encode(run: CouncilRun): JSONObject = JSONObject()
        .put("question", run.question)
        .put("stage", run.stage.name)
        .put("startedAt", run.startedAt)
        .put("finishedAt", run.finishedAt ?: JSONObject.NULL)
        .put("stage1", JSONArray().apply { run.stage1.forEach { put(answerJson(it)) } })
        .put("stage2", JSONArray().apply { run.stage2.forEach { put(reviewJson(it)) } })
        .put("aggregate", JSONArray().apply { run.aggregate.forEach { put(rankJson(it)) } })
        .put("chairman", run.chairman?.let(::answerJson) ?: JSONObject.NULL)
        .put("errors", JSONObject().apply { run.errors.forEach { (k, v) -> put(k, v) } })

    private fun answerJson(a: ModelAnswer) = JSONObject()
        .put("model", a.model).put("text", a.text).put("latencyMs", a.latencyMs)
        .put("error", a.error ?: JSONObject.NULL)

    private fun reviewJson(r: RankingReview) = JSONObject()
        .put("model", r.model).put("text", r.text).put("latencyMs", r.latencyMs)
        .put("error", r.error ?: JSONObject.NULL)
        .put("ranking", JSONArray(r.parsedRanking))

    private fun rankJson(r: AggregateRank) = JSONObject()
        .put("model", r.model).put("averageRank", r.averageRank).put("votes", r.votes)

    private fun decode(o: JSONObject): CouncilRun {
        val stage1 = o.optJSONArray("stage1").toAnswers()
        val stage2 = o.optJSONArray("stage2").toReviews()
        val aggregate = o.optJSONArray("aggregate").toRanks()
        val chairmanObj = o.opt("chairman") as? JSONObject
        val errorsObj = o.optJSONObject("errors") ?: JSONObject()
        val errors = buildMap {
            val keys = errorsObj.keys()
            while (keys.hasNext()) { val k = keys.next(); put(k, errorsObj.optString(k)) }
        }
        return CouncilRun(
            question = o.optString("question"),
            stage = runCatching { CouncilStage.valueOf(o.optString("stage")) }.getOrDefault(CouncilStage.IDLE),
            stage1 = stage1,
            stage2 = stage2,
            aggregate = aggregate,
            chairman = chairmanObj?.let(::decodeAnswer),
            errors = errors,
            startedAt = o.optLong("startedAt", System.currentTimeMillis()),
            finishedAt = if (o.isNull("finishedAt")) null else o.optLong("finishedAt")
        )
    }

    private fun JSONArray?.toAnswers(): List<ModelAnswer> = if (this == null) emptyList() else buildList {
        for (i in 0 until length()) optJSONObject(i)?.let { add(decodeAnswer(it)) }
    }

    private fun decodeAnswer(o: JSONObject) = ModelAnswer(
        model = o.optString("model"), text = o.optString("text"), latencyMs = o.optLong("latencyMs"),
        error = if (o.isNull("error")) null else o.optString("error")
    )

    private fun JSONArray?.toReviews(): List<RankingReview> = if (this == null) emptyList() else buildList {
        for (i in 0 until length()) optJSONObject(i)?.let { o ->
            val ranking = o.optJSONArray("ranking")
            add(RankingReview(o.optString("model"), o.optString("text"), buildList {
                if (ranking != null) for (j in 0 until ranking.length()) add(ranking.optString(j))
            }, o.optLong("latencyMs"), if (o.isNull("error")) null else o.optString("error")))
        }
    }

    private fun JSONArray?.toRanks(): List<AggregateRank> = if (this == null) emptyList() else buildList {
        for (i in 0 until length()) optJSONObject(i)?.let { add(AggregateRank(it.optString("model"), it.optDouble("averageRank"), it.optInt("votes"))) }
    }
}
