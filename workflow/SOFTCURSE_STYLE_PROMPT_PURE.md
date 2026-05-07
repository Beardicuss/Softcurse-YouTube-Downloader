# ◆ SOFTCURSE SYSTEMS — STYLE PROMPT
### *High-Tech Neon / Cyberpunk Design System*

---

## ◆ IDENTITY & AESTHETIC DIRECTION

> **Codename:** `SOFTCURSE/SYS`
> **Tone:** Retro-Futuristic · Cyberpunk · Tactical Intelligence · Ghost-in-the-Machine
> **Soul:** A bleeding-edge ops terminal born inside a neon-drenched underground server room. Every pixel feels *live*, every surface feels like it's processing classified data in real time. Cold, precise, dangerous — but beautiful.

This is not a UI. This is an **interface artifact** from a world where the grid is alive and silence is a vulnerability. Every element breathes, glitches, pulses. The system is always watching. Always running.

---

## ◆ COLOR PALETTE

| Role | Name | Hex | Usage |
|---|---|---|---|
| **Primary Accent** | Cyan / Aqua | `#00ffff` / `#00ffc8` | Borders, highlights, primary glow, active states |
| **Secondary Accent** | Neon Blue | `#0088ff` | Network indicators, secondary badges, links |
| **Warning / Active** | Electric Orange | `#ff6b35` | CTAs, live data, danger signals, pulse animation |
| **Glitch / Alert** | Magenta | `#ff00ff` | Error states, glitch FX, critical alerts, flicker |
| **Deep Background** | Void Black | `#020202` | Base canvas — absolute dark |
| **Panel Surface** | Abyss Glass | `rgba(5, 8, 16, 0.85)` | Cards, modals, overlays |
| **Grid Overlay** | Ghost Cyan | `rgba(0, 255, 255, 0.03)` | Background grid lines (40px × 40px) |
| **Text Primary** | Ice White | `#e8f4f8` | Body copy, readable text |
| **Text Muted** | Dim Aqua | `rgba(0, 255, 255, 0.45)` | Labels, metadata, secondary copy |
| **Text Data** | Cyan Live | `#00ffcc` | Live values, stats, terminal output |
| **Radial Glow** | Deep Teal Bloom | `rgba(0, 255, 200, 0.04)` | Ambient glow behind focal content |
| **Scanline** | Ghost White | `rgba(255, 255, 255, 0.015)` | CRT scanline overlay pattern |

### Palette Rules
- **NEVER** use white (`#fff`) or grey (`#999`) for borders — always `rgba(0,255,255,N)` variants
- Borders are always **cyan-family**, glows are **cyan or orange**, alerts are **magenta**
- Background is absolute dark — no gradients on the base canvas itself
- All translucency values must be intentional: `0.03` (ghost), `0.12` (subtle), `0.25` (visible), `0.4` (hover), `0.6` (active)

---

## ◆ TYPOGRAPHY

### Font Stack

```css
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');
```

| Role | Font | Style | Usage |
|---|---|---|---|
| **Display / Hero** | `Bebas Neue` | UPPERCASE, wide tracking, cyan glow | Page titles, section headers, hero text |
| **Monospace / Data** | `Space Mono` | Regular / Bold | Stats, labels, tags, code, timestamps, coordinates, IDs |
| **Body / UI Copy** | `DM Sans` | Light / Regular / Medium | Descriptions, paragraphs, UI copy, tooltips |

### Typography Scale

```css
--font-display: 'Bebas Neue', sans-serif;
--font-mono: 'Space Mono', monospace;
--font-body: 'DM Sans', sans-serif;

/* Display Sizes */
--text-hero:    clamp(64px, 10vw, 128px);
--text-h1:      clamp(40px, 6vw, 72px);
--text-h2:      clamp(28px, 4vw, 48px);
--text-h3:      clamp(20px, 3vw, 32px);

/* Mono / Data Sizes */
--text-data-xl: 48px;
--text-data-lg: 32px;
--text-data-md: 18px;
--text-data-sm: 13px;
--text-label:   11px;

/* Body Sizes */
--text-body:    15px;
--text-small:   13px;
--text-micro:   11px;
```

### Typography Rules
- **Display text:** Always `UPPERCASE`, `letter-spacing: 0.08em`, cyan text-shadow glow
- **All labels:** UPPERCASE, `letter-spacing: 2–3px`, `opacity: 0.45`, `Space Mono`
- **Live values / data:** Oversized `Space Mono`, colored by type (see Data Color Coding)
- **Body text:** `DM Sans`, `line-height: 1.7`, `color: rgba(232, 244, 248, 0.82)`
- **Never** mix display font into body copy — strict role separation

### Data Color Coding

```
Cyan    (#00ffcc)  →  Default / General data
Orange  (#ff6b35)  →  Active / Warning / CTA values
Magenta (#ff00ff)  →  Error / Glitch / Critical
Blue    (#0088ff)  →  Network / Connectivity / Remote
```

---

## ◆ BACKGROUND & ATMOSPHERE

### Base Canvas

```css
body {
  background-color: #020202;
  background-image:
    linear-gradient(rgba(0,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,255,255,0.03) 1px, transparent 1px),
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(255,255,255,0.015) 2px,
      rgba(255,255,255,0.015) 4px
    );
  background-size: 40px 40px, 40px 40px, 100% 4px;
}
```

### Atmospheric Layers (stack order)
1. `#020202` — base void
2. Cyan grid `0.03` — structural skeleton
3. Scanline overlay `0.015` — CRT texture
4. Radial glow blooms behind focal content — `rgba(0,255,200,0.04)`
5. Panel surfaces on top — glassmorphism

