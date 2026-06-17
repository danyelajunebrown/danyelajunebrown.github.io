# Product Context

## Why this exists
The Feels makes someone's emotional history *walkable*. Instead of reading a year of
diary entries, you put on the headset and physically walk through them: each emotion
floods the real world around you with its color, for as long as that feeling actually
lasted. It's an embodied, durational portrait of a person's interior life.

## The artist's intent
- The piece is felt, not operated. The viewer should never see a menu, a dialog, or
  debug text — only the walk and the color.
- The color belongs to the *real world*, not a screen. Passthrough MR (not opaque VR)
  is essential: you are tinting reality, not replacing it. The Depth-API surface tint
  (color on real surfaces) is the truest expression of this; the flat wash is the safe
  fallback.
- The path is real and specific (~445.8 m, a measured outdoor route). Walking the true
  distance matters — the duration of the walk mirrors the duration of the feelings.

## Experience goals
- **Put on headset → it's already running.** Auto-launch on power-on; no laptop, no
  controller, no Quest menu.
- **Start anywhere.** The odometer begins at 0 wherever the wearer is standing; they
  just start walking. No "go to the start point" instruction.
- **Walk freely.** No guardian wall interrupts the path.
- **One color at a time.** The current emotion tints the world until the wearer crosses
  into the next zone.
- **Intensity reads as opacity.** Stronger feelings = more saturated tint.

## Success criteria
- Headset powers on → the piece is running, in passthrough, tinting the world — no
  human setup.
- Emotion color changes as the wearer walks the real path, in the right order (oldest
  feeling first).
- The emotion color is reliably VISIBLE (never blank) — and, when depth is feeding,
  concentrated on nearby real surfaces.
- No UI artifacts, no boundary interruptions, no stored secrets.

## What it is NOT (anymore)
- Not WebXR / A-Frame (`vr.html` was the prototype; this is native).
- Not a spectator/QR experience in the native build (the WebXR `live.html` / `qr.html`
  spectator view is not part of the installation piece).
- Not GPS-driven (Quest has no GPS; position is head-tracking odometry).
