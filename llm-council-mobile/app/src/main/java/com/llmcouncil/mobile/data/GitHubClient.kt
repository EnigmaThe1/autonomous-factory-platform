package com.llmcouncil.mobile.data

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
import java.util.zip.ZipInputStream

class GitHubClient(private val settings: SecureSettings) {
    private val http = OkHttpClient.Builder()
        .connectTimeout(25, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .followRedirects(true)
        .followSslRedirects(true)
        .build()

    private data class TreeMeta(val path: String, val sha: String, val size: Long, val category: String)

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
            val data = JSONArray(executeText(request))
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

    suspend fun snapshot(
        repo: GitHubRepo,
        ref: String = repo.defaultBranch,
        onProgress: (Int, Int, String) -> Unit = { _, _, _ -> }
    ): RepoSnapshot = withContext(Dispatchers.IO) {
        require(settings.getGitHubToken().isNotBlank()) { "GitHub token is not configured" }
        val safeRepo = repo.fullName.split('/').joinToString("/") { encode(it) }
        val commitReq = auth(Request.Builder().url("https://api.github.com/repos/$safeRepo/commits/${encode(ref)}")).build()
        val commitSha = JSONObject(executeText(commitReq)).getString("sha")

        // The recursive tree is the authoritative audit manifest. If GitHub truncates it,
        // we refuse to call the audit exhaustive.
        val treeReq = auth(Request.Builder().url("https://api.github.com/repos/$safeRepo/git/trees/$commitSha?recursive=1")).build()
        val treeRoot = JSONObject(executeText(treeReq))
        if (treeRoot.optBoolean("truncated", false)) {
            throw IllegalStateException("GitHub returned a truncated recursive tree. Exhaustive audit aborted because 100% repository coverage cannot be proven.")
        }

        val requiredMeta = linkedMapOf<String, TreeMeta>()
        val excluded = mutableListOf<RepoFile>()
        val tree = treeRoot.optJSONArray("tree") ?: JSONArray()
        for (i in 0 until tree.length()) {
            val item = tree.optJSONObject(i) ?: continue
            if (item.optString("type") != "blob") continue
            val path = item.optString("path")
            val sha = item.optString("sha")
            val size = item.optLong("size", 0L)
            val category = classify(path)
            val reason = exclusionReason(path, size)
            if (reason != null) excluded += RepoFile(path, sha, size, "", category, true, reason)
            else requiredMeta[path] = TreeMeta(path, sha, size, category)
        }

        // Fetch contents as one pinned archive instead of one API call per blob. This scales
        // to large repos without burning the GitHub REST rate limit while the tree above still
        // gives us the deterministic coverage denominator and per-file SHAs.
        val found = linkedMapOf<String, RepoFile>()
        val archiveReq = auth(Request.Builder().url("https://api.github.com/repos/$safeRepo/zipball/$commitSha")).build()
        http.newCall(archiveReq).execute().use { response ->
            if (!response.isSuccessful) throw githubError(response.code, response.body?.string().orEmpty())
            val body = response.body ?: throw IllegalStateException("GitHub returned an empty repository archive")
            ZipInputStream(body.byteStream().buffered()).use { zip ->
                var entry = zip.nextEntry
                while (entry != null) {
                    if (!entry.isDirectory) {
                        val rawName = entry.name
                        val path = rawName.substringAfter('/', rawName)
                        val meta = requiredMeta[path]
                        if (meta != null) {
                            onProgress(found.size + 1, requiredMeta.size, path)
                            val bytes = zip.readBytes()
                            if (bytes.size > 1_000_000) {
                                excluded += RepoFile(path, meta.sha, meta.size, "", meta.category, true, "archive entry exceeds 1 MB audit ingestion limit")
                                requiredMeta.remove(path)
                            } else if (bytes.any { it.toInt() == 0 }) {
                                excluded += RepoFile(path, meta.sha, meta.size, "", meta.category, true, "binary content")
                                requiredMeta.remove(path)
                            } else {
                                val text = String(bytes, StandardCharsets.UTF_8)
                                found[path] = RepoFile(path, meta.sha, meta.size, text, meta.category)
                            }
                        }
                    }
                    zip.closeEntry()
                    entry = zip.nextEntry
                }
            }
        }

        val missing = requiredMeta.keys - found.keys
        if (missing.isNotEmpty()) {
            throw IllegalStateException(
                "Pinned repository archive did not contain ${missing.size} required manifest file(s), including ${missing.take(8).joinToString()}. Exhaustive audit aborted rather than silently skipping them."
            )
        }

        val files = requiredMeta.keys.map { path -> found.getValue(path) }
        RepoSnapshot(repo, ref, commitSha, files, excluded.sortedBy { it.path })
    }

    private fun exclusionReason(path: String, size: Long): String? {
        val lower = path.lowercase()
        if (size > 1_000_000L) return "file exceeds 1 MB audit ingestion limit"
        val segments = lower.split('/')
        if (segments.any { it in setOf(".git", "node_modules", "vendor", "dist", "build", ".gradle", ".idea", "coverage", "target", "pods") }) return "generated/vendor directory"
        val blocked = setOf(
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".7z", ".jar", ".aar", ".apk",
            ".so", ".dll", ".exe", ".bin", ".mp3", ".mp4", ".mov", ".woff", ".woff2", ".ttf", ".otf"
        )
        if (blocked.any(lower::endsWith)) return "binary/non-text file type"
        return null
    }

    private fun classify(path: String): String {
        val p = path.lowercase()
        return when {
            p.endsWith(".md") || p.endsWith(".rst") || p.endsWith(".txt") || p.contains("docs/") -> "documentation"
            p.contains("test") || p.contains("spec") -> "tests"
            p.endsWith(".yml") || p.endsWith(".yaml") || p.endsWith(".json") || p.endsWith(".toml") || p.endsWith(".ini") || p.endsWith(".xml") || p.endsWith(".properties") || p.endsWith(".lock") -> "configuration-dependencies"
            p.contains("migration") || p.endsWith(".sql") -> "database"
            p.contains(".github/") || p.contains("docker") || p.contains("terraform") || p.endsWith(".tf") -> "ci-infrastructure"
            else -> "source"
        }
    }

    private fun executeText(request: Request): String {
        http.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()
            if (!response.isSuccessful) throw githubError(response.code, body)
            return body
        }
    }

    private fun githubError(code: Int, body: String): IllegalStateException {
        val message = runCatching { JSONObject(body).optString("message") }.getOrNull().orEmpty().ifBlank { body.take(500) }
        return IllegalStateException("GitHub HTTP $code: $message")
    }

    private fun encode(value: String): String = URLEncoder.encode(value, "UTF-8").replace("+", "%20")
}
