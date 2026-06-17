# Tech Context

## Engine / toolchain
- **Unity 6 LTS 6000.0.76f1**. Binary:
  `/Applications/Unity/Hub/Editor/6000.0.76f1/Unity.app/Contents/MacOS/Unity`
- URP 17.0.4, IL2CPP, ARM64. Build target: Android (Quest).
- Meta XR SDK (`com.meta.xr.sdk.core`) + `com.unity.xr.meta-openxr`. Depth via the
  `Meta.XR.EnvironmentDepth` namespace (`EnvironmentDepthManager`).
- **adb**:
  `/Applications/Unity/Hub/Editor/6000.0.76f1/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb`

## Project location (MIND THE SPACE)
`/Users/danyelabrown/Desktop/danyelajunebrown GITHUB/danyelajunebrown.github.io-main/toolbelt/the-feels/Unity`
— "danyelajunebrown GITHUB" has a space; ALWAYS quote the path.

## Build & deploy (all headless, Unity CLOSED)
- **Build APK:** `Unity -batchmode -quit -projectPath "<PROJ>" -buildTarget Android
  -executeMethod FeelsBuild.Android -logFile <log>` → `~/Desktop/TheFeels.apk`
- **Enable Depth (one-time / idempotent):** `Unity -batchmode -quit -projectPath
  "<PROJ>" -executeMethod FeelsDepthSetup.Enable -logFile <log>` (enables the OpenXR
  Occlusion + Session features for Android; exits 0 on success).
- **Install:** `adb -s 340YC10G8R0ZLP install -r ~/Desktop/TheFeels.apk`
- **Launch:** `adb -s 340YC10G8R0ZLP shell am start -n
  com.UnityTechnologies.com.unity.template.urpblank/com.unity3d.player.UnityPlayerGameActivity`
- **KEY INSIGHT:** because builds are headless with the Editor CLOSED, scene / asset /
  manifest / `.cs` / `.shader` files can be safely HAND-EDITED directly while Unity is
  closed — no GUI round-trip needed.

## Device
- Quest 3S, serial **340YC10G8R0ZLP**.
- Package **com.UnityTechnologies.com.unity.template.urpblank**, activity
  **com.unity3d.player.UnityPlayerGameActivity** (default URP-template ids, not yet
  renamed).
- App pauses off-head (proximity sensor); a paused app can be KILLED by the OS (saw
  APP_CMD_LOW_MEMORY) — must be on-head to run/measure.

## On-device verification
- Heartbeat tags `[FeelsXP]` / `[TheFeels]`. Pull with:
  `adb -s 340YC10G8R0ZLP logcat -d -v time | grep -i feels`. System spam rolls the ring
  buffer fast — heartbeats (every ~2 s) may already be gone; relaunch or dump promptly.
- Depth frame telemetry: MRSS `FramesetTelemetry` (system log) — line
  `stereo/depth/color: avail: X/Y/Z`; the middle number Y = depth frames. **Y=0 =
  environment depth producing nothing** (the current blocker).

## Backend (Supabase) — unchanged from the web app
- Project `bczevwhzlammcjomuqrg`, table `diary_entries`.
- Kiosk user_id `ee04c688-d857-45f8-849c-2f072053cf28`.
- Anon key is EMBEDDED in `FeelsDataLoader.cs`: PUBLIC by design, RLS read-only (anon
  SELECT only, scoped to that user_id). SAFE to commit. No other secrets in code.

## Path data
- 14-point GPX polyline (recorded 2026-06-09), haversine length **~445.8 m**
  (straight-line endpoints ~375 m, elevation net ~0). Replace `FeelsPath.Pts` to
  re-measure; the length recomputes automatically.

## Constraints / do-not-touch
- Do NOT edit Meta SDK code: `Library/PackageCache/...`, `OVRProjectSetupXRTasks.cs`,
  `OVRBuild.cs`.
- Quest has no GPS — position is head-tracking odometry only.
- A sideloaded app can't make itself the only app from code; true kiosk = Quest OS
  Single-App/Kiosk Mode or a BOOT_COMPLETED receiver.
- Never commit unless explicitly asked. The working tree has unrelated uncommitted
  portfolio changes — stage specific files only, NEVER `git add -A`.
