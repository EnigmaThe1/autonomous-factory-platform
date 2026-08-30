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
            _modelsLoading.value = true; _modelsError.value = null
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

    fun applyPreset(name: String) {
        val available = _models.value.map { it.id }.toSet()
        val candidates = when (name) {
            "Original" -> listOf("openai/gpt-5.1", "google/gemini-3-pro-preview", "anthropic/claude-sonnet-4.5", "x-ai/grok-4")
            "Low cost" -> _models.value.sortedBy { it.promptPricePerToken + it.completionPricePerToken }.take(4).map { it.id }
            "Balanced" -> listOfNotNull(
                _models.value.firstOrNull { it.id.startsWith("openai/") }?.id,
                _models.value.firstOrNull { it.id.startsWith("anthropic/") }?.id,
                _models.value.firstOrNull { it.id.startsWith("google/") }?.id,
                _models.value.firstOrNull { it.id.startsWith("x-ai/") }?.id
            )
            else -> emptyList()
        }.filter { it in available || name == "Original" }.distinct()
        if (candidates.size >= 2) settings.setCouncilModels(candidates.toSet())
        val current = settings.councilModels()
        if (settings.chairman() !in current && current.isNotEmpty()) settings.setChairman(current.first())
    }

    fun runCouncil(question: String) {
        if (question.isBlank() || activeRun?.isActive == true) return
        activeRun = viewModelScope.launch {
            try {
                val result = engine.run(question.trim()) { _run.value = it }
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

    fun loadHistory() {
        viewModelScope.launch { _history.value = withContext(Dispatchers.IO) { historyDb.list() } }
    }

    fun clearHistory() {
        viewModelScope.launch { withContext(Dispatchers.IO) { historyDb.clear() }; _history.value = emptyList() }
    }
}
