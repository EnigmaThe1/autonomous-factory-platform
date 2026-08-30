package com.llmcouncil.mobile

import android.content.Context
import com.llmcouncil.mobile.data.CouncilRunStore
import com.llmcouncil.mobile.model.CouncilRun
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

object CouncilRuntime {
    private val _run = MutableStateFlow(CouncilRun(""))
    val run: StateFlow<CouncilRun> = _run.asStateFlow()
    @Volatile private var initialised = false

    fun initialise(context: Context) {
        if (initialised) return
        synchronized(this) {
            if (initialised) return
            CouncilRunStore(context.applicationContext).load()?.let { _run.value = it }
            initialised = true
        }
    }

    fun update(run: CouncilRun) { _run.value = run }
    fun clear(context: Context) {
        CouncilRunStore(context.applicationContext).clear()
        _run.value = CouncilRun("")
    }
}
