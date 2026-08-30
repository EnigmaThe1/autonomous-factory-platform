package com.llmcouncil.mobile.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecureSettings(context: Context) {
    private val prefs = context.getSharedPreferences("llm_council_v4", Context.MODE_PRIVATE)
    private val alias = "llm_council_openrouter_key"
    private val separator = ":"

    private fun secretKey(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val existing = ks.getKey(alias, null) as? SecretKey
        if (existing != null) return existing
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(
            KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        return generator.generateKey()
    }

    fun setApiKey(value: String) {
        if (value.isBlank()) { prefs.edit().remove("api_key_enc").apply(); return }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, secretKey())
        val encrypted = cipher.doFinal(value.toByteArray(StandardCharsets.UTF_8))
        val packed = Base64.encodeToString(cipher.iv, Base64.NO_WRAP) + separator + Base64.encodeToString(encrypted, Base64.NO_WRAP)
        prefs.edit().putString("api_key_enc", packed).apply()
    }

    fun getApiKey(): String {
        val packed = prefs.getString("api_key_enc", null) ?: return ""
        return try {
            val parts = packed.split(separator, limit = 2)
            val iv = Base64.decode(parts[0], Base64.NO_WRAP)
            val encrypted = Base64.decode(parts[1], Base64.NO_WRAP)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(128, iv))
            String(cipher.doFinal(encrypted), StandardCharsets.UTF_8)
        } catch (_: Exception) { "" }
    }

    fun councilModels(): List<String> = prefs.getStringSet("council_models", null)?.toList()?.sorted()
        ?: listOf("openai/gpt-5.1", "google/gemini-3-pro-preview", "anthropic/claude-sonnet-4.5", "x-ai/grok-4")

    fun setCouncilModels(ids: Set<String>) { prefs.edit().putStringSet("council_models", ids).apply() }
    fun chairman(): String = prefs.getString("chairman_model", "google/gemini-3-pro-preview") ?: "google/gemini-3-pro-preview"
    fun setChairman(id: String) { prefs.edit().putString("chairman_model", id).apply() }
    fun maxConcurrency(): Int = prefs.getInt("max_concurrency", 6)
    fun setMaxConcurrency(value: Int) { prefs.edit().putInt("max_concurrency", value.coerceIn(1, 12)).apply() }
}
