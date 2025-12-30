# Stage 2 Testing - Manual Broadcast Transition

## What Changed
✅ Added `transitionBroadcastToLive()` function  
✅ Function manually forces broadcast to transition to "live"  
✅ Available in console for manual testing  
✅ **NO automatic behavior** - you must call it manually

## Purpose
Test if we CAN manually transition the broadcast to live. If this works, we'll automate it in Stage 3.

---

## Test Procedure

### Step 1: Start a Stream (Same as Before)
1. Open app on iPhone: https://danyelajunebrown.github.io/toolbelt/dance-clips/
2. Connect Safari dev tools from Mac (Safari → Develop → [Your iPhone])
3. Wait 3 seconds for stream to start
4. Screen turns green (stream is active)
5. Console shows broadcast monitoring (from Stage 1)

### Step 2: Check Initial Broadcast Status
In the console, type:
```javascript
await getBroadcastStatus()
```

**Expected output:**
```javascript
{
  lifeCycleStatus: "ready",  // or "testing"
  privacyStatus: "unlisted",
  recordingStatus: "notRecording"  // or "recording"
}
```

### Step 3: Manually Trigger Transition
In the console, type:
```javascript
await transitionBroadcastToLive()
```

**What should happen:**
```
🚀 STAGE 2: Manually transitioning broadcast to LIVE...
Broadcast ID: [some ID]
✅ Transition request successful!
New status: live
🎉 Broadcast is now LIVE!
Video should be playable at: https://youtube.com/watch?v=[broadcastId]
```

**Function returns:** `true` (if successful) or `false` (if failed)

### Step 4: Verify on YouTube
1. Copy the URL from console: `https://youtube.com/watch?v=[broadcastId]`
2. Open in a browser
3. **Does the video play?** ✓ or ✗
4. **Is it showing live?** ✓ or ✗

### Step 5: Check Status Again
```javascript
await getBroadcastStatus()
```

**Expected output:**
```javascript
{
  lifeCycleStatus: "live",  // Should now be "live"
  privacyStatus: "unlisted",
  recordingStatus: "recording"
}
```

---

## Success Criteria

**Stage 2 passes if:**
- ✅ `transitionBroadcastToLive()` returns `true`
- ✅ Console shows "🎉 Broadcast is now LIVE!"
- ✅ `lifeCycleStatus` changes from "ready" to "live"
- ✅ Video actually plays on YouTube
- ✅ No errors in console

**If it fails:**
- ❌ Function returns `false`
- ❌ Console shows error details
- ❌ Video still shows "Upcoming" on YouTube

---

## Troubleshooting

### If transition fails with error:
**Check the error message in console:**

1. **"No active broadcast to transition"**
   - Broadcast ID is null
   - Stream didn't start properly
   - Check: Is screen green?

2. **"Transition failed: [error details]"**
   - YouTube API returned an error
   - Possible reasons:
     - Broadcast not in correct state
     - Permissions issue
     - Stream not active yet

3. **"Transition succeeded but status is: ready"**
   - API call worked but status didn't change
   - YouTube may need more time
   - Try waiting 5 seconds and check status again

### If video won't play:
1. Check broadcast status: `await getBroadcastStatus()`
2. Is `lifeCycleStatus` actually "live"?
3. Try refreshing the YouTube page
4. Check if stream is still active: Stream status should be "active"

---

## Report Back

Please provide:

1. **Did the manual transition work?** (Yes/No)
2. **Console output** from calling `transitionBroadcastToLive()`
3. **Video playability** - Does it actually play on YouTube?
4. **Broadcast status** before and after transition
5. **Any errors** encountered

### Example Report:
```
✅ Manual transition: SUCCESS
✅ Console: "Broadcast is now LIVE!"
✅ Video: Plays immediately on YouTube
✅ Status before: "ready"
✅ Status after: "live"
❌ Errors: None
```

---

## Next Steps

**If Stage 2 succeeds:**
→ Proceed to Stage 3: Automate the transition (no manual console command needed)

**If Stage 2 fails:**
→ Debug the specific error before proceeding
→ May need API permission changes or different approach

---

## Quick Test Commands

Copy/paste these into console while stream is running:

```javascript
// Check current status
await getBroadcastStatus()

// Force transition to live
await transitionBroadcastToLive()

// Monitor for 10 seconds
await monitorBroadcastStatus(10000)

// Check status again
await getBroadcastStatus()
```
