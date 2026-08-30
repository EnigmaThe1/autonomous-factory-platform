package com.llmcouncil.mobile.data

import android.util.Base64
import com.llmcouncil.mobile.model.GitHubRepo
import com.llmcouncil.mobile.model.RepoFile
import com.llmcouncil.mobile.model.RepoSnapshot
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.util.concurrent.TimeUnit

class GitHubClient(private val settings: SecureSettings) {
    private val http = OkHttpClient.Builder()
        .connectTimeout(25, TimeUnit.SECONDS)
        .readTimeout(90, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private fun auth(request: Request.Builder): Request.Builder {
        val token = settings.getGitHubToken()
        if (token.isNotBlank()) request.header("Authorization", "Bearer $token")
        return request
            .header("Accept", "application/vnd.github+json")
            .header("X-GitHub-Api-Version", "2022-11-28")
            .header("User-Agent", "LLM-Council-Mobile")
    }

    suspend fun listRepos(): List<GitHubRepo> = withContext(Dispatchers.IO) {
        require(settings.getGitHubToken().isNotBlank()) { "GitHub token is not configured" }
        val out = mutableListOf<GitHubRepo>()
        for (page in 1..20) {
            val request = auth(Request.Builder().url("https://api.github.com/user/repos?per_page=100&page=$page&sort=updated&affiliation=owner,collaborator,organization_member")).build()
            val data = JSONArray(execute(request))
            for (i in 0 until data.length()) {
                val o = data.getJSONObject(i)
                out += GitHubRepo(
                    fullName = o.getString("full_name"),
                    defaultBranch = o.optString("default_branch", "main"),
                    privateRepo = o.optBoolean("private", false),
                    updatedAt = o.optString("updated_at", ""),
                    description = o.optString("description", "")
                )
            }
            if (data.length() < 100) break
        }
        out.distinctBy { it.fullName }.sortedBy { it.fullName.lowercase() }
    }

    suspend fun snapshot(repo: GitHubRepo, ref: String = repo.defaultBranch, onProgress: (Int, Int, String) -> Unit = { _,_,_ -> }): RepoSnapshot = withContext(Dispatchers.IO) {
        require(settings.getGitHubToken().isNotBlank()) { "GitHub token is not configured" }
        val safeRepo = repo.fullName.split('/').joinToString("/") { encode(it) }
        val commitReq = auth(Request.Builder().url("https://api.github.com/repos/$safeRepo/commits/${encode(ref)}")).build()
        val commitSha = JSONObject(execute(commitReq)).getString("sha")
        val treeReq = auth(Request.Builder().url("https://api.github.com/repos/$safeRepo/git/trees/$commitSha?recursive=1")).build()
        val treeRoot = JSONObject(execute(treeReq))
        if (treeRoot.optBoolean("truncated", false)) {
            throw IllegalStateException("GitHub returned a truncated recursive tree. Exhaustive audit aborted because 100% repository coverage cannot be proven.")
        }
        val tree = treeRoot.optJSONArray("tree") ?: JSONArray()
        val candidates = mutableListOf<JSONObject>()
        val excluded = mutableListOf<RepoFile>()
        for (i in 0 until tree.length()) {
            val item = tree.optJSONObject(i) ?: continue
            if (item.optString("type") != "blob") continue
            val path = item.optString("path")
            val sha = item.optString("sha")
            val size = item.optLong("size", 0L)
            val reason = exclusionReason(path, size)
            if (reason != null) {
                excluded += RepoFile(path, sha, size, "", classify(path), true, reason)
            } else candidates += item
        }

        val files = mutableListOf<RepoFile>()
        candidates.forEachIndexed { index, item ->
            val path = item.getString("path")
            onProgress(index + 1, candidates.size, path)
            val sha = item.getString("sha")
            val size = item.optLong("size", 0L)
            try {
                val blobReq = auth(Request.Builder().url("https://api.github.com/repos/$safeRepo/git/blobs/$sha")).build()
                val blob = JSONObject(execute(blobReq))
                val encoding = blob.optString("encoding")
                val raw = blob.optString("content").replace("\n", "")
                val bytes = if (encoding == "base64") Base64.decode(raw, Base64.DEFAULT) else raw.toByteArray(StandardCharsets.UTF_8)
                if (bytes.any { it.toInt() == 0 }) {
                    excluded += RepoFile(path, sha, size, "", classify(path), true, "binary content")
                } else {
                    val text = String(bytes, StandardCharsets.UTF_8)
                    files += RepoFile(path, sha, size, text, classify(path))
                }
            } catch (e: Exception) {
                throw IllegalStateException("Failed to ingest required file '$path': ${e.message}. Exhaustive audit aborted rather than silently skipping it.", e)
            }
        }
        RepoSnapshot(repo, ref, commitSha, files, excluded)
    }

    private fun exclusionReason(path: String, size: Long): String? {
        val lower = path.lowercase()
        if (size > 1_000_000L) return "file exceeds 1 MB audit ingestion limit"
        val segments = lower.split('/')
        if (segments.any { it in setOf(".git", "node_modules", "vendor", "dist", "build", ".gradle", ".idea", "coverage", "target", "Pods".lowercase()) }) return "generated/vendor directory"
        val blocked = setOf(".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".7z", ".jar", ".aar", ".apk", ".so", ".dll", ".exe", ".bin", ".mp3", ".mp4", ".mov", ".woff", ".woff2", ".ttf", ".otf", ".lock")
        if (blocked.any(lower::endsWith)) return "binary/generated/non-reviewable file type"
        return null
    }

    private fun classify(path: String): String {
        val p = path.lowercase()
        return when {
            p.endsWith(".md") || p.endsWith(".rst") || p.endsWith(".txt") || p.contains("docs/") -> "documentation"
            p.contains("test") || p.contains("spec") -> "tests"
            p.endsWith(".yml") || p.endsWith(".yaml") || p.endsWith(".json") || p.endsWith(".toml") || p.endsWith(".ini") || p.endsWith(".xml") || p.endsWith(".properties") -> "configuration"
            p.contains("migration") || p.endsWith(".sql") -> "database"
            p.contains(".github/") || p.contains("docker") || p.contains("terraform") || p.endsWith(".tf") -> "ci-infrastructure"
            else -> "source"
        }
    }

    private fun execute(request: Request): String {
        http.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                val message = runCatching { JSONObject(body).optString("message") }.getOrNull().orEmpty().ifBlank { body.take(500) }
                throw IllegalStateException("GitHub HTTP ${response.code}: $message")
            }
            return body
        }
    }

    private fun encode(value: String): String = URLEncoder.encode(value, "UTF-8").replace("+", "%20")
}
