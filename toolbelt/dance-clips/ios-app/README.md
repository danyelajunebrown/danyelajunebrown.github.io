# DanceClips iOS App (Native)

This folder will contain the native iOS implementation that can capture **system audio** (music from Spotify/Apple Music/etc.) while recording/streaming.

## Phase 0/1 Benchmark (Tonight)
Goal: a minimal SwiftUI app that runs on your iPhone and toggles **full-screen red/green**.

### Prereqs
- macOS + Xcode
- iPhone connected via USB (or WiFi debugging)
- Apple ID signed into Xcode (Xcode Settings → Accounts)

### Create the Xcode project
We’ll generate a **SwiftUI iOS App** project named `DanceClipsNative` into `ios-app/DanceClipsNative`.

### Run on device
1. Open `ios-app/DanceClipsNative/DanceClipsNative.xcodeproj`
2. Select your iPhone as the run target
3. Signing & Capabilities:
   - Team: your Apple ID team
   - Bundle Identifier: something unique like `io.danyelica.danceclips.native`
4. Press Run

### Expected behavior
- App launches
- Screen is solid red
- Tap anywhere → screen turns green
- Tap again → red

### Debugging checklist
- If you get “Developer Mode required”: enable on iPhone (Settings → Privacy & Security → Developer Mode)
- If signing fails: set **Team** and ensure bundle id is unique
- If install fails: trust your computer + keep phone unlocked

## Next benchmark (Phase 2)
Add CoreMotion-based “set down (still) → start” and “picked up → stop”.
