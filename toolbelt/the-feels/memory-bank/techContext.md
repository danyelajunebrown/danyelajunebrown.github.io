# Tech Context

## Technologies Used

### Frontend
- **HTML5** - Two standalone single-page documents
- **CSS3** - Flexbox, grid, animations
- **Vanilla JavaScript** - All application logic

### External Libraries (all CDN, no npm build)
- **Supabase JS SDK** (v2.39.7) - Authentication & database
- **html2canvas** (v1.4.1) - DOM to canvas capture for PDF
- **jsPDF** (v2.5.1) - PDF generation
- **A-Frame** (v1.6.0) - WebXR framework for the VR/AR kiosk

### Development Environment
- Visual Studio Code, Git
- Browser-based testing (Chrome/Safari) for the diary app
- Meta Quest 3 browser for the VR kiosk (WebXR needs HTTPS — i.e. deployed)

## Setup
- `index.html` and `vr.html`, each with embedded CSS and JS
- CDN-loaded dependencies
- Hosted on GitHub Pages (`danyelajunebrown.github.io/toolbelt/the-feels/`)
- Supabase project `bczevwhzlammcjomuqrg` for backend

## Supabase
- Table `diary_entries`: feeling, intensity, dbt_skill, timestamp, user_id
- RLS enabled. Policies:
  - Owner policies for the diary app (authenticated users see their own rows)
  - "Kiosk anon read-only": `anon` SELECT scoped to the kiosk owner's user_id
- Kiosk owner user_id: `ee04c688-d857-45f8-849c-2f072053cf28`

## Browser / Device APIs
- Canvas API (html2canvas), Drag-and-Drop API, Touch events
- LocalStorage (via Supabase session)
- **WebXR** `immersive-ar` — passthrough + inside-out SLAM head tracking on Quest 3

## Constraints
- WebXR requires HTTPS and a user gesture to enter an immersive session
- Quest 3 has no GPS; position comes only from on-device SLAM tracking
- SLAM tracking is built for room-scale — reliability over a ~172m walk is
  unverified and must be tested on the real path
- A web page cannot make itself the only app on the headset; true kiosk lockdown
  is a Quest OS / device-management setting

## Security Notes
- The Supabase anon key is public by design (safe in client code)
- No user password is stored in any file (kiosk uses read-only RLS instead)
- An earlier commit briefly embedded a password; it has since been rotated/killed
