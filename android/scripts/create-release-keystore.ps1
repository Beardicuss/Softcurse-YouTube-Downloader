[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$androidDirectory = Split-Path -Parent $PSScriptRoot
$keystoreDirectory = Join-Path $androidDirectory "keystores"
$keystorePath = Join-Path $keystoreDirectory "softcurse-release.jks"
$propertiesPath = Join-Path $androidDirectory "keystore.properties"
$keyAlias = "softcurse-release"
$keytoolPath = if ($env:JAVA_HOME) {
    Join-Path $env:JAVA_HOME "bin\keytool.exe"
} else {
    $keytoolCommand = Get-Command keytool.exe -ErrorAction SilentlyContinue
    if ($keytoolCommand) { $keytoolCommand.Source } else { $null }
}

if (-not $keytoolPath -or -not (Test-Path -LiteralPath $keytoolPath)) {
    throw "keytool.exe was not found. Set JAVA_HOME to a JDK installation and run this script again."
}

New-Item -ItemType Directory -Path $keystoreDirectory -Force | Out-Null

if (Test-Path -LiteralPath $keystorePath) {
    throw "A release keystore already exists at $keystorePath. It was not overwritten."
}

Write-Host "Creating the permanent Softcurse Android release key."
Write-Host "Use a strong password and save it in your password manager."
Write-Host "At the key-password prompt, press Enter to reuse the keystore password."
Write-Host ""

& $keytoolPath -genkeypair -v `
    -keystore $keystorePath `
    -alias $keyAlias `
    -keyalg RSA `
    -keysize 4096 `
    -validity 10000

if ($LASTEXITCODE -ne 0) {
    throw "keytool did not create the release key."
}

Write-Host ""
Write-Host "Enter the same password again so Gradle can sign release builds locally."
$storePasswordSecure = Read-Host "Keystore password" -AsSecureString
$keyPasswordSecure = Read-Host "Key password (press Enter if it is the same)" -AsSecureString

function ConvertFrom-PrivateSecureString([Security.SecureString]$Value) {
    return [System.Net.NetworkCredential]::new("", $Value).Password
}

$storePassword = ConvertFrom-PrivateSecureString $storePasswordSecure
$keyPassword = ConvertFrom-PrivateSecureString $keyPasswordSecure
if ([string]::IsNullOrWhiteSpace($storePassword)) {
    throw "The keystore password cannot be empty."
}
if ([string]::IsNullOrWhiteSpace($keyPassword)) {
    $keyPassword = $storePassword
}

$properties = @(
    "storeFile=keystores/softcurse-release.jks"
    "storePassword=$storePassword"
    "keyAlias=$keyAlias"
    "keyPassword=$keyPassword"
)
[System.IO.File]::WriteAllLines($propertiesPath, $properties, [System.Text.UTF8Encoding]::new($false))

$storePassword = $null
$keyPassword = $null
$storePasswordSecure.Dispose()
$keyPasswordSecure.Dispose()

Write-Host ""
Write-Host "Release signing is configured. Keep both the .jks file and password backed up securely."
Write-Host "You can close this terminal and tell Codex: done."
