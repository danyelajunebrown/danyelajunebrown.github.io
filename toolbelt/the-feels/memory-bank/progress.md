# Progress

## Project Status
- [x] Basic DBT Skills Tracker functionality complete
- [x] Feelings wheel interaction working
- [x] User authentication with Supabase
- [x] Diary card generation with drag-and-drop
- [x] PDF generation - fixed
- [x] Change-password action in app header
- [x] VR/AR kiosk (`vr.html`) built
- [x] Live spectator view (`live.html` + `qr.html`) built
- [ ] VR kiosk verified on a real Meta Quest 3 / real path
- [ ] Spectator broadcast verified end-to-end (headset -> live.html)

## VR/AR Kiosk - BUILT

### Done
- [x] A-Frame 1.6.0 passthrough-AR scene
- [x] Pull every `diary_entries` row, oldest → newest
- [x] Duration model: block length ∝ (next timestamp − this timestamp);
      most recent entry extends to "now"
- [x] Path scaled to 172.5m (haversine distance of the two real coordinates)
- [x] Wearer-controlled movement via headset SLAM tracking; progress projected
      onto the captured start→end direction (no GPS, no auto-glide)
- [x] Per-emotion color flood of the passthrough view; opacity ∝ intensity (1-5)
- [x] Floating emotion name, repositioned on each zone change
- [x] Single-tap kiosk start, no other UI
- [x] Live refresh every 60s
- [x] Colors sourced from `emotionWheelData`; 3 free-text feelings aliased

### Auth / security
- [x] Removed embedded password; kiosk uses read-only RLS instead
- [x] RLS policy "Kiosk anon read-only" added in Supabase (verified: 399 rows)
- [x] Leaked password rotated; old one confirmed dead
- [x] Change-password feature added to `index.html`

### Live spectator view
- [x] `vr.html` broadcasts path progress over Supabase Realtime (~4x/sec)
- [x] `live.html` subscribes, floods screen with current emotion + path dot
- [x] `qr.html` renders a scannable QR linking to `live.html`
- [ ] Verify Realtime broadcast actually reaches spectators end-to-end

### Remaining / to verify
- [ ] Real Quest 3 walk-through on the physical path
- [ ] Confirm SLAM tracking holds over ~172m
- [ ] Tune color-wash opacity if it washes out in daylight
- [ ] (Optional) Quest OS-level kiosk lockdown

## PDF Generation Fix - COMPLETED (prior work)
- [x] Alerts hidden before capture
- [x] Container expanded; html2canvas uses scroll dimensions
- [x] Aspect-ratio scaling, content centered both axes

## Implementation Details
- `index.html` - diary app; PDF function `downloadDiaryCardPDF()`,
  change-password `handleChangePassword()`
- `vr.html` - kiosk; `feels-walk` A-Frame component drives the color flood
- Backend: Supabase project `bczevwhzlammcjomuqrg`, table `diary_entries`
- ~399 entries spanning Sep 2025 – May 2026
