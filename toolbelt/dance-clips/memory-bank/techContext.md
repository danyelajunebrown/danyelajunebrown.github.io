# Technical Context

## Technologies

### Frontend
- **HTML5** - Single page app in index.html
- **Vanilla JavaScript** - No frameworks
- **MediaRecorder API** - Captures camera video
- **WebSocket** - Sends video to relay
- **YouTube Data API v3** - Creates broadcasts/streams

### Backend (Relay Server)
- **Node.js** - Runtime
- **Express** - HTTP server
- **ws** - WebSocket library
- **FFmpeg** - Video transcoding to RTMP

### Infrastructure
- **GitHub Pages** - Hosts frontend
- **DigitalOcean Droplet** - Hosts relay server
- **Nginx** - Reverse proxy with SSL
- **Let's Encrypt** - SSL certificates
- **systemd** - Service management

## Dependencies

### Frontend (none - vanilla JS)

### Backend (package.json)
```json
{
  "dependencies": {
    "express": "^4.18.2",
    "ws": "^8.16.0",
    "cors": "^2.8.5"
  }
}
```

## Environment Setup

### Local Development
```bash
cd relay-server
npm install
npm start  # Runs on port 3001
```

### Server Deployment
```bash
# SSH into server
ssh root@104.131.178.73

# Service commands
systemctl status dance-relay
systemctl restart dance-relay
journalctl -u dance-relay -f  # View logs

# Files location
/root/dance-clips-relay/server.js
/root/dance-clips-relay/package.json
```

## API Configuration

### Google Cloud Console
- Project with YouTube Data API v3 enabled
- OAuth 2.0 Client (Web application type)
- Authorized redirect URI: https://danyelajunebrown.github.io/toolbelt/dance-clips/
- OAuth consent screen configured with youtube scope
- User added as test user (app in testing mode)

### YouTube API Endpoints Used
- `GET /youtube/v3/channels` - Validate token
- `POST /youtube/v3/liveBroadcasts` - Create broadcast
- `POST /youtube/v3/liveStreams` - Create stream
- `POST /youtube/v3/liveBroadcasts/bind` - Bind stream to broadcast
- `GET /youtube/v3/liveStreams?part=status` - Poll stream status
- `POST /youtube/v3/liveBroadcasts/transition` - End broadcast

## Known Constraints

### iOS Safari
- DeviceMotionEvent.requestPermission() requires user gesture
- Cannot detect external audio playback (Spotify, etc.)
- Microphone request pauses background music
- Supported MediaRecorder mimeTypes: video/mp4

### YouTube Live
- Stream key changes each time a new stream is created
- Takes ~10-30 seconds for stream to become "active"
- enableAutoStart: true auto-transitions to live when video received
- Broadcasts stuck as "Upcoming" if video never received

### Browser Permissions
- Camera: persistent once granted
- Motion: requires tap each session on iOS
