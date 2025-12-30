# DanceClips iOS App (Native)

Native iOS app that captures video WITH background music - something impossible in Safari.

**See [DanceClips/README.md](DanceClips/README.md) for full setup instructions.**

## Quick Start

```bash
# Install XcodeGen if you don't have it
brew install xcodegen

# Generate Xcode project
cd DanceClips
xcodegen generate

# Open in Xcode
open DanceClips.xcodeproj
```

Then: connect iPhone → select as target → Run (Cmd+R)

## Why Native?

Safari's WebKit pauses background music when microphone is requested. This is a browser policy we cannot override.

Native iOS apps can configure their own audio session:

```swift
try audioSession.setCategory(
    .playAndRecord,
    options: [.mixWithOthers]  // ← THE KEY
)
```

This is how TikTok and Instagram work.
