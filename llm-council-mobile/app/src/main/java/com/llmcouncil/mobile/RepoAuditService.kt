package com.llmcouncil.mobile

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.llmcouncil.mobile.data.GitHubClient
import com.llmcouncil.mobile.data.ModelHealthDb
import com.llmcouncil.mobile.data.OpenRouterClient
import com.llmcouncil.mobile.data.SecureSettings
import com.llmcouncil.mobile.domain.RepoAuditEngine
import com.llmcouncil.mobile.model.GitHubRepo
import com.llmcouncil.mobile.model.RepoAuditRun
import com.llmcouncil.mobile.model.RepoAuditStage
import kotlinx.coroutines.*

class RepoAuditService : Service() {
    companion object {
        const val ACTION_START = "com.llmcouncil.mobile.action.START_REPO_AUDIT"
        const val ACTION_CANCEL = "com.llmcouncil.mobile.action.CANCEL_REPO_AUDIT"
        const val EXTRA_REPO = "repo"
        const val EXTRA_REF = "ref"
        private const val CHANNEL = "repo_audit_runs"
        private const val NOTIFICATION_ID = 4405
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var active: Job? = null

    override fun onCreate() {
        super.onCreate()
        RepoAuditRuntime.initialise(this)
        createChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CANCEL -> {
                active?.cancel()
                val cancelled = RepoAuditRuntime.run.value.copy(stage = RepoAuditStage.CANCELLED, finishedAt = System.currentTimeMillis())
                RepoAuditRuntime.update(this, cancelled)
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
            ACTION_START -> {
                val repo = intent.getStringExtra(EXTRA_REPO).orEmpty().trim()
                val ref = intent.getStringExtra(EXTRA_REF).orEmpty().trim().ifBlank { "main" }
                if (repo.isNotBlank() && active?.isActive != true) startAudit(repo, ref)
            }
        }
        return START_REDELIVER_INTENT
    }

    private fun startAudit(repoFullName: String, ref: String) {
        startForeground(NOTIFICATION_ID, notification("Preparing repository snapshot…", indeterminate = true))
        active = scope.launch {
            val settings = SecureSettings(this@RepoAuditService)
            val github = GitHubClient(settings)
            val ai = OpenRouterClient(settings)
            val engine = RepoAuditEngine(ai, settings, ModelHealthDb(this@RepoAuditService))
            try {
                var state = RepoAuditRun(repoFullName = repoFullName, ref = ref, stage = RepoAuditStage.SNAPSHOT)
                RepoAuditRuntime.update(this@RepoAuditService, state)
                val repo = GitHubRepo(repoFullName, ref, privateRepo = false, updatedAt = "")
                val snapshot = github.snapshot(repo, ref) { current, total, path ->
                    val pct = if (total <= 0) 0 else (current * 100 / total)
                    notifyProgress("Snapshot $current/$total · ${path.takeLast(38)}", pct)
                }
                state = state.copy(commitSha = snapshot.commitSha, requiredFiles = snapshot.requiredFiles.size, excludedFiles = snapshot.excluded.size)
                RepoAuditRuntime.update(this@RepoAuditService, state)

                val result = engine.run(snapshot) { update ->
                    RepoAuditRuntime.update(this@RepoAuditService, update)
                    notifyAudit(update)
                }
                RepoAuditRuntime.update(this@RepoAuditService, result)
                val finalText = when (result.stage) {
                    RepoAuditStage.COMPLETE -> "Repository audit finished · tap to view"
                    RepoAuditStage.CANCELLED -> "Repository audit cancelled"
                    else -> "Repository audit stopped · tap for diagnostics"
                }
                val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                manager.notify(NOTIFICATION_ID, notification(finalText, indeterminate = false, ongoing = false))
            } catch (e: CancellationException) {
                val cancelled = RepoAuditRuntime.run.value.copy(stage = RepoAuditStage.CANCELLED, finishedAt = System.currentTimeMillis())
                RepoAuditRuntime.update(this@RepoAuditService, cancelled)
            } catch (e: Exception) {
                val failed = RepoAuditRuntime.run.value.copy(
                    stage = RepoAuditStage.ERROR,
                    errors = RepoAuditRuntime.run.value.errors + ("Repository audit" to (e.message ?: e.toString())),
                    finishedAt = System.currentTimeMillis()
                )
                RepoAuditRuntime.update(this@RepoAuditService, failed)
                val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                manager.notify(NOTIFICATION_ID, notification("Repository audit failed · tap for diagnostics", false, false))
            } finally {
                stopForeground(STOP_FOREGROUND_DETACH)
                stopSelf()
            }
        }
    }

    private fun notifyAudit(run: RepoAuditRun) {
        val text = when (run.stage) {
            RepoAuditStage.SNAPSHOT -> "Building repository manifest"
            RepoAuditStage.INDEPENDENT -> {
                val complete = run.modelAudits.count { it.complete }
                val partial = run.modelAudits.lastOrNull()
                val coverage = partial?.let { if (it.requiredCount == 0) 0 else it.coveredCount * 100 / it.requiredCount } ?: 0
                "Independent audits · $complete complete · current coverage $coverage%"
            }
            RepoAuditStage.PEER_REVIEW -> "Peer-reviewing exhaustive audits"
            RepoAuditStage.VERIFY -> "Adversarial finding verification"
            RepoAuditStage.CHAIRMAN -> "Chairman final synthesis"
            RepoAuditStage.COMPLETE -> "Repository audit finished"
            RepoAuditStage.ERROR -> "Repository audit stopped"
            RepoAuditStage.CANCELLED -> "Repository audit cancelled"
            else -> "Repository audit running"
        }
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, notification(text, indeterminate = run.stage !in listOf(RepoAuditStage.COMPLETE, RepoAuditStage.ERROR, RepoAuditStage.CANCELLED)))
    }

    private fun notifyProgress(text: String, pct: Int) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, notification(text, false, true, pct))
    }

    private fun notification(text: String, indeterminate: Boolean, ongoing: Boolean = true, progress: Int? = null): Notification {
        val openIntent = Intent(this, RepoAuditActivity::class.java)
        val pending = PendingIntent.getActivity(this, 4405, openIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val cancelIntent = Intent(this, RepoAuditService::class.java).apply { action = ACTION_CANCEL }
        val cancel = PendingIntent.getService(this, 4406, cancelIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val builder = NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setContentTitle("LLM Council · Repository Audit")
            .setContentText(text)
            .setContentIntent(pending)
            .setOnlyAlertOnce(true)
            .setOngoing(ongoing)
            .setPriority(NotificationCompat.PRIORITY_LOW)
        if (ongoing) builder.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Cancel", cancel)
        when {
            progress != null -> builder.setProgress(100, progress.coerceIn(0, 100), false)
            indeterminate -> builder.setProgress(0, 0, true)
            else -> builder.setProgress(0, 0, false)
        }
        return builder.build()
    }

    private fun createChannel() {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(NotificationChannel(CHANNEL, "Repository audits", NotificationManager.IMPORTANCE_LOW).apply {
            description = "Progress and completion for exhaustive LLM Council repository audits"
        })
    }

    override fun onDestroy() {
        super.onDestroy()
        if (active?.isCompleted == true) scope.cancel()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
