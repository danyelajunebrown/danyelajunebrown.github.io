# Service Status

## Core Infrastructure

| Service | Purpose | URL | Status |
|---------|---------|-----|--------|
| GitHub Pages | Static site hosting | danyelajunebrown.github.io | Active |
| Supabase (Portfolio) | Database (portfolio_projects, portfolio_media) | qbbgrsdofmhiqeusguoq.supabase.co | Active |
| Supabase (Culture Circle) | Database (culture circle tables) | ezttcqgkegfikrmftlmo.supabase.co | Active |
| Supabase (JDCatBS map) | Database (jdcatbs_drawing) | hbhorkrfndwsnwdhxotd.supabase.co | Active |
| Cloudflare R2 | Media file storage | pub-f9bb84bd43c343799213e3bfbc9436c5.r2.dev | Active |
| R2 Upload Worker | Chunked upload handler | r2-upload-handler.db7613.workers.dev | Active |
| Songlink Proxy | CORS proxy for Odesli API | songlink-proxy.danyelajune.workers.dev | Active |

## Database Tables (Supabase)

### Portfolio
- `portfolio_projects` — artwork records (title, date, year, materials, scores)
- `portfolio_media` — media assets per project (url, type, sort_order)

### Culture Circle
- `participants`, `interviews`, `transcript_segments`, `voice_fingerprints`, `speaker_suggestions`, `email_change_requests`, `consent_forms`, `consent_records`, `audit_logs`, `notifications`

## Applications

| App | Location | Backend | Status |
|-----|----------|---------|--------|
| Portfolio (Sets) | projects.html | Supabase + R2 | Active |
| Culture Circle | Projects/2026/JDCatBS/culture-circle/ | Supabase + Deepgram + SendGrid | Edge functions need deploy |
| THE QUEUE | toolbelt/CoMmUnItY playlist/ | Firebase Realtime DB | Active |
| Dance Clips | toolbelt/dance-clips/ | Node.js + Puppeteer | Local dev only |
| Damages | toolbelt/damages/ | Flask + PostgreSQL | Scaffolded, not deployed |
| Make It Cunt | toolbelt/make-it-cunt/ | Flask | Scaffolded, not deployed |
| Gaze Study | Fuck You Looking At/ | Node.js + PostgreSQL | Scaffolded, not deployed |

## Key Files
- `projects.html` — Portfolio single-file app
- `projects.json` — Legacy data fallback
- `portfolio-schema.sql` — Supabase schema + migration
- `backup.sh` — Local backup script (exports Supabase + downloads R2 media)

## Backup
Run `./backup.sh` to export data + media locally.
For external drive: `./backup.sh /Volumes/YOUR_DRIVE/portfolio-backup`
