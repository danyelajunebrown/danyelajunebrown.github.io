# Active Context

## Current Task
Building the Meta Quest 3 VR/AR kiosk (`vr.html`) — a passthrough-AR walk
through every logged feeling.

## Status: BUILT — awaiting real-world test on the headset

## What was built
- `vr.html`: A-Frame 1.6.0 passthrough-AR experience
  - Every `diary_entries` row laid back-to-back along a ~172.5m path
  - Block length ∝ feeling duration (next timestamp − this one; last → now)
  - Wearer walks physically; headset SLAM tracking drives progress along the
    captured start→end line. No auto-movement.
  - Passthrough view floods with the current emotion's color; opacity ∝ intensity
  - Emotion name floats ahead, repositions per zone
  - Single-tap start, no other UI
  - Live refresh every 60s
  - Broadcasts path progress over Supabase Realtime for spectators
- `live.html`: spectator companion view — subscribes to the broadcast, floods a
  phone screen with the wearer's current emotion + a dot on the full path
- `qr.html`: scannable QR pointing onlookers to `live.html`
- `index.html`: added a Change Password action to the header

## Auth / security resolution
- Kiosk reads via a read-only RLS policy ("Kiosk anon read-only"), NO password
  in the file
- An earlier commit (23d4364) leaked a password into public git history; it has
  been rotated to a new private value and the old one is dead, so no history
  scrub was required
- New account password is held only by the user (password manager), not in code

## Decisions made with the user
- Movement: wearer-controlled physical walking (not auto-glide)
- Path length: 172.5m, the real haversine distance between the two given coords
  (the user's "150ft" was off; the coordinates were trusted)
- Visual: whole-world color flood per emotion, held until the next block
- View: passthrough + translucent color tint (safe for walking outdoors)
- Data: anonymous read-only, no login dialogue

## Next Steps
1. User runs the experience on a real Quest 3 along the physical path
2. Report back: does SLAM tracking hold over ~172m? does color track position?
3. Verify Supabase Realtime broadcast reaches `live.html` (untested live)
4. Likely tuning: color-wash opacity curve (washes out over bright passthrough)
5. Optional: add a real change-password UX beyond the prompt()-based one
6. Optional: investigate Quest OS-level kiosk lockdown ("only app on headset")

## Open risks
- Quest 3 SLAM tracking is room-scale rated; ~172m outdoor walk is unverified
- Color wash reads weaker over bright daylight passthrough (compositing contrast)
- "Only thing on the headset" is an OS setting, not achievable from the page
