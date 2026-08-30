package com.llmcouncil.mobile

import android.app.Application
import android.content.Intent
import android.net.Uri
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.llmcouncil.mobile.data.ExportManager
import com.llmcouncil.mobile.data.GitHubClient
import com.llmcouncil.mobile.data.SecureSettings
import com.llmcouncil.mobile.model.GitHubRepo
import com.llmcouncil.mobile.model.RepoAuditRun
import com.llmcouncil.mobile.model.RepoAuditStage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class RepoAuditViewModel(private val app: Application) : AndroidViewModel(app) {
    private val settings = SecureSettings(app)
    private val github = GitHubClient(settings)
    val run: StateFlow<RepoAuditRun> = RepoAuditRuntime.run

    private val _repos = MutableStateFlow<List<GitHubRepo>>(emptyList())
    val repos: StateFlow<List<GitHubRepo>> = _repos.asStateFlow()
    private val _loading = MutableStateFlow(false)
    val loading: StateFlow<Boolean> = _loading.asStateFlow()
    private val _message = MutableStateFlow<String?>(null)
    val message: StateFlow<String?> = _message.asStateFlow()

    init { RepoAuditRuntime.initialise(app); CouncilRuntime.initialise(app) }

    fun githubConfigured(): Boolean = settings.getGitHubToken().isNotBlank()
    fun saveGitHubToken(value: String) {
        settings.setGitHubToken(value.trim())
        if (value.isNotBlank()) loadRepos()
    }

    fun loadRepos() {
        if (_loading.value) return
        viewModelScope.launch {
            _loading.value = true; _message.value = null
            try { _repos.value = github.listRepos() }
            catch (e: Exception) { _message.value = e.message ?: e.toString() }
            finally { _loading.value = false }
        }
    }

    fun start(repo: GitHubRepo, ref: String) {
        val running = run.value.stage in listOf(RepoAuditStage.SNAPSHOT, RepoAuditStage.INDEPENDENT, RepoAuditStage.PEER_REVIEW, RepoAuditStage.VERIFY, RepoAuditStage.CHAIRMAN)
        if (running) return
        val intent = Intent(app, RepoAuditService::class.java).apply {
            action = RepoAuditService.ACTION_START
            putExtra(RepoAuditService.EXTRA_REPO, repo.fullName)
            putExtra(RepoAuditService.EXTRA_REF, ref.ifBlank { repo.defaultBranch })
        }
        ContextCompat.startForegroundService(app, intent)
    }

    fun cancel() { app.startService(Intent(app, RepoAuditService::class.java).apply { action = RepoAuditService.ACTION_CANCEL }) }
    fun clear() { RepoAuditRuntime.clear(app) }

    fun setExportTree(uri: Uri) {
        settings.setExportTreeUri(uri.toString())
        _message.value = "Export workspace saved"
    }

    fun exportTree(): Uri? = settings.exportTreeUri()?.let(Uri::parse)

    fun exportCurrent() {
        val uri = exportTree()
        if (uri == null) { _message.value = "Choose an export workspace folder first"; return }
        val current = run.value
        if (current.repoFullName.isBlank()) { _message.value = "No repository audit is available to export"; return }
        viewModelScope.launch {
            _loading.value = true
            try {
                val result = withContext(Dispatchers.IO) { ExportManager.exportRepoAudit(app, uri, current) }
                _message.value = "Exported repository audit to $result"
            } catch (e: Exception) { _message.value = "Export failed: ${e.message ?: e}" }
            finally { _loading.value = false }
        }
    }

    fun exportLastCouncil() {
        val uri = exportTree()
        if (uri == null) { _message.value = "Choose an export workspace folder first"; return }
        val council = CouncilRuntime.run.value
        if (council.question.isBlank()) { _message.value = "No standard council run is available to export"; return }
        viewModelScope.launch {
            _loading.value = true
            try {
                val result = withContext(Dispatchers.IO) { ExportManager.exportCouncilRun(app, uri, council) }
                _message.value = "Exported council run to $result"
            } catch (e: Exception) { _message.value = "Council export failed: ${e.message ?: e}" }
            finally { _loading.value = false }
        }
    }

    fun clearMessage() { _message.value = null }
}
