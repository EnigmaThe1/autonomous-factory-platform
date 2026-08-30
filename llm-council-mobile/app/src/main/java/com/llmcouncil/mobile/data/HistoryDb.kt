package com.llmcouncil.mobile.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import com.llmcouncil.mobile.model.HistoryItem

class HistoryDb(context: Context) : SQLiteOpenHelper(context, "llm_council_v4.db", null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""
            CREATE TABLE history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                question TEXT NOT NULL,
                final_answer TEXT NOT NULL,
                chairman TEXT NOT NULL,
                council_models TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """.trimIndent())
    }
    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    fun insert(title: String, question: String, finalAnswer: String, chairman: String, models: List<String>) {
        writableDatabase.insert("history", null, ContentValues().apply {
            put("title", title); put("question", question); put("final_answer", finalAnswer)
            put("chairman", chairman); put("council_models", models.joinToString("\n")); put("created_at", System.currentTimeMillis())
        })
    }

    fun list(): List<HistoryItem> {
        val result = mutableListOf<HistoryItem>()
        readableDatabase.query("history", null, null, null, null, null, "created_at DESC", "100").use { c ->
            while (c.moveToNext()) {
                result += HistoryItem(
                    id = c.getLong(c.getColumnIndexOrThrow("id")),
                    title = c.getString(c.getColumnIndexOrThrow("title")),
                    question = c.getString(c.getColumnIndexOrThrow("question")),
                    finalAnswer = c.getString(c.getColumnIndexOrThrow("final_answer")),
                    chairman = c.getString(c.getColumnIndexOrThrow("chairman")),
                    councilModels = c.getString(c.getColumnIndexOrThrow("council_models")).split('\n').filter { it.isNotBlank() },
                    createdAt = c.getLong(c.getColumnIndexOrThrow("created_at"))
                )
            }
        }
        return result
    }

    fun clear() { writableDatabase.delete("history", null, null) }
}
