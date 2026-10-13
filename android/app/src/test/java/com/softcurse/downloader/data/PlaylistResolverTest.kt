package com.softcurse.downloader.data

import com.softcurse.downloader.domain.DownloadRequest
import com.softcurse.downloader.domain.MediaFormat
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PlaylistResolverTest {
    @Test
    fun `extracts a YouTube playlist id`() {
        assertEquals(
            "PLjdoAVZSiklxfxkq2tG8l7Djy3SBUP0hf",
            youtubePlaylistId("https://youtube.com/playlist?list=PLjdoAVZSiklxfxkq2tG8l7Djy3SBUP0hf&si=test"),
        )
        assertEquals(null, youtubePlaylistId("https://example.com/?list=PLjdoAVZSiklxfxkq2tG8l7Djy3SBUP0hf"))
    }

    @Test
    fun `parses YouTube playlist feed fallback`() {
        val xml = """
            <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
              <title>Muse</title>
              <entry><yt:videoId>firstId1234</yt:videoId><title>First</title></entry>
              <entry><yt:videoId>secondId567</yt:videoId><title>Second</title></entry>
            </feed>
        """.trimIndent().encodeToByteArray()

        val preview = parseYouTubePlaylistFeed("https://youtube.com/playlist?list=playlist12345", "playlist12345", xml)

        assertEquals("Muse", preview.title)
        assertEquals(2, preview.entries.size)
        assertEquals("https://www.youtube.com/watch?v=firstId1234", preview.entries.first().url)
    }

    @Test
    fun playlistMetadataExpandsIntoIndividualEntries() {
        val preview = parseSourcePreview(
            "https://www.youtube.com/playlist?list=list-1",
            """{"id":"list-1","title":"Mix","playlist_count":2,"entries":[{"id":"a","title":"First","extractor_key":"Youtube"},{"id":"b","title":"Second","webpage_url":"https://example.com/b"}]}""",
        )

        assertTrue(preview.isPlaylist)
        assertEquals("Mix", preview.title)
        assertEquals(2, preview.entries.size)
        assertEquals("https://www.youtube.com/watch?v=a", preview.entries[0].url)
        assertEquals("https://example.com/b", preview.entries[1].url)
        assertFalse(preview.truncated)
    }

    @Test
    fun singleMediaMetadataKeepsOriginalUrlAsFallback() {
        val preview = parseSourcePreview(
            "https://example.com/video",
            """{"id":"video-1","title":"Single"}""",
        )

        assertFalse(preview.isPlaylist)
        assertEquals("https://example.com/video", preview.entries.single().url)
    }

    @Test
    fun playlistEntryIdsAreStableAndFormatSpecific() {
        val mp3 = DownloadRequest(url = "https://example.com", format = MediaFormat.Mp3, quality = "320 kbps")
        val mp4 = mp3.copy(format = MediaFormat.Mp4, quality = "1080p")

        assertEquals(playlistEntryId("playlist", "entry", mp3), playlistEntryId("playlist", "entry", mp3))
        assertTrue(playlistEntryId("playlist", "entry", mp3) != playlistEntryId("playlist", "entry", mp4))
    }
}
