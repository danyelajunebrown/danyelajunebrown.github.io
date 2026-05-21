# System Patterns

## Architecture
Two standalone HTML pages, vanilla JavaScript, all client-side. No build step.
- `index.html` — the diary card app
- `vr.html` — the Meta Quest 3 passthrough-AR kiosk

## Diary App (`index.html`)

### Authentication
- Supabase Auth for user management; session persisted by the SDK
- Change-password action in the header calls `supabase.auth.updateUser({ password })`

### Feelings Wheel
- SVG-based rotating wheel, touch + mouse drag
- Hierarchical emotion selection (inner/middle/outer rings)
- `emotionWheelData` defines 7 families, each with a color, middle, and outer emotions

### Diary Card Generation
- Weekly report with date-range selection
- Drag-and-drop entry reorganization (updates timestamps in DB)
- Entries grouped by day of week

### PDF Generation (fixed)
- Hide alerts → expand container → html2canvas at scrollWidth/scrollHeight
- jsPDF landscape A4, content centered both axes

## VR/AR Kiosk (`vr.html`)

### Stack
- A-Frame 1.6.0, WebXR `immersive-ar` (passthrough), `referenceSpaceType: local-floor`

### Concept
- The wearer physically walks a ~172.5m real-world path
  (start `42.003567,-73.921784` → end `42.003286,-73.923837`, haversine distance)
- Every `diary_entries` row becomes a back-to-back block along the path
- Block length ∝ how long that feeling was felt = next entry's timestamp minus
  this one's; the most recent entry extends to "now"
- The headset's own SLAM tracking measures distance walked; progress = the
  walker's displacement projected onto the captured start→end direction
- No GPS (Quest 3 has none) and no auto-movement — the walk is fully wearer-driven

### Rendering
- The `feels-walk` A-Frame component reads head position each tick, finds the
  current emotion block, and crossfades a camera-parented translucent plane
  (the "color wash") to that emotion's color
- Color from `emotionWheelData`; wash opacity scales with intensity (1-5)
- The current emotion's name floats ahead, repositioned on each zone change
- NOTE: a translucent wash over bright passthrough content reads weaker than
  over dark content (compositing contrast), so daylight scenes mute the color

### Data access (no stored password)
- Reads `diary_entries` anonymously, scoped by `KIOSK_USER_ID`
- Supabase RLS policy "Kiosk anon read-only": grants `anon` SELECT on
  `diary_entries` where `user_id = ee04c688-d857-45f8-849c-2f072053cf28`
- Read-only — nobody can insert/edit/delete even with the public anon key
- Re-pulls every 60s so a newly logged feeling reshapes the path live

## Live Spectator View (`live.html` + `qr.html`)
- Onlookers cannot get the real passthrough video (WebXR blocks camera access),
  so the spectator view is a synced companion, not a literal video stream
- `vr.html` broadcasts the wearer's path progress (a 0-1 fraction) over a
  Supabase Realtime channel `feels-live`, ~4x/sec
- `live.html` loads the same timeline itself (read-only RLS), subscribes to the
  channel, and floods the phone screen with the wearer's current emotion color +
  name, plus a dot moving along the full year-long path bar
- Payload is just `{ progress }` — `live.html` derives emotion/color/date locally
- `qr.html` renders a QR pointing to `live.html` for onlookers to scan
- Goes idle ("waiting for the walk" / "paused") if no signal for 6s

## Data Flow
- All emotion data in Supabase `diary_entries` (feeling, intensity, timestamp, user_id)
- Diary app: fetched by date range, grouped by weekday client-side
- Kiosk + spectator: full history fetched oldest→newest, converted to proportional
  path blocks; spectator position arrives via Realtime broadcast
