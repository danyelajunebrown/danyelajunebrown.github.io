# Progress

## Status (2026-06-12): native MR walk RUNS; depth gradient + kiosk polish open

## Working on real hardware
- [x] Native Unity 6 Quest app builds headless → installs → runs on Quest 3S
- [x] Passthrough MR view
- [x] ~413 diary entries load from Supabase (anon read-only) → segments over 445.8 m
- [x] Odometer advances with real walking; emotion changes by zone, oldest first
- [x] Emotion family colors verified on-device (7 families, 0 fallbacks)
- [x] Opacity = intensity × 0.1
- [x] Flat color wash reliably visible over passthrough
- [x] Depth API subsystem stands up (EnvironmentDepthManager created, HardOcclusion)
- [x] Scene permission (USE_SCENE) granted; OpenXR Occlusion+Session features enabled headless
- [x] Path length derived (haversine ~445.8 m over 14-pt GPX)

## In progress
- [~] Never-blank `_MinTint` floor — edited in shader + FeelsExperience; NOT yet
  built/installed/confirmed

## Open — the depth "real prize"
- [ ] **Meta environment depth produces 0 frames** → depth surface-tint can't compute
  (falls back to flat wash). ROOT CAUSE UNSOLVED. Leading suspicion: broken spatial
  Space data; try rebuilding Space Setup on the headset.
- [ ] Confirm the true near-surface gradient renders once frames flow
- [ ] Tune `tintReachMeters` / `_MaxDist` and `minTint` to taste on the real path

## Open — installation polish (the 3 tracked tasks)
- [ ] **Auto-launch on power-on** (Task #1) — BOOT_COMPLETED receiver, or Quest
  Single-App/Kiosk Mode
- [ ] **Strip debug readout + set metersScale = 1** for the true 445.8 m walk (Task #2)
- [ ] **Disable guardian boundary** for uninterrupted walking (Task #3) — persistent
  in-headset Boundary toggle (debug props don't hold)
- [ ] Rename package id off the default URP template (optional, cosmetic)
- [ ] Clamp per-frame odometer displacement so a tracking glitch can't jump it

## Resolved this stretch
- [x] "No storage for roomscale" = spurious glitch (106 GB free), not real disk
- [x] Black screen when paused = mCurrentFocus null → `am start` relaunch
- [x] Guardian debug flags don't affect depth (tested, ruled out)
- [x] Identified "colors far / translucent near" as the flat-wash perception effect,
      not depth

## Superseded (WebXR prototype, now reference-only)
- [x] `vr.html` A-Frame passthrough walk (172.5 m, GPS-projected) — replaced by the
      native app
- [x] `live.html` / `qr.html` spectator view — not part of the native installation
- [x] `index.html` diary app — STILL LIVE; it's the data source
