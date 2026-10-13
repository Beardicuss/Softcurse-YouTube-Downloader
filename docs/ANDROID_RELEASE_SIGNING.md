# Android release signing

The release key is the permanent identity of the Android application. Losing it can prevent future updates from being accepted, so keep encrypted offline backups of both the keystore and its passwords.

## Create the local key

From the repository root in PowerShell:

```powershell
$env:JAVA_HOME = "D:\Android\jdk-21"
.\android\scripts\create-release-keystore.ps1
```

The script creates these local, Git-ignored files:

- `android/keystores/softcurse-release.jks`
- `android/keystore.properties`

Never commit either file. Store an encrypted backup separately from the development computer.

## Build signed artifacts

```powershell
Set-Location android
$env:JAVA_HOME = "D:\Android\jdk-21"
.\gradlew.bat testReleaseUnitTest lintRelease assembleRelease bundleRelease
```

The signed APK and Play Store bundle are written below `android/app/build/outputs/apk/release/` and `android/app/build/outputs/bundle/release/`.

CI can use the equivalent `SOFTCURSE_KEYSTORE_FILE`, `SOFTCURSE_KEYSTORE_PASSWORD`, `SOFTCURSE_KEY_ALIAS`, and `SOFTCURSE_KEY_PASSWORD` environment variables instead of a properties file.
