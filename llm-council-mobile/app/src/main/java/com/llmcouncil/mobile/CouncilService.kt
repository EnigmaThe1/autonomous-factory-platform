package com.llmcouncil.mobile

import android.app.*
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.llmcouncil.mobile.data.*
import com.llmcouncil.mobile.domain.CouncilEngine
import com.llmcouncil.mobile.model.CouncilRun
import com.llmcouncil.mobile.model.CouncilStage
import kotlinx.coroutines.*

class CouncilService : Service() {
    companion object {
        const val ACTION_START = "com.llmcouncil.mobile.action.START_COUNCIL"
        const val ACTION_CANCEL = "com.llmcouncil.mobile.action.CANCEL_COUNCIL"
        const val EXTRA_QUESTION = "question"
        private const val CHANNEL_ID = "council_runs"
        private const val NOTIFICATION_ID = 4401
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var runJob: Job? = null
    private lateinit var store: CouncilRunStore
    private lateinit var notificationManager: NotificationManager

    override fun onCreate() {
        super.onCreate()
        CouncilRuntime.initialise(this)
        store = CouncilRunStore(this)
        notificationManager = getSystemService(NotificationManager::class.java)
        createChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CANCEL -> cancelCurrentRun()
            ACTION_START -> {
                val question = intent.getStringExtra(EXTRA_QUESTION)?.trim().orEmpty()
                if (question.isNotBlank() && runJob?.isActive != true) startRun(question)
            }
        }
        return START_REDELIVER_INTENT
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private fun startRun(question: String) {
        startForeground(NOTIFICATION_ID, buildNotification("Preparing council…", ongoing = true))
        runJob = scope.launch {
            val settings = SecureSettings(this@CouncilService)
            val client = OpenRouterClient(settings)
            val healthDb = ModelHealthDb(this@CouncilService)
            val historyDb = HistoryDb(this@CouncilService)
            val engine = CouncilEngine(client, settings, healthDb)
            val checkpoint = store.load()?.takeIf {
                it.question == question && it.stage !in listOf(CouncilStage.COMPLETE, CouncilStage.CANCELLED)
            }
            try {
                val result = engine.run(question, checkpoint) { update ->
                    CouncilRuntime.update(update)
                    store.save(update)
                    notificationManager.notify(NOTIFICATION_ID, buildNotification(statusText(update), ongoing = true))
                }
                if (result.stage == CouncilStage.COMPLETE && result.chairman != null) {
                    val title = question.lineSequence().firstOrNull().orEmpty().take(48).ifBlank { "New conversation" }
                    historyDb.insert(title, question, result.chairman.text, result.chairman.model, settings.councilModels())
                    finishForeground("Council finished · tap to view result", result, completed = true)
                } else {
                    finishForeground(statusText(result), result, completed = false)
                }
            } catch (e: CancellationException) {
                val cancelled = (store.load() ?: CouncilRun(question)).copy(stage = CouncilStage.CANCELLED, finishedAt = System.currentTimeMillis())
                CouncilRuntime.update(cancelled)
                store.save(cancelled)
                finishForeground("Council run cancelled", cancelled, completed = false)
            } catch (e: Exception) {
                val current = store.load() ?: CouncilRun(question)
                val failed = current.copy(
                    stage = CouncilStage.ERROR,
                    errors = current.errors + ("Service" to (e.message ?: e.toString())),
                    finishedAt = System.currentTimeMillis()
                )
                CouncilRuntime.update(failed)
                store.save(failed)
                finishForeground("Council stopped with an error", failed, completed = false)
            } finally {
                runJob = null
                stopSelf()
            }
        }
    }

    private fun cancelCurrentRun() {
        runJob?.cancel()
        if (runJob == null) stopSelf()
    }

    private fun statusText(run: CouncilRun): String = when (run.stage) {
        CouncilStage.STAGE1 -> "Stage 1 · collecting model responses"
        CouncilStage.STAGE2 -> "Stage 2 · peer review"
        CouncilStage.STAGE3 -> "Stage 3 · chairman synthesis"
        CouncilStage.COMPLETE -> "Council finished · tap to view result"
        CouncilStage.ERROR -> "Council stopped with an error"
        CouncilStage.CANCELLED -> "Council run cancelled"
        else -> "Preparing council…"
    }

    private fun finishForeground(text: String, run: CouncilRun, completed: Boolean) {
        val notification = buildNotification(text, ongoing = false)
        if (Build.VERSION.SDK_INT >= 24) stopForeground(STOP_FOREGROUND_DETACH) else @Suppress("DEPRECATION") stopForeground(false)
        notificationManager.notify(NOTIFICATION_ID, notification)
    }

    private fun buildNotification(text: String, ongoing: Boolean): Notification {
        val openIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openPending = PendingIntent.getActivity(this, 0, openIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val cancelIntent = Intent(this, CouncilService::class.java).apply { action = ACTION_CANCEL }
        val cancelPending = PendingIntent.getService(this, 1, cancelIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_notify_chat)
            .setContentTitle("LLM Council")
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(openPending)
            .setOngoing(ongoing)
            .setOnlyAlertOnce(ongoing)
            .setCategory(NotificationCompat.CATEGORY_PROGRESS)
            .setPriority(NotificationCompat.PRIORITY_LOW)

        if (ongoing) builder.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Cancel", cancelPending)
        return builder.build()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            notificationManager.createNotificationChannel(
                NotificationChannel(CHANNEL_ID, "Council runs", NotificationManager.IMPORTANCE_LOW).apply {
                    description = "Progress and completion notifications for active LLM Council runs"
                    setShowBadge(false)
                }
            )
        }
    }
}
