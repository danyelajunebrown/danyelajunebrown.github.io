# I'm In Charge of the Girls

**Also known as:** Keep Me Rolling Juice (Camera Recorder)

## What It Does

A mobile web app that solves a common frustration: recording video on your phone while music keeps playing in the background. Perfect for dancers, content creators, and anyone who wants to record themselves performing with music without the audio cutting out.

## The Problem It Solves

When you open your phone's native camera app, it automatically pauses your music. This project bypasses that limitation by:
- Using the browser's MediaRecorder API instead of the native camera
- Keeping music apps (Spotify, Apple Music, etc.) running in the background
- Capturing both your voice AND the background music through the microphone

## Current Features

### Camera Recording
- Front-facing camera with 720p/1280p recording
- Real-time video preview
- Timer showing recording duration
- Auto-starts camera on page load

### Audio Capture
- Microphone picks up both voice and background music
- Disabled audio processing (echo cancellation, noise suppression, auto gain) to preserve music quality
- Records in WebM format with VP9 video and Opus audio codecs

### User Experience
- Clean, modern UI with gradient styling
- Recording indicator with pulsing animation
- Simple 3-button workflow: Start Camera → Record → Stop & Download
- Automatic file download with timestamp naming (`recording-[timestamp].webm`)

## Technical Details

### Technologies
- Pure HTML5 + CSS3 + Vanilla JavaScript
- MediaStream Recording API
- No external dependencies
- Mobile-first responsive design

### Browser Compatibility
- Works best on iOS Safari and Chrome for Android
- Requires HTTPS for camera/microphone access
- Uses `getUserMedia` for media capture

### Audio Configuration
```javascript
audio: {
    echoCancellation: false,    // Preserves background music
    noiseSuppression: false,     // Keeps full audio spectrum
    autoGainControl: false       // Prevents volume adjustments
}
```

## Future Enhancements (Planned)

### Dance Clip Generation
- AI person tracking to automatically identify individual dancers
- Upload full class livestream videos
- Generate individual reels for each student
- Automatic cropping and framing around detected person

### Advanced Recording Features
- Front/back camera toggle
- Video quality selector (480p, 720p, 1080p)
- Pause/resume recording
- Video filters and effects
- Playback preview before download

### Audio Features
- Volume level visualization
- Audio balance adjustment
- Option to mix in uploaded audio tracks
- Background music library integration

### Export Options
- Multiple format support (MP4, MOV)
- Direct social media sharing
- Cloud storage integration
- Batch download for multiple recordings

## Use Cases

1. **Dance Practice**: Record yourself dancing to Spotify playlists
2. **Lip Sync Videos**: Create TikTok/Instagram content with music
3. **Workout Videos**: Film exercise routines with motivational music
4. **Music Covers**: Record performances with backing tracks
5. **Content Creation**: Any scenario where you need video + background music

## File Structure

```
dance-clips/
├── index.html          # Main app (camera recorder)
└── claude.md          # This documentation
```

## Known Limitations

- Output format is WebM (may need conversion for some platforms)
- File size can be large for long recordings
- Audio quality depends on phone's microphone
- Background music volume depends on phone speaker output
- No built-in video editing capabilities (yet)

## Development Notes

- Keep the audio configuration settings (no echo cancellation, etc.) to maintain music capture quality
- Consider adding a warning about file sizes for long recordings
- Future: Implement chunk-based recording for better memory management
- Future: Add service worker for offline functionality

## Architecture Vision

This tool is designed to evolve from a simple camera recorder into a full dance studio management tool:

1. **Phase 1** (Current): Personal recording with background music
2. **Phase 2**: AI person detection and tracking
3. **Phase 3**: Automated clip generation from livestreams
4. **Phase 4**: Studio dashboard with batch processing

The name "I'm In Charge of the Girls" reflects its ultimate purpose: helping dance instructors manage and distribute individual student clips from group classes.
