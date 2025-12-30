# System Patterns & Architecture

## Overall Architecture
```
┌─────────────────┐     WebSocket      ┌─────────────────┐     RTMP        ┌─────────────────┐
│  iPhone Safari  │ ──────────────────►│  Relay Server   │ ──────────────► │  YouTube Live   │
│  (MediaRecorder)│    video/mp4       │  (Node + FFmpeg)│                 │                 │
└─────────────────┘                    └─────────────────┘                 └─────────────────┘
        │                                      │
        │ OAuth                                │
        ▼                                      │
┌─────────────────┐                           │
│  YouTube API    │ ◄─────────────────────────┘
│  (Create stream)│   Gets stream key
└─────────────────┘
```

## Client-Side Flow (index.html)

### Initialization
1. `window.onload` → `init()`
2. Check OAuth callback (URL hash for access_token)
3. Validate token with YouTube API
4. If invalid → redirect to Google OAuth
5. Start camera (video only, no audio)
6. Initialize motion detection
7. Set 3-second timer to auto-start streaming

### Streaming Start
1. `startStreaming()` called after 3s delay
2. Create YouTube broadcast via API
3. Create YouTube stream via API
4. Bind stream to broadcast
5. Register with relay server (`POST /start-stream`)
6. Connect WebSocket to relay
7. Create MediaRecorder with detected mimeType
8. Start recording, send chunks via WebSocket
9. Poll YouTube API for stream status
10. When status = "active" → **ensure broadcast goes live**
11. `waitForBroadcastLive()` monitors broadcast status
12. Auto-transitions to "live" if needed (after 10s)
13. When broadcast = "live" → screen turns GREEN

### Streaming Stop
1. Motion detected (movement > 1.5) while streaming
2. Stop MediaRecorder
3. Close WebSocket
4. Call relay server (`POST /stop-stream`)
5. Transition YouTube broadcast to "complete"
6. Screen turns RED

## Server-Side (relay-server/server.js)

### Endpoints
- `GET /health` - Returns status and active stream count
- `POST /start-stream` - Registers stream key for client
- `POST /stop-stream` - Kills FFmpeg and cleans up

### WebSocket Handling
1. Client connects with `?clientId=xxx`
2. On first message, spawn FFmpeg process
3. Pipe incoming WebSocket data to FFmpeg stdin
4. FFmpeg transcodes to H.264 and sends to YouTube RTMP
5. On disconnect, kill FFmpeg and cleanup

### FFmpeg Command
```bash
ffmpeg -i pipe:0 \
  -c:v libx264 -preset veryfast -tune zerolatency \
  -c:a aac -ar 44100 -b:a 128k \
  -f flv rtmp://a.rtmp.youtube.com/live2/{streamKey}
```

## Key Design Patterns

### Fresh Stream Per Session
- Each `/start-stream` creates new streamInfo object
- Kills any existing FFmpeg for that client
- Prevents stream key mismatch bugs

### Graceful Cleanup
- WebSocket close triggers FFmpeg termination
- Client disconnect removes from activeStreams map
- Prevents zombie FFmpeg processes

### Format Detection
- Client tries multiple mimeTypes: vp9, vp8, webm, mp4
- Safari typically uses mp4 (H.264)
- Server handles transcoding regardless

## Infrastructure

### Relay Server (DigitalOcean)
- Domain: dance.danyelica.fish
- IP: 104.131.178.73
- SSL via Let's Encrypt + Nginx
- Systemd service: dance-relay

### GitHub Pages (Frontend)
- URL: https://danyelajunebrown.github.io/toolbelt/dance-clips/
- Auto-deploys on push to main branch
