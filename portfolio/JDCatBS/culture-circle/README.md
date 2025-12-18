# Service Culture Circle - Setup Guide

A secure interview research management system for veteran problem-posing research practice.

## Features

- Secure audio upload with automatic transcription (Deepgram)
- Speaker diarization with voice fingerprint matching
- Participant login keys (no passwords)
- IRB-compliant audit logging
- Consent workflow
- Participants see only their own transcript portions

## Setup Instructions

### 1. Supabase Project

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor** and run the contents of `schema.sql`
4. Go to **Storage** and create a bucket named `interview-audio`:
   - Public: OFF
   - File size limit: 500MB
   - Allowed MIME types: `audio/mpeg, audio/wav, audio/mp4, audio/x-m4a`

### 2. Configure Environment Variables

In your Supabase project settings, add these secrets:

```
DEEPGRAM_API_KEY=your_deepgram_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=your-email@domain.com
FROM_NAME=Service Culture Circle
```

### 3. Deploy Edge Functions

Install the Supabase CLI:
```bash
npm install -g supabase
```

Login and link your project:
```bash
supabase login
supabase link --project-ref YOUR_PROJECT_REF
```

Deploy the functions:
```bash
cd supabase/functions
supabase functions deploy process-audio
supabase functions deploy send-login-key
supabase functions deploy verify-login-key
```

### 4. Update Frontend Configuration

Edit `js/supabase-config.js` and replace:
```javascript
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
```

Find these values in your Supabase project: **Settings > API**

### 5. Create Study Lead Account

1. Open `index.html` in a browser
2. Click "Create account" and sign up with your email
3. Check your email for the confirmation link
4. You're now the study lead with admin access

## Third-Party Services

### Deepgram (Transcription)

1. Sign up at [deepgram.com](https://deepgram.com)
2. Create an API key
3. Cost: ~$0.0043/minute with speaker diarization

### SendGrid (Email)

1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Verify a sender email address
3. Create an API key
4. Free tier: 100 emails/day

## Cost Estimate

| Service | Monthly |
|---------|---------|
| Supabase Pro | $25 |
| Deepgram (~20hrs audio) | $5-10 |
| SendGrid | $0 (free tier) |
| **Total** | **~$30-35** |

## File Structure

```
culture-circle/
├── index.html           # Study lead admin dashboard
├── participant.html     # Participant portal
├── schema.sql           # Database schema
├── README.md            # This file
├── js/
│   ├── supabase-config.js
│   ├── admin.js
│   └── participant.js
└── supabase/functions/
    ├── process-audio/
    ├── send-login-key/
    └── verify-login-key/
```

## Workflow

1. **Upload**: Study lead uploads audio file
2. **Transcribe**: Deepgram transcribes with speaker diarization
3. **Delete Audio**: Original audio is deleted (IRB compliance)
4. **Tag Speakers**: Study lead assigns speakers to participants
5. **Notify**: Login keys sent to new participants via SendGrid
6. **Access**: Participants log in, consent, and view their portions

## Security

- Login keys: `SCC-XXXX-XXXX-XXXX-XXXX` format (~2^80 combinations)
- Keys stored as SHA-256 hash only
- Rate limiting: 5 attempts/minute/IP
- All access logged in audit table
- Row-level security on all tables

## IRB Compliance

- Encryption at rest (Supabase default)
- Complete audit trail
- Consent workflow with withdrawal option
- Audio deleted immediately after transcription
- Participants see only their own data
