package com.llmcouncil.mobile

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.llmcouncil.mobile.data.HistoryDb
import com.llmcouncil.mobile.data.ModelHealthDb
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
    private val historyDb = HistoryDb(app)
    private val healthDb = ModelHealthDb(app)
    private val engine = CouncilEngine(client, settings, healthDb)

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
    private val _health = MutableStateFlow<List<ModelHealth>>(emptyList())
    val health: StateFlow<List<ModelHealth>> = _health.asStateFlow()
    private val _verificationStatus = MutableStateFlow<String?>(null)
    val verificationStatus: StateFlow<String?> = _verificationStatus.asStateFlow()
    private val _selectionVersion = MutableStateFlow(0)
    val selectionVersion: StateFlow<Int> = _selectionVersion.asStateFlow()
    private var activeRun: Job? = null

    fun hasApiKey(): Boolean = settings.getOpenRouterKey().isNotBlank()
    fun saveApiKey(key: String) = saveProviderKey(ModelSource.OPENROUTER, key)
    fun selectedModels(): Set<String> = settings.councilModels().toSet()
    fun chairman(): String = settings.chairman()
    fun concurrency(): Int = settings.maxConcurrency()
    fun setConcurrency(v: Int) = settings.setMaxConcurrency(v)
    fun activePreset(): String? = settings.activePreset()

    fun providerKeyConfigured(source: ModelSource): Boolean = when (source) {
        ModelSource.OPENROUTER -> settings.getOpenRouterKey().isNotBlank()
        ModelSource.OPENAI -> settings.getOpenAiKey().isNotBlank()
        ModelSource.ANTHROPIC -> settings.getAnthropicKey().isNotBlank()
        ModelSource.GEMINI -> settings.getGeminiKey().isNotBlank()
    }

    fun saveProviderKey(source: ModelSource, key: String) {
        val clean = key.trim()
        when (source) {
            ModelSource.OPENROUTER -> settings.setOpenRouterKey(clean)
            ModelSource.OPENAI -> settings.setOpenAiKey(clean)
            ModelSource.ANTHROPIC -> settings.setAnthropicKey(clean)
            ModelSource.GEMINI -> settings.setGeminiKey(clean)
        }
        loadModels(true)
    }

    fun loadModels(force: Boolean = false) {
        if (_modelsLoading.value || (!force && _models.value.isNotEmpty())) return
        viewModelScope.launch {
            _modelsLoading.value = true
            _modelsError.value = null
            try {
                _models.value = client.models()
                if (settings.activePreset() == "Free") resolveFreePreset(probeIfNeeded = false)
            } catch (e: Exception) { _modelsError.value = e.message ?: e.toString() }
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
        settings.setActivePreset(null)
        _selectionVersion.value++
    }

    fun setChairman(id: String) {
        settings.setChairman(id)
        settings.setActivePreset(null)
        _selectionVersion.value++
    }

    private fun totalPricePerMillion(model: OpenRouterModel): Double = model.promptPricePerMillion + model.completionPricePerMillion

    private fun isRestricted(model: OpenRouterModel): Boolean {
        val text = model.description.lowercase()
        return listOf(
            "only available on agentic harnesses",
            "only available through agentic harnesses",
            "only available via agentic",
            "restricted to agentic",
            "not available through the api",
            "only available to"
        ).any(text::contains)
    }

    private fun isSpecialPurpose(model: OpenRouterModel): Boolean {
        val s = "${model.apiId} ${model.name}".lowercase()
        val blocked = listOf(
            "embedding", "rerank", "moderation", "whisper", "transcription",
            "text-to-speech", "tts", "speech", "image-generation", "imagegen",
            "text-to-video", "video-generation", "lyria", "musicgen", "clip-preview"
        )
        return blocked.any(s::contains)
    }

    fun isCouncilEligible(model: OpenRouterModel): Boolean =
        model.acceptsText && model.returnsText && !isRestricted(model) && !isSpecialPurpose(model) &&
            model.apiId != "openrouter/auto" && model.apiId != "openrouter/free"

    fun isFreeCouncilEligible(model: OpenRouterModel): Boolean =
        model.source == ModelSource.OPENROUTER && isCouncilEligible(model) && model.isFree

    fun freeEligibleCount(): Int = _models.value.count(::isFreeCouncilEligible)

    private fun diverseTop(source: List<OpenRouterModel>, limit: Int = 4, score: (OpenRouterModel) -> Double): List<OpenRouterModel> {
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

    fun applyPreset(name: String) {
        if (name == "Free") {
            settings.setActivePreset("Free")
            viewModelScope.launch { resolveFreePreset(probeIfNeeded = true) }
            return
        }
        val catalogue = _models.value
        if (catalogue.isEmpty()) return
        val textModels = catalogue.filter(::isCouncilEligible)
        val chosen: List<OpenRouterModel> = when (name) {
            "Low cost" -> {
                val priced = textModels.filter { it.pricingKnown }
                val ranked = priced.sortedWith(compareBy<OpenRouterModel> { totalPricePerMillion(it) }.thenByDescending { it.contextLength })
                val firstPerProvider = ranked.distinctBy { it.provider }.take(4).toMutableList()
                if (firstPerProvider.size < 4) ranked.filter { it !in firstPerProvider }.take(4 - firstPerProvider.size).forEach(firstPerProvider::add)
                firstPerProvider
            }
            "Balanced" -> {
                val priced = textModels.filter { it.pricingKnown }
                diverseTop(if (priced.isNotEmpty()) priced else textModels, 4) { model ->
                    val contextScore = ln(1.0 + model.contextLength.coerceAtLeast(1).toDouble())
                    val costPenalty = ln(1.0 + totalPricePerMillion(model).coerceAtLeast(0.0))
                    contextScore - (0.55 * costPenalty)
                }
            }
            "High-end" -> {
                val premium = textModels.filter { it.pricingKnown && !it.isFree }
                diverseTop(if (premium.isNotEmpty()) premium else textModels, 4) { model ->
                    val premiumSignal = ln(1.0 + totalPricePerMillion(model).coerceAtLeast(0.0))
                    val contextSignal = ln(1.0 + model.contextLength.coerceAtLeast(1).toDouble())
                    (1.8 * premiumSignal) + contextSignal
                }
            }
            else -> emptyList()
        }
        applyChosenPreset(name, chosen)
    }

    private fun applyChosenPreset(name: String, chosen: List<OpenRouterModel>) {
        if (chosen.size < 2) {
            _modelsError.value = "Fewer than two eligible models are currently available for $name."
            return
        }
        _modelsError.value = null
        settings.setActivePreset(name)
        settings.setCouncilModels(chosen.map { it.id }.toSet())
        val chairman = chosen.maxByOrNull { model ->
            val priceSignal = if (name == "Free") 0.0 else ln(1.0 + totalPricePerMillion(model).coerceAtLeast(0.0))
            val contextSignal = ln(1.0 + model.contextLength.coerceAtLeast(1).toDouble())
            priceSignal + contextSignal
        } ?: chosen.first()
        settings.setChairman(chairman.id)
        _selectionVersion.value++
    }

    private suspend fun resolveFreePreset(probeIfNeeded: Boolean) {
        if (_models.value.isEmpty()) {
            try { _models.value = client.models() } catch (e: Exception) { _modelsError.value = e.message ?: e.toString(); return }
        }
        val candidates = _models.value.filter(::isFreeCouncilEligible)
        if (candidates.size < 2) {
            _modelsError.value = "Fewer than two unrestricted zero-price text-chat models are currently visible in OpenRouter."
            return
        }
        val health = withContext(Dispatchers.IO) { healthDb.list() }
        val byId = health.associateBy { it.modelKey }
        val freshCutoff = System.currentTimeMillis() - 7L * 24 * 60 * 60 * 1000
        val verified = candidates.filter { c -> byId[c.id]?.let { it.verifiedWorking && it.lastSuccessAt >= freshCutoff } == true }.toMutableList()

        if (verified.size < 4 && probeIfNeeded) {
            _verificationStatus.value = "Verifying free models… ${verified.size}/4 confirmed"
            val ranked = candidates.sortedWith(
                compareByDescending<OpenRouterModel> { byId[it.id]?.verifiedWorking == true }
                    .thenBy { byId[it.id]?.consecutiveFailures ?: 0 }
                    .thenByDescending { it.contextLength }
            )
            for (model in ranked) {
                if (model in verified) continue
                if (verified.size >= 4) break
                val old = byId[model.id]
                if (old != null && old.consecutiveFailures >= 2 && old.lastTestedAt >= freshCutoff) continue
                _verificationStatus.value = "Testing ${model.name}… ${verified.size}/4 confirmed"
                val ok = try {
                    val answer = client.chat(model.id, "Reply with exactly: OK", 16)
                    answer.trim().isNotBlank()
                } catch (e: Exception) {
                    withContext(Dispatchers.IO) { healthDb.record(model.id, false, e.message ?: e.toString()) }
                    false
                }
                if (ok) {
                    withContext(Dispatchers.IO) { healthDb.record(model.id, true) }
                    verified += model
                }
            }
        }

        val latestHealth = withContext(Dispatchers.IO) { healthDb.list() }
        _health.value = latestHealth
        val workingIds = latestHealth.filter { it.verifiedWorking }.map { it.modelKey }.toSet()
        val working = candidates.filter { it.id in workingIds }
        val chosen = diverseTop(working, 4) { ln(1.0 + it.contextLength.coerceAtLeast(1).toDouble()) }
        if (chosen.size < 2) {
            _modelsError.value = "Free verification found fewer than two working models. Open Model Learning Register to inspect failures and re-test later."
            _verificationStatus.value = "Free verification finished: ${chosen.size} working model(s)"
            return
        }
        applyChosenPreset("Free", chosen)
        _verificationStatus.value = "Free verification complete: ${chosen.size} verified working models selected"
    }

    fun verifyFreeModels() {
        settings.setActivePreset("Free")
        viewModelScope.launch { resolveFreePreset(probeIfNeeded = true) }
    }

    fun loadHealth() {
        viewModelScope.launch { _health.value = withContext(Dispatchers.IO) { healthDb.list() } }
    }

    fun clearHealth() {
        viewModelScope.launch {
            withContext(Dispatchers.IO) { healthDb.clear() }
            _health.value = emptyList()
        }
    }

    fun runCouncil(question: String) {
        if (question.isBlank() || activeRun?.isActive == true) return
        activeRun = viewModelScope.launch {
            try {
                if (settings.activePreset() == "Free") resolveFreePreset(probeIfNeeded = true)
                val result = engine.run(question.trim()) { _run.value = it }
                loadHealth()
                val final = result.chairman
                if (result.stage == CouncilStage.COMPLETE && final != null) {
                    val title = question.trim().lineSequence().firstOrNull().orEmpty().take(48).ifBlank { "New conversation" }
                    withContext(Dispatchers.IO) { historyDb.insert(title, question.trim(), final.text, final.model, settings.councilModels()) }
                    loadHistory()
                }
            } catch (e: kotlinx.coroutines.CancellationException) {
                _run.value = _run.value.copy(stage = CouncilStage.CANCELLED, finishedAt = System.currentTimeMillis())
            } catch (e: Exception) {
                _run.value = _run.value.copy(stage = CouncilStage.ERROR, errors = _run.value.errors + ("App" to (e.message ?: e.toString())), finishedAt = System.currentTimeMillis())
            }
        }
    }

    fun cancelRun() { activeRun?.cancel() }
    fun clearRun() { if (activeRun?.isActive != true) _run.value = CouncilRun("") }
    fun loadHistory() { viewModelScope.launch { _history.value = withContext(Dispatchers.IO) { historyDb.list() } } }
    fun clearHistory() { viewModelScope.launch { withContext(Dispatchers.IO) { historyDb.clear() }; _history.value = emptyList() } }
}
