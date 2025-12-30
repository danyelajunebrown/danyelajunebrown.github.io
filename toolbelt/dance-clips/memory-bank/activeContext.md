# Active Context

## Current Focus
✅ **SOLVED!** YouTube livestream broadcasts now automatically transition to "live" and are immediately playable.

## Recent Changes (Dec 10, 2025)

### Broadcast Transition Fix - COMPLETE ✅
**Problem:** Videos showing as "Upcoming" despite stream being active
**Solution:** Automatic broadcast transition with intelligent fallback

**Implementation:**
- `waitForBroadcastLive()` - Monitors broadcast status and auto-transitions
- Waits 10 seconds for YouTube's auto-transition
- Falls back to manual `transitionBroadcastToLive()` if needed
- Green screen only shows when broadcast is truly "live"

**Testing:** User needs to test and confirm videos are playable

## Previous Changes (Dec 9, 2025)

### Bug Fixed: Stream Key Mismatch
- **Problem**: Old FFmpeg process was running with old stream key
- **Symptom**: YouTube API showed stream status "inactive" with "noData"
- **Cause**: Relay server reused existing FFmpeg instead of creating new one
- **Fix**: `/start-stream` now kills existing FFmpeg and creates fresh streamInfo
- **Deployed**: Yes, relay server updated

### UI Simplified
- Removed all buttons, text, and visible elements
- Full-screen red = not streaming
- Full-screen green = streaming
- Auto-starts 3 seconds after page load

### Motion Detection Changed
- Motion only used for STOPPING stream (detecting phone pickup)
- Stream starts automatically on timer, not motion
- Avoids iOS permission requirement for starting

### Stream Status Polling Added
- Client polls YouTube API every 2s for stream status
- Waits for status "active" before turning green
- 30 second timeout, turns green anyway after timeout
- Detailed console logging for debugging

## What Works
- OAuth flow and token validation
- Camera capture (video only)
- YouTube broadcast/stream creation
- Relay server receives video
- FFmpeg transcodes and sends to YouTube RTMP

## Current Issue Being Tested
After fixing the stream key mismatch bug, need to verify:
1. New stream gets new FFmpeg with correct stream key
2. YouTube receives video data
3. Stream status transitions to "active"
4. Screen turns green promptly

## Next Steps
1. User tests the fix
2. Verify stream appears on YouTube
3. If working, clean up console logging
4. Consider motion detection for stopping

## Active Decisions

### Why 3-second auto-start?
- iOS DeviceMotionEvent.requestPermission() needs user tap
- Can't reliably detect "phone set down" without motion permission
- Timer-based start avoids permission requirement
- Motion still used for stopping (prompted when phone picked up)

### Why poll for stream status?
- Can't trust that video is actually reaching YouTube
- Previous streams stuck as "Upcoming" because no data received
- Polling confirms YouTube is receiving video before showing green

## Debugging Commands
```bash
# Check relay server logs
sshpass -p 'Jeh8lesmotsdepassEs' ssh -o StrictHostKeyChecking=no root@104.131.178.73 "journalctl -u dance-relay --no-pager -n 50"

# Check running FFmpeg processes
sshpass -p 'Jeh8lesmotsdepassEs' ssh -o StrictHostKeyChecking=no root@104.131.178.73 "ps aux | grep ffmpeg"

# Restart relay server
sshpass -p 'Jeh8lesmotsdepassEs' ssh -o StrictHostKeyChecking=no root@104.131.178.73 "systemctl restart dance-relay"

# Check relay health
curl https://dance.danyelica.fish/health
```
