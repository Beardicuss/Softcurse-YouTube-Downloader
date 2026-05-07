# Windows Icon Sizing — Why Your Icon Looks Blurry or Small (and How to Fix It)

## The actual problem

The issue is not your ICO file's dimensions — it's that your ICO is missing the
smaller embedded sizes. Windows does not scale down from 256×256. It requests an
exact pixel match at each display context, and if that size isn't present in the
ICO, it falls back to scaling. Windows' scaling at small sizes is poor: you get
blurry results, or the icon renders smaller than native system icons because
Windows couldn't fill the slot cleanly.

---

## What sizes Windows actually requests

### Standard DPI (96 DPI / 100% scaling)

| Context | Sizes requested |
|---------|----------------|
| Desktop icons | 32×32, 48×48 |
| Taskbar | 16×16, 24×24, 32×32 |
| File Explorer (details view) | 16×16 |
| File Explorer (small icons) | 32×32 |
| File Explorer (medium icons) | 48×48 |
| File Explorer (large icons) | 96×96 |
| File Explorer (extra large) | 256×256 |
| Inno Setup installer | 16×16, 32×32, 48×48 |
| Alt+Tab switcher | 32×32 |
| Start menu (modern) | 48×48 |

### High DPI / scaled displays (common on 1440p and 4K)

| Scaling | Additional sizes requested |
|---------|--------------------------|
| 125% | 20×20, 40×40, 60×60 |
| 150% | 24×24, 48×48, 96×96 |
| 200% | 32×32, 64×64, 128×128 |

This is why `96×96` and `128×128` matter on modern hardware even though they
are not part of the original Windows icon spec — without them, icons on 4K
displays scale from the nearest available size and look soft.

---

## The correct size set

Include all of these in your ICO:

```
16×16    — taskbar, details view, legacy contexts
24×24    — taskbar at 150% DPI
32×32    — desktop, taskbar, alt+tab
48×48    — file explorer medium, start menu
64×64    — file explorer at 125% scaling
96×96    — file explorer large, 150% DPI
128×128  — 200% DPI (4K displays)
256×256  — file explorer extra large (must be PNG-compressed — see below)
```

---

## Critical: the 256×256 frame must be PNG-compressed

Since Windows Vista, the 256×256 frame inside an ICO is stored as a compressed
PNG, not a raw bitmap. This is called the "Vista ICO format." If your converter
outputs a raw 256×256 bitmap, the ICO will be ~200 KB larger than necessary and
may fail to render in some contexts.

Verify this with a hex editor or inspection tool — the 256×256 frame should
start with the PNG magic bytes `89 50 4E 47` (not a BMP header).

Most modern converters (ImageMagick 7+, IcoFX, Greenfish Icon Editor) handle
this correctly by default. Older tools and some online converters do not.

---

## Color depth requirements

Each frame in the ICO should have a 32-bit RGBA version. For maximum
compatibility with Windows XP-era installers and legacy system contexts, also
include an 8-bit (256-color with transparency mask) version of the smaller sizes
(16×16 and 32×32). Most professional icon editors handle this automatically.

If you are only targeting Windows 7+, 32-bit RGBA only is fine.

---

## How to verify your ICO contains the right sizes

### On Windows — Resource Hacker (free)

Open your `.ico` or `.exe` in Resource Hacker. Expand the `Icon` or
`RT_ICON` tree. You will see each embedded frame listed with its dimensions
and color depth. Confirm all required sizes are present.

Download: https://www.angusj.com/resourcehacker/

### On macOS / Linux — ImageMagick

```bash
identify your_icon.ico
```

Output lists every frame:
```
your_icon.ico[0] ICO 256x256 256x256+0+0 32-bit sRGB
your_icon.ico[1] ICO 128x128 128x128+0+0 32-bit sRGB
your_icon.ico[2] ICO 96x96 96x96+0+0 32-bit sRGB
your_icon.ico[3] ICO 64x64 64x64+0+0 32-bit sRGB
your_icon.ico[4] ICO 48x48 48x48+0+0 32-bit sRGB
your_icon.ico[5] ICO 32x32 32x32+0+0 32-bit sRGB
your_icon.ico[6] ICO 24x24 24x24+0+0 32-bit sRGB
your_icon.ico[7] ICO 16x16 16x16+0+0 32-bit sRGB
```

### On Linux — icotool (icoutils package)

```bash
icotool --list your_icon.ico
```

---

## Generating the ICO correctly

### ImageMagick (cross-platform, recommended for automation)

