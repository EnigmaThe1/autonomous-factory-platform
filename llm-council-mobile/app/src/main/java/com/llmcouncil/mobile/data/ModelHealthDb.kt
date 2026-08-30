package com.llmcouncil.mobile.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import com.llmcouncil.mobile.model.ModelHealth
import com.llmcouncil.mobile.model.ModelSource

class ModelHealthDb(context: Context) : SQLiteOpenHelper(context, "llm_council_health.db", null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """CREATE TABLE model_health(
                model_key TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                successes INTEGER NOT NULL DEFAULT 0,
                failures INTEGER NOT NULL DEFAULT 0,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                last_status TEXT NOT NULL DEFAULT 'untested',
                last_error TEXT,
                last_tested_at INTEGER NOT NULL DEFAULT 0,
                last_success_at INTEGER NOT NULL DEFAULT 0
            )""".trimIndent()
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    fun record(modelKey: String, success: Boolean, error: String? = null) {
        val now = System.currentTimeMillis()
        val old = get(modelKey)
        val values = ContentValues().apply {
            put("model_key", modelKey)
            put("source", ModelSource.fromKey(modelKey).name)
            put("successes", (old?.successes ?: 0) + if (success) 1 else 0)
            put("failures", (old?.failures ?: 0) + if (success) 0 else 1)
            put("consecutive_failures", if (success) 0 else (old?.consecutiveFailures ?: 0) + 1)
            put("last_status", if (success) "working" else "failed")
            put("last_error", if (success) null else error?.take(800))
            put("last_tested_at", now)
            put("last_success_at", if (success) now else (old?.lastSuccessAt ?: 0L))
        }
        writableDatabase.insertWithOnConflict("model_health", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun get(modelKey: String): ModelHealth? {
        readableDatabase.query("model_health", null, "model_key=?", arrayOf(modelKey), null, null, null).use { c ->
            if (!c.moveToFirst()) return null
            return c.toHealth()
        }
    }

    fun list(): List<ModelHealth> {
        readableDatabase.query("model_health", null, null, null, null, null, "last_tested_at DESC").use { c ->
            val out = mutableListOf<ModelHealth>()
            while (c.moveToNext()) out += c.toHealth()
            return out
        }
    }

    fun clear() { writableDatabase.delete("model_health", null, null) }

    private fun android.database.Cursor.toHealth() = ModelHealth(
        modelKey = getString(getColumnIndexOrThrow("model_key")),
        source = runCatching { ModelSource.valueOf(getString(getColumnIndexOrThrow("source"))) }.getOrDefault(ModelSource.OPENROUTER),
        successes = getInt(getColumnIndexOrThrow("successes")),
        failures = getInt(getColumnIndexOrThrow("failures")),
        consecutiveFailures = getInt(getColumnIndexOrThrow("consecutive_failures")),
        lastStatus = getString(getColumnIndexOrThrow("last_status")),
        lastError = getString(getColumnIndexOrThrow("last_error")),
        lastTestedAt = getLong(getColumnIndexOrThrow("last_tested_at")),
        lastSuccessAt = getLong(getColumnIndexOrThrow("last_success_at"))
    )
}
