$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$version = (Get-Content -Raw (Join-Path $projectRoot "VERSION")).Trim()
$executable = Join-Path $projectRoot "dist\Softcurse_Media_Downloader.exe"
if (-not (Test-Path -LiteralPath $executable)) {
    throw "Build the executable first with build_exe.bat"
}

$compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $compiler) {
    $candidatePaths = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 7\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidatePath in $candidatePaths) {
        if (Test-Path -LiteralPath $candidatePath) {
            $compiler = Get-Item -LiteralPath $candidatePath
            break
        }
    }
}
if (-not $compiler) {
    throw "Inno Setup 6 or 7 compiler (ISCC.exe) was not found"
}

$compilerPath = if ($compiler -is [System.Management.Automation.CommandInfo]) {
    $compiler.Source
} else {
    $compiler.FullName
}
& $compilerPath (Join-Path $PSScriptRoot "softcurse_installer.iss")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$installer = Join-Path $PSScriptRoot "Output\Softcurse_Media_Downloader_v${version}_Setup.exe"
if (-not (Test-Path -LiteralPath $installer)) {
    throw "Expected installer was not produced: $installer"
}
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $installer).Hash.ToLower()
$checksumPath = "$installer.sha256"
Set-Content -Encoding ascii -LiteralPath $checksumPath "$hash *$(Split-Path -Leaf $installer)"
Write-Host "Built $installer"
Write-Host "Checksum $checksumPath"
