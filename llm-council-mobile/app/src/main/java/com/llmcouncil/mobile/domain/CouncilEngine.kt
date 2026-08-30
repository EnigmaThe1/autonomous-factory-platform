package com.llmcouncil.mobile.domain

import com.llmcouncil.mobile.data.OpenRouterClient
import com.llmcouncil.mobile.data.SecureSettings
import com.llmcouncil.mobile.model.*
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlin.math.round

class CouncilEngine(
    private val client: OpenRouterClient,
    private val settings: SecureSettings
) {
    companion object {
        private const val STAGE1_MAX_TOKENS = 2048
        private const val STAGE2_MAX_TOKENS = 1536
        private const val STAGE3_MAX_TOKENS = 3072
    }

    suspend fun run(question: String, onUpdate: suspend (CouncilRun) -> Unit): CouncilRun = coroutineScope {
        val configured = settings.councilModels()
        var run = CouncilRun(question = question, stage = CouncilStage.STAGE1)
        onUpdate(run)

        val catalogueIds = try { client.models().map { it.id }.toSet() } catch (_: Exception) { emptySet() }
        val unavailable = if (catalogueIds.isEmpty()) emptyList() else configured.filter { it !in catalogueIds }
        val selected = if (catalogueIds.isEmpty()) configured else configured.filter { it in catalogueIds }
        val preflightErrors = unavailable.associateWith { "Model is no longer present in the current OpenRouter catalogue. Choose a replacement in Models." }

        if (selected.size < 2) {
            run = run.copy(
                stage = CouncilStage.ERROR,
                errors = preflightErrors + ("Council" to "Stage 1 cannot start: fewer than two currently available council models are selected."),
                finishedAt = System.currentTimeMillis()
            )
            onUpdate(run)
            return@coroutineScope run
        }

        val semaphore = Semaphore(settings.maxConcurrency())
        val stage1 = selected.map { model ->
            async {
                semaphore.withPermit {
                    val started = System.currentTimeMillis()
                    try { ModelAnswer(model, client.chat(model, question, STAGE1_MAX_TOKENS), System.currentTimeMillis() - started) }
                    catch (e: Exception) { ModelAnswer(model, "", System.currentTimeMillis() - started, e.message ?: e.toString()) }
                }
            }
        }.awaitAll()
        val successful1 = stage1.filter { it.error == null && it.text.isNotBlank() }
        val stage1Errors = stage1.mapNotNull { it.error?.let { e -> it.model to e } }.toMap()
        run = run.copy(stage1 = stage1, errors = preflightErrors + stage1Errors)
        onUpdate(run)

        if (successful1.size < 2) {
            run = run.copy(
                stage = CouncilStage.ERROR,
                errors = run.errors + ("Council" to "Stopped after Stage 1: ${successful1.size}/${selected.size} available models produced usable answers. At least two are required for peer review."),
                finishedAt = System.currentTimeMillis()
            )
            onUpdate(run)
            return@coroutineScope run
        }

        run = run.copy(stage = CouncilStage.STAGE2); onUpdate(run)
        val labelToModel = LinkedHashMap<String, String>()
        val responsesText = buildString {
            successful1.forEachIndexed { index, answer ->
                val label = "Response ${('A'.code + index).toChar()}"
                labelToModel[label] = answer.model
                if (isNotEmpty()) append("\n\n")
                append(label).append(":\n").append(answer.text)
            }
        }
        val rankingPrompt = """You are evaluating different responses to the following question:

Question: $question

Here are the responses from different models (anonymized):

$responsesText

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example:
FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

        val stage2 = successful1.map { answer -> answer.model }.map { model ->
            async {
                semaphore.withPermit {
                    val started = System.currentTimeMillis()
                    try {
                        val text = client.chat(model, rankingPrompt, STAGE2_MAX_TOKENS)
                        RankingReview(model, text, parseRanking(text), System.currentTimeMillis() - started)
                    } catch (e: Exception) {
                        RankingReview(model, "", emptyList(), System.currentTimeMillis() - started, e.message ?: e.toString())
                    }
                }
            }
        }.awaitAll()
        val aggregate = aggregate(stage2, labelToModel)
        val errors = run.errors + stage2.mapNotNull { it.error?.let { e -> "${it.model} (review)" to e } }.toMap()
        run = run.copy(stage2 = stage2, aggregate = aggregate, errors = errors)
        onUpdate(run)

        run = run.copy(stage = CouncilStage.STAGE3); onUpdate(run)
        val stage1Text = successful1.joinToString("\n\n") { "Model: ${it.model}\nResponse: ${it.text}" }
        val successful2 = stage2.filter { it.error == null && it.text.isNotBlank() }
        val stage2Text = successful2.joinToString("\n\n") { "Model: ${it.model}\nRanking: ${it.text}" }
        val chairmanPrompt = """You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: $question

STAGE 1 - Individual Responses:
$stage1Text

STAGE 2 - Peer Rankings:
$stage2Text

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""

        val configuredChairman = settings.chairman()
        val survivingModels = successful1.map { it.model }.toSet()
        val chairmanModel = when {
            configuredChairman in survivingModels -> configuredChairman
            else -> successful1.first().model
        }
        val started = System.currentTimeMillis()
        val chairman = try { ModelAnswer(chairmanModel, client.chat(chairmanModel, chairmanPrompt, STAGE3_MAX_TOKENS), System.currentTimeMillis() - started) }
        catch (e: Exception) { ModelAnswer(chairmanModel, "", System.currentTimeMillis() - started, e.message ?: e.toString()) }
        run = if (chairman.error == null) run.copy(stage = CouncilStage.COMPLETE, chairman = chairman, finishedAt = System.currentTimeMillis())
        else run.copy(stage = CouncilStage.ERROR, chairman = chairman, errors = run.errors + ("$chairmanModel (chairman)" to chairman.error), finishedAt = System.currentTimeMillis())
        onUpdate(run)
        run
    }

    private fun parseRanking(text: String): List<String> {
        val source = text.substringAfter("FINAL RANKING:", text)
        return Regex("Response [A-Z]").findAll(source).map { it.value }.toList().distinct()
    }

    private fun aggregate(reviews: List<RankingReview>, labels: Map<String, String>): List<AggregateRank> {
        val positions = linkedMapOf<String, MutableList<Int>>()
        reviews.filter { it.error == null }.forEach { review ->
            review.parsedRanking.forEachIndexed { index, label ->
                labels[label]?.let { model -> positions.getOrPut(model) { mutableListOf() }.add(index + 1) }
            }
        }
        return positions.map { (model, values) ->
            val avg = if (values.isEmpty()) 999.0 else values.average()
            AggregateRank(model, round(avg * 100.0) / 100.0, values.size)
        }.sortedBy { it.averageRank }
    }
}
