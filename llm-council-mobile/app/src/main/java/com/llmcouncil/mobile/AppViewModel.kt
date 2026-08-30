package com.llmcouncil.mobile

import android.app.Application
import android.content.Intent
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.llmcouncil.mobile.data.HistoryDb
import com.llmcouncil.mobile.data.ModelHealthDb
import com.llmcouncil.mobile.data.OpenRouterClient
import com.llmcouncil.mobile.data.SecureSettings
import com.llmcouncil.mobile.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.ln

class AppViewModel(private val app: Application) : AndroidViewModel(app) {
    companion object { private const val QUALIFICATION_PROTOCOL_VERSION = 1 }

    private val settings = SecureSettings(app)
    private val client = OpenRouterClient(settings)
    private val historyDb = HistoryDb(app)
    private val healthDb = ModelHealthDb(app)

    val run: StateFlow<CouncilRun> = CouncilRuntime.run
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

    init {
        CouncilRuntime.initialise(app)
        loadHistory()
    }

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
            } catch (e: Exception) {
                _modelsError.value = e.message ?: e.toString()
            } finally {
                _modelsLoading.value = false
            }
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
            "only available on agentic harnesses", "only available through agentic harnesses",
            "only available via agentic", "restricted to agentic", "not available through the api", "only available to"
        ).any(text::contains)
    }

    private fun isSpecialPurpose(model: OpenRouterModel): Boolean {
        val s = "${model.apiId} ${model.name}".lowercase()
        return listOf(
            "embedding", "rerank", "moderation", "whisper", "transcription", "text-to-speech", "tts", "speech",
            "image-generation", "imagegen", "text-to-video", "video-generation", "lyria", "musicgen", "clip-preview"
        ).any(s::contains)
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
        val textModels = _models.value.filter(::isCouncilEligible)
        val chosen = when (name) {
            "Low cost" -> {
                val ranked = textModels.filter { it.pricingKnown }
                    .sortedWith(compareBy<OpenRouterModel> { totalPricePerMillion(it) }.thenByDescending { it.contextLength })
                val out = ranked.distinctBy { it.provider }.take(4).toMutableList()
                ranked.filter { it !in out }.take(4 - out.size).forEach(out::add)
                out
            }
            "Balanced" -> {
                val priced = textModels.filter { it.pricingKnown }
                diverseTop(if (priced.isNotEmpty()) priced else textModels, 4) {
                    ln(1.0 + it.contextLength.coerceAtLeast(1).toDouble()) - 0.55 * ln(1.0 + totalPricePerMillion(it).coerceAtLeast(0.0))
                }
            }
            "High-end" -> {
                val premium = textModels.filter { it.pricingKnown && !it.isFree }
                diverseTop(if (premium.isNotEmpty()) premium else textModels, 4) {
                    1.8 * ln(1.0 + totalPricePerMillion(it).coerceAtLeast(0.0)) + ln(1.0 + it.contextLength.coerceAtLeast(1).toDouble())
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
        val chairman = chosen.maxByOrNull {
            (if (name == "Free") 0.0 else ln(1.0 + totalPricePerMillion(it).coerceAtLeast(0.0))) +
                ln(1.0 + it.contextLength.coerceAtLeast(1).toDouble())
        } ?: chosen.first()
        settings.setChairman(chairman.id)
        _selectionVersion.value++
    }

    private fun qualificationUsable(text: String): Boolean {
        val clean = text.trim()
        if (clean.length < 100) return false
        val lower = clean.lowercase()
        if (lower in setOf("null", "nil", "none", "n/a", "ok")) return false
        if (!lower.contains("council-probe-27")) return false
        if (!lower.contains("7")) return false
        if (!lower.contains("alpha") || !lower.contains("beta")) return false
        val alphaChars = clean.count { it.isLetter() }
        return alphaChars >= 50 && alphaChars.toDouble() / clean.length.coerceAtLeast(1) > 0.18
    }

    private suspend fun qualifyModel(model: OpenRouterModel): Boolean {
        val prompt = """Council compatibility probe. This is not a knowledge test. Return a substantive plain-text response that proves normal text generation and instruction following.
Include all of the following:
1. The exact marker COUNCIL-PROBE-27.
2. State that 3 + 4 = 7.
3. Compare the words alpha and beta in one complete sentence.
4. Add one complete sentence explaining why an empty response would be unusable for a review council.
Do not return only JSON, a tool call, nil, null, or a single word."""
        return try {
            val answer = client.chat(model.id, prompt, 160)
            val ok = qualificationUsable(answer)
            withContext(Dispatchers.IO) {
                healthDb.recordQualification(
                    model.id,
                    QUALIFICATION_PROTOCOL_VERSION,
                    ok,
                    if (ok) null else "Qualification returned empty/malformed/noncompliant text"
                )
            }
            ok
        } catch (e: Exception) {
            withContext(Dispatchers.IO) {
                healthDb.recordQualification(model.id, QUALIFICATION_PROTOCOL_VERSION, false, "Qualification: ${e.message ?: e}")
            }
            false
        }
    }

    private suspend fun resolveFreePreset(probeIfNeeded: Boolean) {
        if (_models.value.isEmpty()) {
            try { _models.value = client.models() }
            catch (e: Exception) { _modelsError.value = e.message ?: e.toString(); return }
        }
        val candidates = _models.value.filter(::isFreeCouncilEligible)
        if (candidates.size < 2) {
            _modelsError.value = "Fewer than two unrestricted zero-price text-chat models are currently visible in OpenRouter."
            return
        }
        val health = withContext(Dispatchers.IO) { healthDb.list() }
        val byId = health.associateBy { it.modelKey }
        val freshCutoff = System.currentTimeMillis() - 7L * 24 * 60 * 60 * 1000
        val verified = candidates.filter {
            byId[it.id]?.let { h ->
                h.verifiedWorking && h.qualificationVersion == QUALIFICATION_PROTOCOL_VERSION &&
                    h.lastQualifiedAt >= freshCutoff && h.consecutiveFailures == 0
            } == true
        }.toMutableList()

        if (verified.size < 4 && probeIfNeeded) {
            val ranked = candidates.sortedWith(
                compareByDescending<OpenRouterModel> { byId[it.id]?.verifiedWorking == true }
                    .thenBy { byId[it.id]?.consecutiveFailures ?: 0 }
                    .thenByDescending { it.contextLength }
            )
            for (model in ranked) {
                if (model in verified || verified.size >= 4) continue
                val old = byId[model.id]
                val recentlyFailedCurrentProtocol = old != null && old.qualificationVersion == QUALIFICATION_PROTOCOL_VERSION &&
                    !old.qualificationPassed && old.lastQualifiedAt >= freshCutoff
                if (recentlyFailedCurrentProtocol && old.consecutiveFailures >= 2) continue
                _verificationStatus.value = "Qualifying ${model.name}… ${verified.size}/4 confirmed"
                if (qualifyModel(model)) verified += model
            }
        }

        val latest = withContext(Dispatchers.IO) { healthDb.list() }
        _health.value = latest
        val workingIds = latest.filter {
            it.verifiedWorking && it.qualificationVersion == QUALIFICATION_PROTOCOL_VERSION && it.lastQualifiedAt >= freshCutoff && it.consecutiveFailures == 0
        }.map { it.modelKey }.toSet()
        val chosen = diverseTop(candidates.filter { it.id in workingIds }, 4) { ln(1.0 + it.contextLength.coerceAtLeast(1).toDouble()) }
        if (chosen.size < 2) {
            _modelsError.value = "Free qualification found fewer than two council-usable models. Open Model Learning Register to inspect failures and re-test later."
            _verificationStatus.value = "Free qualification finished: ${chosen.size} council-usable model(s)"
            return
        }
        applyChosenPreset("Free", chosen)
        _verificationStatus.value = "Free qualification complete: ${chosen.size} empirically usable models selected"
    }

    fun verifyFreeModels() { settings.setActivePreset("Free"); viewModelScope.launch { resolveFreePreset(true) } }
    fun loadHealth() { viewModelScope.launch { _health.value = withContext(Dispatchers.IO) { healthDb.list() } } }
    fun clearHealth() { viewModelScope.launch { withContext(Dispatchers.IO) { healthDb.clear() }; _health.value = emptyList() } }

    fun runCouncil(question: String) {
        val clean = question.trim()
        if (clean.isBlank() || run.value.stage in listOf(CouncilStage.STAGE1, CouncilStage.STAGE2, CouncilStage.STAGE3)) return
        viewModelScope.launch {
            if (settings.activePreset() == "Free") resolveFreePreset(probeIfNeeded = true)
            val intent = Intent(app, CouncilService::class.java).apply {
                action = CouncilService.ACTION_START
                putExtra(CouncilService.EXTRA_QUESTION, clean)
            }
            ContextCompat.startForegroundService(app, intent)
        }
    }

    fun cancelRun() {
        app.startService(Intent(app, CouncilService::class.java).apply { action = CouncilService.ACTION_CANCEL })
    }

    fun clearRun() {
        if (run.value.stage !in listOf(CouncilStage.STAGE1, CouncilStage.STAGE2, CouncilStage.STAGE3)) CouncilRuntime.clear(app)
    }

    fun loadHistory() { viewModelScope.launch { _history.value = withContext(Dispatchers.IO) { historyDb.list() } } }
    fun clearHistory() { viewModelScope.launch { withContext(Dispatchers.IO) { historyDb.clear() }; _history.value = emptyList() } }
}
