# Audio Capture Testing Guide 🎵

## Objective
Find a method to capture audio from iPhone microphone for YouTube livestream **without stopping background music playback** (Spotify, Apple Music, etc.)

---

## Test File Location
**Local**: `file:///Users/danyelabrown/Desktop/danyelajunebrown GITHUB/danyelajunebrown.github.io-main/toolbelt/dance-clips/audio-test-harness.html`

**After deployment**: `https://danyelajunebrown.github.io/toolbelt/dance-clips/audio-test-harness.html`

---

## Testing Setup

### Before You Start:
1. **Start your music app** (Spotify, Apple Music, YouTube Music, etc.)
2. **Play a song** at audible volume
3. **Open Safari** on your iPhone
4. **Navigate to the test harness URL** (push to GitHub first, or use local file)
5. **Connect Safari Dev Tools from Mac** (optional but helpful for debugging)

### Important Notes:
- Test **one method at a time**
- **Stop each test** before starting the next one (use Stop button)
- **Pay attention** to the exact moment music stops (if it stops)
- **Note** any error messages in the logs
- Each test is independent - previous tests don't affect later ones

---

## Tests to Run

### ✅ Test 1A: Simultaneous Video + Audio
**What it tests**: Requesting video and audio together in a single getUserMedia call

**Expected behavior**: 
- Camera opens ✓
- Microphone activates ✓
- Music stops ✗ (likely)

**Why this might work**: Some implementations handle simultaneous requests differently

---

### ✅ Test 1B: Audio with Minimal Processing
**What it tests**: Requesting audio with all processing disabled (no echo cancellation, no auto-gain control, no noise suppression)

**Expected behavior**:
- Camera opens ✓
- Microphone activates ✓
- Music might continue? (hypothesis)

**Why this might work**: Minimal processing might not trigger iOS audio session takeover

---

### ✅ Test 1C: Delayed Audio Request
**What it tests**: Request video first, wait 5 seconds, then request audio separately

**Expected behavior**:
- Camera opens immediately ✓
- Wait 5 seconds ⏳
- Microphone activates ✓
- Music might continue? (hypothesis)

**Why this might work**: Timing/ordering might matter to iOS audio session management

---

### ✅ Test 2A: Display Capture API
**What it tests**: Using getDisplayMedia instead of getUserMedia to capture audio

**Expected behavior**:
- Likely not supported on iOS Safari ✗
- If supported: might preserve music playback

**Why this might work**: Display capture uses different audio session category

---

### ✅ Test 2B: Dual Stream (Video + Display Audio)
**What it tests**: Camera for video + screen capture for audio, merged together

**Expected behavior**:
- Likely not supported on iOS Safari ✗
- Requires getDisplayMedia support

**Why this might work**: Separate capture streams might use different audio categories

---

### ✅ Test 3A: Web Audio API Routing
**What it tests**: Capturing microphone through Web Audio API with custom routing

**Expected behavior**:
- Camera opens ✓
- Audio routing through Web Audio API ✓
- Music might continue? (hypothesis)

**Why this might work**: Web Audio API uses different audio processing pipeline

---

### ✅ Test 4A: Audio with Voice Processing
**What it tests**: Request audio with FULL processing enabled (opposite of Test 1B)

**Expected behavior**:
- Camera opens ✓
- Microphone activates with processing ✓
- Music stops ✗ (likely)

**Why test this**: Establishes baseline - confirms processing doesn't help

---

### ✅ Test 5A: Background Mode Request
**What it tests**: Audio with specific low-latency, stereo configuration

**Expected behavior**:
- Camera opens ✓
- Microphone activates ✓
- Music might continue? (hypothesis)

**Why this might work**: Specific audio configuration might hint background compatibility

---

## How to Report Results

### For EACH test, report:

1. **Test Name**: (e.g., "Test 1A")
2. **Music Status**: Did background music CONTINUE or STOP?
3. **Capture Success**: Did it successfully capture audio? (check logs)
4. **Errors**: Any error messages?
5. **Browser Console**: Copy any relevant console output

### Report Format:
```
Test 1A: Simultaneous Video + Audio
✓ Camera opened
✓ Got 1 audio track
✗ Music STOPPED immediately
Result: FAILED (music stopped)

Test 1B: Minimal Processing
✓ Camera opened
✓ Got 1 audio track
✓ Music CONTINUED playing!
Result: SUCCESS! (music preserved)
```

---

## What We're Looking For

### 🎯 SUCCESS Criteria:
- Background music **continues playing**
- Microphone **successfully captures** audio
- No errors in capture process

### If we find a SUCCESS:
1. Document exact parameters used
2. Test with actual YouTube streaming
3. Integrate into main app
4. Celebrate! 🎉

### If ALL tests FAIL:
We'll explore alternative approaches:
- Server-side audio injection
- Post-processing merge
- Separate audio recording + sync
- Native app wrapper

---

## Troubleshooting

### "Permission denied" errors
- Grant camera/microphone permissions in Safari settings
- Try reloading the page

### "getDisplayMedia not supported"
- Expected on iOS Safari
- Mark test as "N/A - Not Supported"

### Page crashes or freezes
- Stop the test, reload page
- Try next test

### Music stops on ALL tests
- This is expected behavior on iOS
- We'll need to explore server-side solutions

---

## After Testing

### Share Results:
1. **Screenshot** each test's log section
2. **Copy** console output from Safari Dev Tools
3. **Report** which test (if any) kept music playing
4. If NONE worked, we proceed to Plan B (server-side solutions)

### Next Steps Based on Results:

**If 1+ tests succeed**:
→ Integrate winning method into production app
→ Test with actual YouTube livestream
→ Update documentation

**If all tests fail**:
→ Implement server-side audio injection
→ Or: Separate audio recording with post-processing
→ Or: Accept video-only, instructor plays music from separate speaker

---

## Technical Background (Why This is Hard)

iOS uses **Audio Session Categories** that are mutually exclusive:
- **AVAudioSessionCategoryPlayback**: Background music only
- **AVAudioSessionCategoryRecord**: Recording only (stops playback)
- **AVAudioSessionCategoryPlayAndRecord**: Both (requires native app)

Web browsers typically use **Record** mode when `getUserMedia({ audio: true })` is called, which stops playback.

**What we're testing**: Can we trick iOS into using **PlayAndRecord** mode through specific Web API configurations?

Instagram does this with native iOS SDK - we're trying to find the web equivalent.

---

## Good Luck! 🍀

Remember: Even if all tests fail, we have backup plans. The goal is to systematically test every possibility before moving to more complex solutions.
