package com.llmcouncil.mobile

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.llmcouncil.mobile.data.HistoryDb
import com.llmcouncil.mobile.data.OpenRouterClient
import com.llmcouncil.mobile.data.SecureSettings
import com.llmcouncil.mobile.domain.CouncilEngine
import com.llmcouncil.mobile.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.ln

class AppViewModel(app: Application) : AndroidViewModel(app) {
    private val settings = SecureSettings(app)
    private val client = OpenRouterClient(settings)
    private val engine = CouncilEngine(client, settings)
    private val historyDb = HistoryDb(app)

    private val _run = MutableStateFlow(CouncilRun(""))
    val run: StateFlow<CouncilRun> = _run.asStateFlow()
    private val _models = MutableStateFlow<List<OpenRouterModel>>(emptyList())
    val models: StateFlow<List<OpenRouterModel>> = _models.asStateFlow()
    private val _modelsLoading = MutableStateFlow(false)
    val modelsLoading: StateFlow<Boolean> = _modelsLoading.asStateFlow()
    private val _modelsError = MutableStateFlow<String?>(null)
    val modelsError: StateFlow<String?> = _modelsError.asStateFlow()
    private val _history = MutableStateFlow<List<HistoryItem>>(emptyList())
    val history: StateFlow<List<HistoryItem>> = _history.asStateFlow()
    private var activeRun: Job? = null

    fun hasApiKey(): Boolean = settings.getApiKey().isNotBlank()
    fun saveApiKey(key: String) { settings.setApiKey(key.trim()) }
    fun selectedModels(): Set<String> = settings.councilModels().toSet()
    fun chairman(): String = settings.chairman()
    fun concurrency(): Int = settings.maxConcurrency()
    fun setConcurrency(v: Int) = settings.setMaxConcurrency(v)

    fun loadModels(force: Boolean = false) {
        if (_modelsLoading.value || (!force && _models.value.isNotEmpty())) return
        viewModelScope.launch {
            _modelsLoading.value = true
            _modelsError.value = null
            try { _models.value = client.models() }
            catch (e: Exception) { _modelsError.value = e.message ?: e.toString() }
            finally { _modelsLoading.value = false }
        }
    }

    fun toggleCouncilModel(id: String) {
        val set = settings.councilModels().toMutableSet()
        if (!set.add(id)) {
            if (set.size <= 2) return
            set.remove(id)
        }
        settings.setCouncilModels(set)
    }

    fun setChairman(id: String) = settings.setChairman(id)

    private fun totalPricePerMillion(model: OpenRouterModel): Double =
        model.promptPricePerMillion + model.completionPricePerMillion

    private fun isFree(model: OpenRouterModel): Boolean =
        model.promptPricePerToken <= 0.0 && model.completionPricePerToken <= 0.0

    /**
     * Pick a small council while preferring provider diversity. The first pass takes
     * the best-scoring model from each provider; the second pass fills any remaining
     * slots from the overall ranking.
     */
    private fun diverseTop(
        source: List<OpenRouterModel>,
        limit: Int = 4,
        score: (OpenRouterModel) -> Double
    ): List<OpenRouterModel> {
        val ranked = source.sortedByDescending(score)
        val out = mutableListOf<OpenRouterModel>()
        val providers = mutableSetOf<String>()
        for (model in ranked) {
            if (providers.add(model.provider)) out += model
            if (out.size == limit) return out
        }
        for (model in ranked) {
            if (model !in out) out += model
            if (out.size == limit) break
        }
        return out
    }

