# Dance Clips - Project Brief

## Project Overview
A mobile web app that enables YouTube livestreaming from an iPhone with automatic start/stop based on phone motion. Designed for dance instructors to record sessions hands-free.

## Core Requirements
1. **YouTube Livestream** - Stream video from phone camera directly to YouTube Live
2. **Motion-based control** - Auto-start stream when phone is set down (still), auto-stop when picked up
3. **Music preservation** - Background music (Spotify, Apple Music) must keep playing
4. **Minimal UI** - Red screen = not streaming, Green screen = streaming. Nothing else.
5. **No manual interaction** - Everything auto-initializes on page load

## Technical Constraints
- Browser-based (iOS Safari)
- Cannot use microphone (stops background music)
- iOS requires user gesture for DeviceMotionEvent permission
- Browsers cannot send RTMP directly - requires relay server

## Architecture
```
iPhone Safari → WebSocket → Relay Server (DigitalOcean) → FFmpeg → YouTube RTMP
```

## Key Credentials
- **Relay Server**: dance.danyelica.fish (104.131.178.73)
- **Server Password**: Jeh8lesmotsdepassEs
- **Google OAuth Client ID**: 129984821928-u6iqasj284ffcmkh15on4gsnbbah7pvo.apps.googleusercontent.com

## Success Criteria
- Page loads, screen is red
- After 3 seconds, streaming starts, screen turns green
- YouTube receives video and shows "Live"
- Picking up phone stops stream, screen turns red
