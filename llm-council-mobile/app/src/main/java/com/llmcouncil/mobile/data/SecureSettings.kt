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
    // Keep historical storage names/alias so existing installed v5 credentials remain readable after the OmniCouncil rebrand.
    private val prefs=context.getSharedPreferences("llm_council_v4",Context.MODE_PRIVATE)
    private val alias="llm_council_openrouter_key"; private val separator=":"
    private fun secretKey():SecretKey { val ks=KeyStore.getInstance("AndroidKeyStore").apply{load(null)}; (ks.getKey(alias,null) as? SecretKey)?.let{return it}; val g=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore"); g.init(KeyGenParameterSpec.Builder(alias,KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setRandomizedEncryptionRequired(true).build()); return g.generateKey() }
    private fun setSecret(k:String,v:String){if(v.isBlank()){prefs.edit().remove(k).apply();return};val c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,secretKey());val enc=c.doFinal(v.toByteArray(StandardCharsets.UTF_8));prefs.edit().putString(k,Base64.encodeToString(c.iv,Base64.NO_WRAP)+separator+Base64.encodeToString(enc,Base64.NO_WRAP)).apply()}
    private fun getSecret(k:String):String { val packed=prefs.getString(k,null)?:return "";return try{val p=packed.split(separator,limit=2);val c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,secretKey(),GCMParameterSpec(128,Base64.decode(p[0],Base64.NO_WRAP)));String(c.doFinal(Base64.decode(p[1],Base64.NO_WRAP)),StandardCharsets.UTF_8)}catch(_:Exception){""} }
    fun setApiKey(v:String)=setOpenRouterKey(v);fun getApiKey()=getOpenRouterKey();fun setOpenRouterKey(v:String)=setSecret("api_key_enc",v);fun getOpenRouterKey()=getSecret("api_key_enc");fun setOpenAiKey(v:String)=setSecret("openai_key_enc",v);fun getOpenAiKey()=getSecret("openai_key_enc");fun setAnthropicKey(v:String)=setSecret("anthropic_key_enc",v);fun getAnthropicKey()=getSecret("anthropic_key_enc");fun setGeminiKey(v:String)=setSecret("gemini_key_enc",v);fun getGeminiKey()=getSecret("gemini_key_enc");fun setGitHubToken(v:String)=setSecret("github_token_enc",v);fun getGitHubToken()=getSecret("github_token_enc")
    fun exportTreeUri():String?=prefs.getString("export_tree_uri",null);fun setExportTreeUri(v:String?){prefs.edit().apply{if(v==null)remove("export_tree_uri")else putString("export_tree_uri",v)}.apply()}
    fun councilModels():List<String> = prefs.getStringSet("council_models",null)?.toList()?.sorted()?:listOf("openai/gpt-5.1","google/gemini-3-pro-preview","anthropic/claude-sonnet-4.5","x-ai/grok-4")
    fun setCouncilModels(ids:Set<String>){prefs.edit().putStringSet("council_models",ids).apply()};fun chairman():String=prefs.getString("chairman_model","google/gemini-3-pro-preview")?:"google/gemini-3-pro-preview";fun setChairman(id:String){prefs.edit().putString("chairman_model",id).apply()};fun maxConcurrency()=prefs.getInt("max_concurrency",6);fun setMaxConcurrency(v:Int){prefs.edit().putInt("max_concurrency",v.coerceIn(1,12)).apply()};fun activePreset():String?=prefs.getString("active_preset",null);fun setActivePreset(v:String?){prefs.edit().apply{if(v==null)remove("active_preset")else putString("active_preset",v)}.apply()}
}
