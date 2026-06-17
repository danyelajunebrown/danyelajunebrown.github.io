# Active Context

## Where the project is (2026-06-12)
The native MR walk builds, installs, and runs on the Quest 3S: passthrough works, ~413
segments load over 445.8 m, the odometer advances as you walk, the emotion color tints
the view, Scene permission is granted, and the Depth API subsystem stands up. The flat
color wash is reliably visible.

## In-flight change: never-blank `_MinTint` floor
Just edited (NOT yet built/installed):
- `FeelsDepthTint.shader` — added `_MinTint` property + CBUFFER member; frag now
  `col.a *= max(prox, _MinTint)` so the emotion color is NEVER fully blank (near
  surfaces still rise above the floor when depth feeds).
- `FeelsExperience.cs` — added `public float minTint = 0.6f` (`[Range 0..1]`) and a
  `SetFloat("_MinTint", …)` in BuildVisuals.
- NEXT: headless build → `adb install -r` → relaunch → artist confirms the color is
  reliably visible (and whether any near-surface gradient appears). Per the
  no-fictitious-data rule, do NOT claim it works until her eyes + logcat confirm.

## The core open problem: 0 depth frames
Meta **environment depth produces 0 valid frames** on this headset (MRSS `avail: X/0/Z`),
persistently, even worn and looking at a lit textured surface. So the depth-driven
gradient can't compute and the shader falls back to the flat wash. This is the thing
standing between "flat color film" and the "real prize" (color painted on real surfaces).
- Ruled out: guardian debug flags (cleared, depth still 0); storage (106 GB free — the
  "no storage for roomscale" message is a spurious spatial-service glitch, NOT real
  disk); Scene permission (granted); the OpenXR depth extension (active,
  XR_META_environment_depth v2).
- Leading suspicion: broken/missing spatial Space data tied to the same glitch as "no
  storage for roomscale" — may need rebuilding Space Setup on the headset. Unconfirmed.

## Today's finding: "colors far away, translucent up close"
That's the FLAT WASH (`#else` path), not the depth gradient. A single uniform
translucent film reads stronger over dim/low-detail far regions and washes out over
bright near surfaces — a perception effect, not depth. It confirms the depth gradient is
NOT currently driving the image (consistent with 0 frames).

## Live device issues seen while wearing it
- "Stuck in regular boundary" / "boundary wall is firm" — the roomscale guardian keeps
  confining the walk. Debug props (`debug.oculus.guardian.*`) are non-persistent and
  unreliable; the real fix is the in-headset Boundary toggle (persistent) — Task #3.
- Black screen when paused (mCurrentFocus=null) → fixed by `am start` relaunch.
- Controllers not enumerating / storage glitch → cleared by rebooting the headset.

## Working agreements (how to collaborate on this) — IMPORTANT
- **No fictitious data.** Never claim a thing works until the artist's eyes AND logcat
  confirm it. Don't assume device behavior.
- **Fetch device state directly** via adb — don't ask her to paste logs.
- **Surface key decisions before building.**
- **External tools = copy-paste + click-by-click steps** (she's often in the headset;
  make it effortless).
- **Final build = zero UI** (strip the debug readout for the install).
- **Deliver complete, paste-ready files.**

## Decisions locked
- Native Unity passthrough MR (NOT WebXR). `vr.html` / `live.html` / `qr.html` are
  prototype/reference only; `index.html` (diary) is the live data source.
- Odometer progress, starts at 0 anywhere, true 1× scale for the install.
- Depth surface-tint is the goal; flat wash (now floored by `_MinTint`) is the
  guaranteed-visible fallback.

## Immediate next steps
1. Build + install the `_MinTint` floor; artist confirms reliable visibility.
2. Get her out of / disable the guardian boundary (Task #3, persistent in-headset toggle).
3. Root-cause the 0 depth frames (likely rebuild Space Setup).
4. Auto-launch on power-on (Task #1).
5. Strip debug + set metersScale = 1 for the install (Task #2).