    /**
     * Dynamic presets use the live OpenRouter catalogue rather than hard-coded IDs.
     * This intentionally means a preset can change as OpenRouter adds/removes models
     * or changes pricing.
     */
    fun applyPreset(name: String) {
        val catalogue = _models.value
        if (catalogue.isEmpty()) return

        val chosen: List<OpenRouterModel> = when (name) {
            "Free" -> {
                val free = catalogue.filter(::isFree)
                diverseTop(free, 4) { model ->
                    // For genuinely free models, prefer larger context and provider diversity.
                    ln(1.0 + model.contextLength.coerceAtLeast(1).toDouble())
                }
            }
            "Low cost" -> {
                // Cheapest live models first; for equal pricing prefer larger context.
                val ranked = catalogue.sortedWith(
                    compareBy<OpenRouterModel> { totalPricePerMillion(it) }
                        .thenByDescending { it.contextLength }
                )
                val firstPerProvider = ranked.distinctBy { it.provider }.take(4).toMutableList()
                if (firstPerProvider.size < 4) {
                    ranked.filter { it !in firstPerProvider }
                        .take(4 - firstPerProvider.size)
                        .forEach(firstPerProvider::add)
                }
                firstPerProvider
            }
            "Balanced" -> {
                // Reward context/capability headroom but penalise very expensive models.
                diverseTop(catalogue, 4) { model ->
                    val contextScore = ln(1.0 + model.contextLength.coerceAtLeast(1).toDouble())
                    val costPenalty = ln(1.0 + totalPricePerMillion(model).coerceAtLeast(0.0))
                    contextScore - (0.55 * costPenalty)
                }
            }
            "High-end" -> {
                // OpenRouter does not expose one universal quality ranking in /models.
                // Use live premium pricing + context as a practical quality/capability proxy,
                // while keeping provider diversity so one vendor cannot fill the whole council.
                val premium = catalogue.filterNot(::isFree)
                diverseTop(if (premium.isNotEmpty()) premium else catalogue, 4) { model ->
                    val premiumSignal = ln(1.0 + totalPricePerMillion(model).coerceAtLeast(0.0))
                    val contextSignal = ln(1.0 + model.contextLength.coerceAtLeast(1).toDouble())
                    (1.8 * premiumSignal) + contextSignal
                }
            }
            else -> emptyList()
        }

        if (chosen.size < 2) return
        settings.setCouncilModels(chosen.map { it.id }.toSet())

        // Chairman follows the strongest member of the chosen preset rather than an old fixed ID.
        val chairman = chosen.maxByOrNull { model ->
            val premiumSignal = ln(1.0 + totalPricePerMillion(model).coerceAtLeast(0.0))
            val contextSignal = ln(1.0 + model.contextLength.coerceAtLeast(1).toDouble())
            premiumSignal + contextSignal
        } ?: chosen.first()
        settings.setChairman(chairman.id)
    }

    fun runCouncil(question: String) {
        if (question.isBlank() || activeRun?.isActive == true) return
        activeRun = viewModelScope.launch {
            try {
                val result = engine.run(question.trim()) { _run.value = it }
                val final = result.chairman
                if (result.stage == CouncilStage.COMPLETE && final != null) {
                    val title = question.trim().lineSequence().firstOrNull().orEmpty().take(48).ifBlank { "New conversation" }
                    withContext(Dispatchers.IO) {
                        historyDb.insert(title, question.trim(), final.text, final.model, settings.councilModels())
                    }
                    loadHistory()
                }
            } catch (e: kotlinx.coroutines.CancellationException) {
                _run.value = _run.value.copy(stage = CouncilStage.CANCELLED, finishedAt = System.currentTimeMillis())
            } catch (e: Exception) {
                _run.value = _run.value.copy(
                    stage = CouncilStage.ERROR,
                    errors = _run.value.errors + ("App" to (e.message ?: e.toString())),
                    finishedAt = System.currentTimeMillis()
                )
            }
        }
    }

    fun cancelRun() { activeRun?.cancel() }
    fun clearRun() { if (activeRun?.isActive != true) _run.value = CouncilRun("") }

    fun loadHistory() {
        viewModelScope.launch { _history.value = withContext(Dispatchers.IO) { historyDb.list() } }
    }

    fun clearHistory() {
        viewModelScope.launch {
            withContext(Dispatchers.IO) { historyDb.clear() }
            _history.value = emptyList()
        }
    }
}
