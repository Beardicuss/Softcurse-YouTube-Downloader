package com.softcurse.downloader.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

class SupportClient {
    suspend fun send(
        type: String,
        subject: String,
        message: String,
        replyEmail: String,
        diagnostics: String,
    ) = withContext(Dispatchers.IO) {
        val fields = linkedMapOf(
            "type" to type,
            "_subject" to subject,
            "message" to message,
            "email" to replyEmail,
            "diagnostics" to diagnostics,
            "app" to "Softcurse Systems Media Downloader",
        )
        val body = fields.entries.joinToString("&") { (key, value) ->
            "${key.urlEncoded()}=${value.urlEncoded()}"
        }
        val connection = (URL(ENDPOINT).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 15_000
            readTimeout = 15_000
            doOutput = true
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        }
        try {
            connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            if (connection.responseCode !in 200..299) {
                throw SupportSubmissionException("Support service returned ${connection.responseCode}")
            }
        } finally {
            connection.disconnect()
        }
    }

    private fun String.urlEncoded(): String = URLEncoder.encode(this, Charsets.UTF_8.name())

    companion object {
        const val ENDPOINT = "https://formspree.io/f/xwlvrwqk"
    }
}

class SupportSubmissionException(message: String) : Exception(message)