```bash
# Start from a high-resolution PNG (512×512 or larger)
magick your_icon_512.png \
  -define icon:auto-resize=256,128,96,64,48,32,24,16 \
  your_icon.ico
```

For maximum compatibility, resize each frame explicitly so you control the
resampling filter:

```bash
magick your_icon_512.png \
  \( -clone 0 -resize 256x256 \) \
  \( -clone 0 -resize 128x128 \) \
  \( -clone 0 -resize 96x96 \) \
  \( -clone 0 -resize 64x64 \) \
  \( -clone 0 -resize 48x48 \) \
  \( -clone 0 -resize 32x32 \) \
  \( -clone 0 -resize 24x24 \) \
  \( -clone 0 -resize 16x16 \) \
  -delete 0 \
  -filter Lanczos \
  your_icon.ico
```

Use Lanczos for downsampling — it preserves edge sharpness better than the
default at small sizes.

---

## Embedding the ICO in your build tool

The ICO must be embedded in two places independently:

1. **In the `.exe` itself** — so File Explorer, the taskbar, and Alt+Tab show
   the right icon when the exe runs
2. **Referenced by Inno Setup** — so the installer shortcut and the installer
   window use the full multi-size ICO

If you only do one, the other will fall back — usually to a single-size resource
that looks fine at one display context and blurry at others.

### PyInstaller

```bash
pyinstaller --icon=assets/your_icon.ico your_script.py
```

Or in your `.spec` file:

```python
exe = EXE(
    pyz,
    a.scripts,
    icon='assets/your_icon.ico',
    ...
)
```

### Electron / electron-builder

In `package.json`:

```json
{
  "build": {
    "win": {
      "icon": "assets/your_icon.ico"
    }
  }
}
```

### Visual Studio (C#, VB.NET)

Project → Properties → Application → Icon → browse to your `.ico`

Or in `.csproj` directly:

```xml
<PropertyGroup>
  <ApplicationIcon>assets\your_icon.ico</ApplicationIcon>
</PropertyGroup>
```

### .NET SDK (modern csproj)

```xml
<PropertyGroup>
  <ApplicationIcon>assets\your_icon.ico</ApplicationIcon>
</PropertyGroup>
```

### Go (using goversioninfo or rsrc)

```bash
go install github.com/josephspurrier/goversioninfo/cmd/goversioninfo@latest
goversioninfo -icon=your_icon.ico -o resource.syso
```

Then build normally — the `.syso` file is automatically linked.

### Rust (using winres)

In `build.rs`:

```rust
fn main() {
    let mut res = winres::WindowsResource::new();
    res.set_icon("assets/your_icon.ico");
    res.compile().unwrap();
}
```

---

## Inno Setup configuration

```iss
[Setup]
SetupIconFile=assets\your_icon.ico

[Files]
Source: "assets\your_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\YourApp"; \
  Filename: "{app}\yourapp.exe"; \
  IconFilename: "{app}\yourapp.ico"
```

Key points:
- `SetupIconFile` controls the installer window icon (what the user sees during install)
- `IconFilename` in `[Icons]` controls the Start Menu / Desktop shortcut icon
- Both should point to your full multi-size ICO, not the exe
- Copy the ICO to `{app}` in `[Files]` so it exists at the path `{app}\yourapp.ico`
  references

---

## Most common failure mode

The most frequent cause of this problem in automated pipelines: the build
script generates the ICO from a single PNG at the end of the build, overwriting
the carefully prepared multi-size ICO from earlier in the pipeline.

Check your build script for any step that outputs a `.ico` file. If you see
something like:

```bash
convert icon.png icon.ico   # ← this produces a single-frame ICO
```

Replace it with the multi-frame ImageMagick command above.

---

## Quick diagnostic checklist

```
[ ] ICO contains all 8 sizes: 16, 24, 32, 48, 64, 96, 128, 256
[ ] 256×256 frame is PNG-compressed (not raw BMP)
[ ] Frames are 32-bit RGBA (add 8-bit for XP/legacy compat if needed)
[ ] ICO is embedded in the .exe via build tool flag
[ ] ICO is copied to {app} in Inno Setup [Files]
[ ] Inno Setup [Setup] SetupIconFile points to the ICO
[ ] Inno Setup [Icons] IconFilename points to the ICO (not just the exe)
[ ] Build pipeline does not regenerate the ICO from a single PNG at the end
[ ] Verified with Resource Hacker or `identify` that all sizes are present
```
