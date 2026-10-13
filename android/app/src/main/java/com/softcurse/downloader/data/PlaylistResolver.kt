package com.softcurse.downloader.data

import android.content.Context
import com.softcurse.downloader.domain.PlaylistEntry
import com.softcurse.downloader.domain.SourcePreview
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import java.net.URI
import java.net.HttpURLConnection
import java.net.URL
import javax.xml.parsers.DocumentBuilderFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.w3c.dom.Element

class PlaylistResolver(private val context: Context) {
    suspend fun inspect(url: String): SourcePreview = withContext(Dispatchers.IO) {
        val playlistId = youtubePlaylistId(url)
        if (playlistId != null) {
            return@withContext inspectYouTubeFeed(url, playlistId)
        }
        YtDlpRuntime.ensureCurrent(context)
        val request = YoutubeDLRequest(url)
            .addOption("--flat-playlist")
            .addOption("--dump-single-json")
            .addOption("--playlist-end", MAX_PLAYLIST_ENTRIES.toString())
            .addOption("--no-warnings")
        val response = YoutubeDL.execute(request)
        if (response.exitCode == 0) {
            return@withContext parseSourcePreview(url, response.out)
        }
        error(response.err.takeIf(String::isNotBlank) ?: "Could not inspect this media link")
    }

    companion object {
        const val MAX_PLAYLIST_ENTRIES = 100
    }
}

private fun inspectYouTubeFeed(sourceUrl: String, playlistId: String): SourcePreview {
    val connection = URL("https://www.youtube.com/feeds/videos.xml?playlist_id=$playlistId")
        .openConnection() as HttpURLConnection
    connection.connectTimeout = 15_000
    connection.readTimeout = 15_000
    connection.setRequestProperty("User-Agent", "Softcurse-Media-Downloader/1.0")
    connection.instanceFollowRedirects = true
    return try {
        check(connection.responseCode in 200..299) {
            "YouTube playlist metadata returned HTTP ${connection.responseCode}"
        }
        connection.inputStream.use { stream ->
            parseYouTubePlaylistFeed(sourceUrl, playlistId, stream.readBytes())
        }
    } finally {
        connection.disconnect()
    }
}

internal fun youtubePlaylistId(sourceUrl: String): String? = runCatching {
    val uri = URI(sourceUrl)
    if (!uri.host.orEmpty().lowercase().let { it == "youtube.com" || it.endsWith(".youtube.com") }) {
        return@runCatching null
    }
    uri.rawQuery.orEmpty().split('&')
        .mapNotNull { part -> part.split('=', limit = 2).takeIf { it.size == 2 } }
        .firstOrNull { it[0] == "list" }
        ?.get(1)
        ?.takeIf { it.matches(Regex("[A-Za-z0-9_-]{10,}")) }
}.getOrNull()

internal fun parseYouTubePlaylistFeed(
    sourceUrl: String,
    playlistId: String,
    xml: ByteArray,
): SourcePreview {
    val factory = DocumentBuilderFactory.newInstance().apply {
        isNamespaceAware = true
        runCatching { setFeature("http://apache.org/xml/features/disallow-doctype-decl", true) }
        runCatching { setFeature("http://xml.org/sax/features/external-general-entities", false) }
        runCatching { setFeature("http://xml.org/sax/features/external-parameter-entities", false) }
        isExpandEntityReferences = false
    }
    val builder = factory.newDocumentBuilder().apply {
        setEntityResolver { _, _ -> org.xml.sax.InputSource("".reader()) }
    }
    val document = builder.parse(xml.inputStream())
    val feed = document.documentElement
    val playlistTitle = feed.childElements("title").firstOrNull()?.textContent?.trim()
        .takeUnless(String?::isNullOrBlank) ?: "YouTube playlist"
    val entries = feed.childElements("entry").mapIndexedNotNull { index, entry ->
        val mediaId = entry.childElements("videoId").firstOrNull()?.textContent?.trim()
            .takeUnless(String?::isNullOrBlank) ?: return@mapIndexedNotNull null
        val title = entry.childElements("title").firstOrNull()?.textContent?.trim()
            .takeUnless(String?::isNullOrBlank) ?: "Playlist item ${index + 1}"
        PlaylistEntry(
            mediaId = mediaId,
            title = title,
            url = "https://www.youtube.com/watch?v=$mediaId",
            index = index + 1,
        )
    }.take(PlaylistResolver.MAX_PLAYLIST_ENTRIES)
    require(entries.isNotEmpty()) { "No downloadable entries were found in this YouTube playlist" }
    return SourcePreview(
        sourceUrl = sourceUrl,
        playlistId = playlistId,
        title = playlistTitle,
        entries = entries,
        truncated = entries.size >= PlaylistResolver.MAX_PLAYLIST_ENTRIES,
    )
}

private fun Element.childElements(localName: String): List<Element> = buildList {
    val children = childNodes
    for (index in 0 until children.length) {
        val child = children.item(index)
        if (child is Element && (child.localName ?: child.tagName.substringAfter(':')) == localName) add(child)
    }
}

internal fun parseSourcePreview(sourceUrl: String, rawOutput: String): SourcePreview {
    val jsonStart = rawOutput.indexOf('{')
    require(jsonStart >= 0) { "The media service returned no metadata" }
    val root = JSONObject(rawOutput.substring(jsonStart))
    val playlistId = root.optString("id").takeIf(String::isNotBlank)
    val playlistTitle = root.optString("title").takeIf(String::isNotBlank) ?: "Untitled media"
    val rawEntries = root.optJSONArray("entries")
    if (rawEntries == null) {
        return SourcePreview(
            sourceUrl = sourceUrl,
            playlistId = null,
            title = playlistTitle,
            entries = listOf(
                PlaylistEntry(
                    mediaId = playlistId ?: sourceUrl,
                    title = playlistTitle,
                    url = root.optString("webpage_url").takeIf(::isHttpUrl) ?: sourceUrl,
                    index = 1,
                ),
            ),
        )
    }

    val entries = buildList {
        for (position in 0 until rawEntries.length()) {
            val entry = rawEntries.optJSONObject(position) ?: continue
            val mediaId = entry.optString("id").takeIf(String::isNotBlank) ?: continue
            val entryUrl = entry.optString("webpage_url").takeIf(::isHttpUrl)
                ?: entry.optString("url").takeIf(::isHttpUrl)
                ?: youtubeUrl(entry.optString("extractor_key"), mediaId)
                ?: continue
            add(
                PlaylistEntry(
                    mediaId = mediaId,
                    title = entry.optString("title").takeIf(String::isNotBlank) ?: "Playlist item ${position + 1}",
                    url = entryUrl,
                    index = position + 1,
                ),
            )
        }
    }
    require(entries.isNotEmpty()) { "No downloadable entries were found in this playlist" }
    val reportedCount = root.optInt("playlist_count", entries.size)
    return SourcePreview(
        sourceUrl = sourceUrl,
        playlistId = playlistId ?: sourceUrl,
        title = playlistTitle,
        entries = entries,
        truncated = reportedCount > entries.size || entries.size >= PlaylistResolver.MAX_PLAYLIST_ENTRIES,
    )
}

private fun isHttpUrl(value: String): Boolean = runCatching {
    URI(value).scheme in setOf("http", "https")
}.getOrDefault(false)

private fun youtubeUrl(extractorKey: String, mediaId: String): String? =
    if (extractorKey.contains("youtube", ignoreCase = true)) {
        "https://www.youtube.com/watch?v=$mediaId"
    } else {
        null
    }
