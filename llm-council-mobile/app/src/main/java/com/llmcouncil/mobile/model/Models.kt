package com.llmcouncil.mobile.model

data class OpenRouterModel(
    val id: String,
    val name: String,
    val contextLength: Int = 0,
    val promptPricePerToken: Double? = null,
    val completionPricePerToken: Double? = null,
    val inputModalities: Set<String> = emptySet(),
    val outputModalities: Set<String> = emptySet(),
    val provider: String = id.substringBefore('/'),
    val description: String = ""
) {
    val pricingKnown: Boolean get() = promptPricePerToken != null && completionPricePerToken != null
    val promptPricePerMillion: Double get() = (promptPricePerToken ?: 0.0) * 1_000_000.0
    val completionPricePerMillion: Double get() = (completionPricePerToken ?: 0.0) * 1_000_000.0
    val isFree: Boolean get() = pricingKnown && promptPricePerToken == 0.0 && completionPricePerToken == 0.0
    val acceptsText: Boolean get() = inputModalities.isEmpty() || "text" in inputModalities
    val returnsText: Boolean get() = outputModalities.isEmpty() || "text" in outputModalities
}

data class CouncilProfile(
    val name: String,
    val councilModels: List<String>,
    val chairmanModel: String
)

data class ModelAnswer(
    val model: String,
    val text: String,
    val latencyMs: Long,
    val error: String? = null
)

data class RankingReview(
    val model: String,
    val text: String,
    val parsedRanking: List<String>,
    val latencyMs: Long,
    val error: String? = null
)

data class AggregateRank(
    val model: String,
    val averageRank: Double,
    val votes: Int
)

enum class CouncilStage { IDLE, STAGE1, STAGE2, STAGE3, COMPLETE, ERROR, CANCELLED }

data class CouncilRun(
    val question: String,
    val stage: CouncilStage = CouncilStage.IDLE,
    val stage1: List<ModelAnswer> = emptyList(),
    val stage2: List<RankingReview> = emptyList(),
    val aggregate: List<AggregateRank> = emptyList(),
    val chairman: ModelAnswer? = null,
    val errors: Map<String, String> = emptyMap(),
    val startedAt: Long = System.currentTimeMillis(),
    val finishedAt: Long? = null
)

data class HistoryItem(
    val id: Long,
    val title: String,
    val question: String,
    val finalAnswer: String,
    val chairman: String,
    val councilModels: List<String>,
    val createdAt: Long
)
