package com.llmcouncil.mobile.data

import com.llmcouncil.mobile.model.OpenRouterModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

sealed class ApiFailure(message: String) : Exception(message) {
    class Authentication(message: String) : ApiFailure(message)
    class Credits(message: String) : ApiFailure(message)
    class RateLimit(message: String) : ApiFailure(message)
    class Unavailable(message: String) : ApiFailure(message)
    class Network(message: String) : ApiFailure(message)
    class Other(message: String) : ApiFailure(message)
}

class OpenRouterClient(private val settings: SecureSettings) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(25, TimeUnit.SECONDS)
        .readTimeout(150, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    private val jsonType = "application/json; charset=utf-8".toMediaType()

    suspend fun models(): List<OpenRouterModel> = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("https://openrouter.ai/api/v1/models")
            .header("Authorization", "Bearer ${settings.getApiKey()}")
            .header("Accept", "application/json")
            .build()
        client.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()
            if (!response.isSuccessful) throw failure(response.code, body)
            val data = JSONObject(body).optJSONArray("data") ?: JSONArray()
            buildList {
                for (i in 0 until data.length()) {
                    val o = data.optJSONObject(i) ?: continue
                    val id = o.optString("id").trim(); if (id.isEmpty()) continue
                    val pricing = o.optJSONObject("pricing")
                    add(OpenRouterModel(
                        id = id,
                        name = o.optString("name", id).ifBlank { id },
                        contextLength = o.optInt("context_length", 0),
                        promptPricePerToken = pricing?.optString("prompt")?.toDoubleOrNull() ?: 0.0,
                        completionPricePerToken = pricing?.optString("completion")?.toDoubleOrNull() ?: 0.0,
                        description = o.optString("description", "")
                    ))
                }
            }.sortedBy { it.name.lowercase() }
        }
    }

    suspend fun chat(model: String, prompt: String): String = withContext(Dispatchers.IO) {
        val payload = JSONObject()
            .put("model", model)
            .put("messages", JSONArray().put(JSONObject().put("role", "user").put("content", prompt)))
        val request = Request.Builder()
            .url("https://openrouter.ai/api/v1/chat/completions")
            .header("Authorization", "Bearer ${settings.getApiKey()}")
            .header("Content-Type", "application/json")
            .header("HTTP-Referer", "https://github.com/karpathy/llm-council")
            .header("X-Title", "LLM Council Mobile")
            .post(payload.toString().toRequestBody(jsonType))
            .build()
        client.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()
            if (!response.isSuccessful) throw failure(response.code, body)
            val root = JSONObject(body)
            root.getJSONArray("choices").getJSONObject(0).getJSONObject("message").optString("content", "")
        }
    }

    private fun failure(code: Int, body: String): ApiFailure {
        val message = try { JSONObject(body).optJSONObject("error")?.optString("message") ?: body } catch (_: Exception) { body }
        val clean = message.ifBlank { "OpenRouter HTTP $code" }.take(500)
        return when (code) {
            401, 403 -> ApiFailure.Authentication(clean)
            402 -> ApiFailure.Credits(clean)
            429 -> ApiFailure.RateLimit(clean)
            404, 408, 502, 503, 504 -> ApiFailure.Unavailable(clean)
            else -> ApiFailure.Other("HTTP $code — $clean")
        }
    }
}
