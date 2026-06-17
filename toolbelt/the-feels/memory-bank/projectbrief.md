# Project Brief

## The Feels — Quest 3 Mixed-Reality Walk (native build)

The Feels is a mixed-reality art installation for the **Meta Quest 3S**. The wearer
walks a fixed **~445.8 m** real-world path; the headset's passthrough view is tinted
by whichever logged emotion they are currently "inside." It turns the diary owner's
emotional history into an embodied, walkable timeline.

This memory bank documents the **native Unity build** — the installation piece. It
supersedes the earlier WebXR prototype (`vr.html`), which is now reference-only.

## The two halves of "The Feels"
1. **Diary app** (`index.html`) — the original web DBT diary card: log feelings on a
   wheel, rate intensity, generate PDFs. This is the DATA SOURCE. Still live, unchanged.
2. **MR walk** (`Unity/`) — THIS project. A sideloaded native Quest app that reads that
   same diary data and renders it as a color-tinted passthrough walk.

## Core concept (artist-confirmed)
- One viewer, in the headset, walking a real ~445.8 m outdoor path.
- ~413 logged diary entries become back-to-back color zones along that path; zone
  length ∝ how long that feeling was actually felt.
- The real world is washed/tinted with the current emotion's family color; opacity ∝
  intensity (intensity × 10%).
- Progress is a distance-walked ODOMETER: starts at 0 on launch, accumulates horizontal
  head movement, can begin ANYWHERE. NOT GPS, NOT a fixed start point.
- The "real prize": a Meta Depth-API surface tint that paints the color onto the ACTUAL
  near surfaces you see (strongest up close, fading with distance), instead of a flat
  film. The flat wash is the proven fallback.

## Must-haves for the installation
- **Auto-launch** when the headset powers on (it's an unattended kiosk piece).
- **Zero UI** in the final build — no debug readout, no menus; just the walk.
- **Uninterrupted walking** — the guardian boundary must not stop the wearer.
- **True 1× walking scale** (walk the real 445.8 m), not the dev-time 20× smoke-test scale.

## Who / where
- Artist: Danyela Brown (Bard College, db7613@bard.edu).
- Built on a MacBook Air (Apple Silicon / arm64), Unity closed, headless batch builds.
- Sideloaded to one Quest 3S over adb.
