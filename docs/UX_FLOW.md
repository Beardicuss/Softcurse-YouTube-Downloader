# Windows interaction flow

## Primary states

```text
Download tab
  -> enter/paste URL
  -> fetch preview
  -> choose format and options
  -> start download OR add one/many URLs to queue
      -> queue processes each waiting item sequentially
      -> failed item is recorded and queue advances
      -> cancellation stops the active item and pauses queue advancement
  -> start download
      -> downloading -> converting -> complete
      -> downloading -> cancelling -> cancelled
      -> downloading -> categorized error -> correct input/dependency/network -> retry
  -> history -> retry/reveal/play
  -> player -> open downloaded media
  -> settings -> save -> return to download
```

On first launch, the readiness flow reports required and optional components. Missing
required components direct source users to install development dependencies and
packaged users to repair or reinstall the application. It never installs software
silently.

No secondary tab is a dead end: Escape returns to Download. While a download is
running, Escape consistently requests cancellation instead.

## Keyboard map

| Input | Action |
|---|---|
| `Ctrl+L` | Open Download and focus/select the URL |
| `Ctrl+D` | Start the configured download |
| `Ctrl+1` | Open Download |
| `Ctrl+2` | Open Player |
| `Ctrl+3` | Open History |
| `Ctrl+4` | Open Settings |
| `Escape` | Cancel active download, otherwise return to Download |
| `Tab` / `Shift+Tab` | Move through actionable controls |
| `Enter` / `Space` | Activate the focused control |

Multi-line clipboard content is interpreted as a URL batch and added to the queue.
Queue items expose waiting, running, complete, failed, and cancelled states.

## Accessibility behavior

- Action buttons expose a high-contrast keyboard focus ring.
- Reduced motion stops title glitches, button pulsing, and animated CRT scanlines.
- Errors use a stable category plus a suggested next action instead of relying only
  on raw downloader output.
- Cancellation and partial playlist completion are visually distinct from failure and
  complete success.
- The interface remains scrollable when vertical space is constrained.
- Navigation typography, title size, preview wrapping, and history columns adapt to
  narrower supported window sizes.
