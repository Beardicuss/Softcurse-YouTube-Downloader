; ─────────────────────────────────────────────────────────────────────────────
; Softcurse // YouTube Downloader v4 — Inno Setup Installer Script
; Requires: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
;
; HOW TO BUILD:
;   1. Install Inno Setup 6 from https://jrsoftware.org/isdl.php
;   2. Place your built Softcurse_YT_Downloader.exe in the dist\ folder
;      (run build_exe.bat first with PyInstaller)
;   3. Open this file in Inno Setup IDE and click Compile (Ctrl+F9)
;   4. Output: installer\Output\Softcurse_YT_Downloader_Setup.exe
; ─────────────────────────────────────────────────────────────────────────────

#define AppName      "Softcurse YT Downloader"
#define AppVersion   "4.0"
#define AppPublisher "Softcurse"
#define AppURL       "https://softcurse.dev"
#define AppExeName   "Softcurse_YT_Downloader.exe"
#define AppIcon      "..\assets\yt.ico"

[Setup]
; Basic identity
AppId={{A7F3C2B1-9E4D-4F2A-8C6E-1D5B3E7A9F02}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=Softcurse_YT_Downloader_v4_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#AppExeName}
; Custom wizard colours (dark/neon theme)
WizardSizePercent=120

; Minimum Windows version: Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "Create a &desktop shortcut";    GroupDescription: "Shortcuts:"; Flags: unchecked
Name: "startmenuicon";   Description: "Create a &Start Menu shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "startupicon";     Description: "Launch on &Windows startup";    GroupDescription: "Options:";   Flags: unchecked

[Files]
; Main executable (built with PyInstaller)
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Bundled ffmpeg (optional — include if present)
Source: "..\ffmpeg\ffmpeg.exe";  DestDir: "{app}\ffmpeg"; Flags: ignoreversion skipifsourcedoesntexist

; README
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

; Icon
Source: "..\assets\yt.ico"; DestDir: "{app}"; DestName: "yt.ico"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu
Name: "{group}\{#AppName}";             Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\yt.ico"
Name: "{group}\Uninstall {#AppName}";   Filename: "{uninstallexe}"

; Desktop shortcut (optional task)
Name: "{autodesktop}\{#AppName}";       Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\yt.ico"; Tasks: desktopicon

; Startup entry (optional task)
Name: "{userstartup}\{#AppName}";       Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up config on uninstall (optional)
; Type: files; Name: "{userappdata}\.softcurse_config.json"
; Type: files; Name: "{userappdata}\.softcurse_history.json"

[Code]
// ── Custom wizard page: show feature checklist ────────────────────────────
var
  FeaturePage: TWizardPage;

procedure InitializeWizard;
var
  Lbl: TLabel;
  Memo: TMemo;
begin
  FeaturePage := CreateCustomPage(wpWelcome, 'Softcurse YT Downloader v4',
    'What''s included in this release:');

  Lbl := TLabel.Create(FeaturePage);
  Lbl.Parent  := FeaturePage.Surface;
  Lbl.Caption :=
    '  ♪  MP3 / ◆ FLAC / ◇ WAV / ▶ MP4 download' + #13#10 +
    '  🛡  SponsorBlock — auto-skip sponsors & intros' + #13#10 +
    '  🏷  Metadata Editor — set artist, album, genre, year' + #13#10 +
    '  ♪  Built-in Mini Player with waveform visualizer' + #13#10 +
    '  🖼  Thumbnail preview before download' + #13#10 +
    '  ✂  Clip / trim any video by timestamp' + #13#10 +
    '  📋  Download history with retry' + #13#10 +
    '  🔔  System tray + desktop notifications' + #13#10 +
    '  📁  Filename template editor' + #13#10 +
    '  📺  CRT scanline visual effect' + #13#10;
  Lbl.Left    := 12;
  Lbl.Top     := 8;
  Lbl.Width   := FeaturePage.SurfaceWidth - 24;
  Lbl.Height  := 200;
  Lbl.Font.Name := 'Courier New';
  Lbl.Font.Size := 9;
  Lbl.Font.Color := $00FFFF;  // Cyan
  Lbl.WordWrap := True;

  Memo := TMemo.Create(FeaturePage);
  Memo.Parent   := FeaturePage.Surface;
  Memo.ReadOnly := True;
  Memo.Left     := 12;
  Memo.Top      := 210;
  Memo.Width    := FeaturePage.SurfaceWidth - 24;
  Memo.Height   := 60;
  Memo.ScrollBars := ssVertical;
  Memo.Font.Name  := 'Courier New';
  Memo.Font.Size  := 8;
  Memo.Text :=
    'REQUIREMENTS:' + #13#10 +
    '  ffmpeg — bundled with installer if available' + #13#10 +
    '  Internet connection — for YouTube downloads' + #13#10#13#10 +
    'Optional (installable from app Settings tab):' + #13#10 +
    '  Pillow — thumbnail previews' + #13#10 +
    '  mutagen — metadata tag writing' + #13#10 +
    '  pygame — mini player audio' + #13#10 +
    '  pystray + plyer — system tray & notifications';
end;

// ── Check Windows 10+ ─────────────────────────────────────────────────────
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWin64 then
  begin
    MsgBox('Softcurse YT Downloader requires a 64-bit version of Windows 10 or later.',
      mbError, MB_OK);
    Result := False;
  end;
end;
