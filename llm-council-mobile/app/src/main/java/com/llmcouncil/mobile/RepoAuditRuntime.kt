package com.llmcouncil.mobile

import android.content.Context
import com.llmcouncil.mobile.data.RepoAuditCheckpointStore
import com.llmcouncil.mobile.model.RepoAuditRun
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

object RepoAuditRuntime {
    private val _run = MutableStateFlow(RepoAuditRun())
    val run: StateFlow<RepoAuditRun> = _run.asStateFlow()
    @Volatile private var initialised = false

    fun initialise(context: Context) {
        if (initialised) return
        synchronized(this) {
            if (initialised) return
            RepoAuditCheckpointStore(context.applicationContext).load()?.let { _run.value = it }
            initialised = true
        }
    }

    fun update(context: Context, value: RepoAuditRun) {
        _run.value = value
        RepoAuditCheckpointStore(context.applicationContext).save(value)
    }

    fun clear(context: Context) {
        _run.value = RepoAuditRun()
        RepoAuditCheckpointStore(context.applicationContext).clear()
    }
}