### Ambient Glow Bloom
```css
.glow-bloom {
  background: radial-gradient(ellipse 60% 40% at 50% 50%,
    rgba(0, 255, 200, 0.06),
    rgba(0, 136, 255, 0.03),
    transparent 70%
  );
  pointer-events: none;
  position: absolute;
  inset: -20%;
  z-index: 0;
}
```

---

## ◆ ANIMATIONS & EFFECTS

```css
/* Cyan pulse glow */
@keyframes pulse-cyan {
  0%, 100% { box-shadow: 0 0 8px rgba(0,255,255,0.3); }
  50%       { box-shadow: 0 0 24px rgba(0,255,255,0.7), 0 0 60px rgba(0,255,255,0.2); }
}

/* Orange pulse glow */
@keyframes pulse-orange {
  0%, 100% { box-shadow: 0 0 8px rgba(255,107,53,0.4); }
  50%       { box-shadow: 0 0 24px rgba(255,107,53,0.8), 0 0 60px rgba(255,107,53,0.25); }
}

/* Glitch text flicker */
@keyframes glitch {
  0%, 100% {
    text-shadow: 2px 0 #ff00ff, -2px 0 #00ffff;
    clip-path: inset(0 0 100% 0);
  }
  10% { clip-path: inset(10% 0 60% 0); transform: skew(-1deg); }
  20% { clip-path: inset(40% 0 20% 0); transform: skew(0.5deg); text-shadow: -2px 0 #ff00ff, 2px 0 #00ffff; }
  30% { clip-path: inset(0 0 100% 0); }
  90% { clip-path: inset(70% 0 5% 0); transform: skew(-0.5deg); }
}

/* Data scan line sweep */
@keyframes scan {
  0%   { transform: translateY(-100%); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 1; }
  100% { transform: translateY(100vh); opacity: 0; }
}

/* Blink cursor */
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

/* Border trace (draw border clockwise) */
@keyframes border-trace {
  0%   { clip-path: inset(0 100% 100% 0); }
  25%  { clip-path: inset(0 0 100% 0); }
  50%  { clip-path: inset(0 0 0 0); }
  100% { clip-path: inset(0 0 0 0); }
}

/* Flicker — for "live" indicators */
@keyframes flicker {
  0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% { opacity: 1; }
  20%, 24%, 55%                           { opacity: 0.3; }
}
```

---

## ◆ DECORATIVE ELEMENTS

### ◆ Decorator Mark
All section titles prefixed with `◆` rotated 45° — the signature mark of this system.

```css
.decorator {
  display: inline-block;
  color: rgba(0,255,255,0.6);
  transform: rotate(45deg) scale(0.75);
  margin-right: 6px;
}
```

### Dividers / Separators

```css
.divider {
  height: 1px;
  background: linear-gradient(90deg,
    transparent,
    rgba(0,255,255,0.3) 20%,
    rgba(0,255,255,0.5) 50%,
    rgba(0,255,255,0.3) 80%,
    transparent
  );
  margin: 24px 0;
  position: relative;
}

.divider::before {
  content: '◆';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  color: rgba(0,255,255,0.5);
  font-size: 8px;
  background: #020202;
  padding: 0 6px;
}
```

---

## ◆ CSS CUSTOM PROPERTIES

```css
:root {
  /* === COLORS === */
  --c-bg:            #020202;
  --c-surface:       rgba(5, 8, 16, 0.85);
  --c-cyan:          #00ffff;
  --c-cyan-soft:     #00ffc8;
  --c-cyan-dim:      rgba(0, 255, 255, 0.45);
  --c-blue:          #0088ff;
  --c-orange:        #ff6b35;
  --c-magenta:       #ff00ff;
  --c-text:          #e8f4f8;
  --c-text-muted:    rgba(232, 244, 248, 0.55);
  --c-border:        rgba(0, 255, 255, 0.12);
  --c-border-hover:  rgba(0, 255, 255, 0.40);
  --c-border-active: rgba(0, 255, 255, 0.70);
  --c-glow-cyan:     rgba(0, 255, 200, 0.04);
  --c-grid:          rgba(0, 255, 255, 0.03);

  /* === TYPOGRAPHY === */
  --font-display: 'Bebas Neue', sans-serif;
  --font-mono:    'Space Mono', monospace;
  --font-body:    'DM Sans', sans-serif;

  /* === SPACING === */
  --space-xs:  4px;
  --space-sm:  8px;
  --space-md:  16px;
  --space-lg:  24px;
  --space-xl:  40px;
  --space-2xl: 64px;
  --space-3xl: 96px;

  /* === EFFECTS === */
  --blur-glass:   blur(20px) saturate(180%);
  --glow-cyan:    0 0 12px rgba(0,255,255,0.3), 0 0 40px rgba(0,255,255,0.08);
  --glow-orange:  0 0 12px rgba(255,107,53,0.4), 0 0 40px rgba(255,107,53,0.1);
  --glow-magenta: 0 0 12px rgba(255,0,255,0.4),  0 0 40px rgba(255,0,255,0.1);
  --transition:   all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  --grid-size:    40px;
}
```

---

## ◆ THE PHILOSOPHY

> *"Precision is the only aesthetic. The grid never lies. Cyan is the color of truth in the dark."*

- Every interface is a **tactical instrument**, not a brochure
- **Data is beautiful** — never hidden, never soft
- **Glass and light** reveal depth, not decoration
- The machine is always **partially alive** — something always moves, blinks, pulses
- **Silence is styled** — negative space is charged with potential, not emptiness

Every pixel is **intentional**. Every glow is **earned**.

---

*— SOFTCURSE/SYS · STYLE ENGINE v2.0 —*
