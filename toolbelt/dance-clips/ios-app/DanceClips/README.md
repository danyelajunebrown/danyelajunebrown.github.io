# DanceClips iOS App

Native iOS app that captures video WITH background music - something impossible in Safari.

## The Magic: AVAudioSession

```swift
try audioSession.setCategory(
    .playAndRecord,
    mode: .videoRecording,
    options: [.mixWithOthers, .defaultToSpeaker, .allowBluetooth]
)
```

This is how TikTok and Instagram do it. The `.mixWithOthers` option is the key - it tells iOS NOT to pause other audio when we start recording.

## Setup

### Option A: Using XcodeGen (recommended)

1. Install XcodeGen:
   ```bash
   brew install xcodegen
   ```

2. Generate the Xcode project:
   ```bash
   cd ios-app/DanceClips
   xcodegen generate
   ```

3. Open the generated project:
   ```bash
   open DanceClips.xcodeproj
   ```

### Option B: Create manually in Xcode

1. Open Xcode → File → New → Project
2. Choose "App" (iOS)
3. Settings:
   - Product Name: `DanceClips`
   - Interface: `SwiftUI`
   - Language: `Swift`
4. Save to `ios-app/DanceClips`
5. Delete the auto-generated files
6. Drag in all the `.swift` files from `DanceClips/` folder
7. Copy Info.plist contents to your project's Info

## Running on Device

1. Connect your iPhone via USB
2. Select your iPhone as the run target
3. Signing & Capabilities:
   - Team: Your Apple ID
   - Bundle ID: `io.danyelica.danceclips` (or your own)
4. Add capabilities:
   - Background Modes → Audio
5. Press Run (Cmd+R)

## Testing Audio

1. Launch the app
2. Start playing music in Spotify/Apple Music
3. **Music should keep playing!** (unlike Safari)
4. Set phone down → wait 3 seconds → streaming starts
5. Pick phone up → streaming stops

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DanceClipsApp                         │
│                         │                                │
│                    ContentView                           │
│                    (Red/Green)                           │
│                         │                                │
│         ┌───────────────┼───────────────┐               │
│         │               │               │               │
│   AudioManager    StreamManager   MotionManager         │
│   (AVAudioSession) (Camera+WS)   (Accelerometer)        │
│         │               │               │               │
│   ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐        │
│   │.mixWith   │   │AVCapture  │   │CoreMotion │        │
│   │Others     │   │Session    │   │           │        │
│   │           │   │    │      │   │           │        │
│   │Spotify    │   │WebSocket  │   │isStill?   │        │
│   │keeps      │   │to Relay   │   │           │        │
│   │playing!   │   │           │   │           │        │
│   └───────────┘   └───────────┘   └───────────┘        │
└─────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `DanceClipsApp.swift` | App entry point, configures audio session |
| `ContentView.swift` | Main UI - full screen red/green |
| `AudioManager.swift` | AVAudioSession with `.mixWithOthers` |
| `StreamManager.swift` | Camera capture + WebSocket to relay |
| `MotionManager.swift` | Detects phone set down / picked up |
| `Info.plist` | Permissions for camera, mic, motion |

## TODO

- [ ] Add YouTube OAuth (currently needs manual stream key)
- [ ] Implement proper H.264 encoding with VideoToolbox
- [ ] Add audio encoding (AAC)
- [ ] Test with actual YouTube stream

## Why This Works

Safari (WebKit) uses a shared audio session that automatically pauses other apps when microphone is requested. This is a WebKit policy, not a hardware limitation.

Native iOS apps can configure their OWN audio session with different rules. By using `.playAndRecord` category with `.mixWithOthers` option, we tell iOS:
- Yes, we want to record audio
- No, don't pause other audio sources
- Let everything mix together

The microphone then picks up:
1. Your voice/room audio
2. Music playing through the speakers

This is exactly how TikTok duets work.
