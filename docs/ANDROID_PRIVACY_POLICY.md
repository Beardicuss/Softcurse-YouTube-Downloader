# Softcurse Systems Media Downloader privacy notice

Effective: 13 October 2026

Softcurse Systems Media Downloader is designed to process downloads on the user's Android
device. The current application has no account system, advertising, analytics, tracking,
telemetry, or crash-reporting service.

## Information stored on the device

The application stores submitted URLs, download state, history, output references, and user
preferences locally using Android Room and DataStore. Media extraction and audio conversion
run on the device. Uninstalling the application removes its private database and settings,
subject to Android backup behavior, but does not automatically delete files already exported
to `Download/Softcurse`.

## Network activity

When the user starts a transfer, the application connects to the submitted URL and to services
required by that media source. These may include the source website and its media or CDN
providers. Those third parties receive ordinary network information such as the user's IP
address and are governed by their own privacy policies and terms.

The current application does not send download history or analytics to Softcurse Systems.

## Files and Android permissions

Completed media is exported through Android MediaStore. The application does not request broad
storage access.

The application requests only:

- Internet access, to retrieve media selected by the user.
- Notification access on Android 13 and newer, when authorized, to display background progress.
- Foreground-service and foreground-data-sync access, to keep user-started transfers visible
  and reliable while the application is not in front.

It does not request contacts, location, camera, microphone, account, or broad media-library
access.

## User responsibility

Users must download only media they own or are authorized to save. Website terms, copyright
rules, and local law remain applicable. Softcurse Systems does not host the selected media and
cannot grant rights to third-party content.

## Changes

This notice must be reviewed whenever analytics, crash reporting, remote services, account
features, or new permissions are introduced. A public release should publish the current notice
at a stable URL and identify an appropriate support or privacy contact before distribution.
