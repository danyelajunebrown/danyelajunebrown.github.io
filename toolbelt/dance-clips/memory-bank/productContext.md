# Product Context

## Problem Statement
Dance instructors need to record their sessions for students to review. Current solutions have problems:
1. Native camera app stops music playback
2. Manual start/stop is inconvenient during class
3. Setting up livestreams is too complex

## Solution
A "set it and forget it" web app:
1. Instructor starts music on phone
2. Opens the dance-clips URL
3. Sets phone down facing the dance floor
4. Stream automatically starts after 3 seconds
5. When class is over, picking up phone stops stream
6. Video is automatically saved as unlisted YouTube video

## User Experience Flow
1. **Before class**: Start music (Spotify/Apple Music)
2. **Open app**: Navigate to https://danyelajunebrown.github.io/toolbelt/dance-clips/
3. **Screen is RED**: Not yet streaming
4. **Set phone down**: Wait 3 seconds...
5. **Screen turns GREEN**: Now streaming to YouTube
6. **During class**: Music plays, video streams, instructor dances
7. **After class**: Pick up phone
8. **Screen turns RED**: Stream ended, video saved

## Why These Design Decisions

### No Microphone
- Requesting microphone permission causes iOS to pause background music
- Video-only stream preserves music playback
- Dance classes don't need voice capture anyway

### Motion Detection
- Allows hands-free operation
- Natural gesture (setting down = start, picking up = stop)
- iOS limitation: requires one tap on first visit to grant motion permission

### YouTube Live (not just recording)
- Automatic cloud backup
- Can share link before class starts
- Students can watch live if desired
- No local storage concerns

### Minimal UI (Red/Green only)
- Visible from across the room
- No buttons to accidentally tap
- Clear status indication
