# 🎵 Audio Testing - Quick Start

## What You Need to Do

1. **Open Safari on your iPhone**
2. **Go to**: https://danyelajunebrown.github.io/toolbelt/dance-clips/audio-test-harness.html
3. **Start your music** (Spotify, Apple Music, etc.)
4. **Run each test** (click the buttons one by one)
5. **Report back** which tests (if any) kept music playing

---

## The Test URL
```
https://danyelajunebrown.github.io/toolbelt/dance-clips/audio-test-harness.html
```

**Note**: GitHub Pages takes 1-2 minutes to deploy after pushing. If you see 404, wait a moment and refresh.

---

## Testing Process (Simple Version)

### For EACH test:

1. **Make sure music is playing** 🎵
2. **Click the test button** 
3. **Notice**: Did music STOP or CONTINUE? 
4. **Click "Stop" button** before next test
5. **Move to next test**

### What to Report:

Simply tell me for each test:
- **Test 1A**: Music stopped ✗ / Music continued ✓
- **Test 1B**: Music stopped ✗ / Music continued ✓
- **Test 1C**: Music stopped ✗ / Music continued ✓
- **Test 2A**: Not supported / Music stopped ✗ / Music continued ✓
- **Test 2B**: Not supported / Music stopped ✗ / Music continued ✓
- **Test 3A**: Music stopped ✗ / Music continued ✓
- **Test 4A**: Music stopped ✗ / Music continued ✓
- **Test 5A**: Music stopped ✗ / Music continued ✓

---

## What We're Looking For

**SUCCESS** = Music keeps playing while capturing audio  
**FAILED** = Music stops when test requests microphone

If even ONE test succeeds, we've found the solution! 🎉

---

## Expected Result (Realistic Expectation)

**Most likely outcome**: All tests will stop music (iOS limitation)

**If that happens**: We have backup plans ready:
- Server-side audio mixing
- Separate audio recording + merge
- Alternative workflow (music from separate speaker)

---

## Full Documentation

- **Test Harness**: `audio-test-harness.html`
- **Full Guide**: `AUDIO-TESTING-GUIDE.md`
- **Results Template**: `AUDIO-TEST-RESULTS.md`

---

## Questions?

Just start testing! The test page has built-in instructions.

**Remember**: Stop each test before starting the next one.
