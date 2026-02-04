# THE QUEUE — Collaborative Song Queue

A collaborative jukebox where anyone can scan a QR code and submit songs from Spotify, Apple Music, SoundCloud, or YouTube. Songs are resolved to YouTube for unified playback on a single host screen.

## How It Works

1. **Host** opens the main page on a screen (TV, laptop, projector)
2. **Guests** scan the QR code with their phone
3. Guests paste a song link from any supported platform
4. The song is matched to its YouTube equivalent and added to the queue
5. Songs play automatically in order
6. Guests are rate-limited to one submission every 5 minutes

### Supported Platforms
- YouTube / YouTube Music
- Spotify
- Apple Music
- SoundCloud
- Tidal
- Deezer

If a song can't be found on YouTube, it appears in the queue as "manual play" with a direct link to the original platform.

---

## Setup Guide

### Step 1: Create a Firebase Project (Free)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"** (or "Add project")
3. Name it something like `song-queue` — click Continue
4. You can disable Google Analytics (not needed) — click Continue
5. Wait for the project to be created, then click Continue

### Step 2: Create a Realtime Database

1. In your Firebase project, click **"Build"** in the left sidebar
2. Click **"Realtime Database"**
3. Click **"Create Database"**
4. Choose the location closest to you (e.g., `us-central1`) — click Next
5. Select **"Start in test mode"** — click Enable

> ⚠️ **Test mode** allows anyone to read/write for 30 days. This is fine for events. For longer-term use, see the Security Rules section below.

### Step 3: Get Your Firebase Config

1. In the Firebase console, click the **gear icon** (⚙️) next to "Project Overview"
2. Click **"Project settings"**
3. Scroll down to **"Your apps"** section
4. Click the **web icon** (`</>`) to add a web app
5. Name it anything (e.g., "song-queue-web") — you do NOT need Firebase Hosting
6. Click **"Register app"**
7. You'll see a code block with `firebaseConfig`. Copy those values.

### Step 4: Configure the App

Open `js/config.js` and replace the placeholder values:

```javascript
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyC...",                            // from Firebase
  authDomain: "song-queue-12345.firebaseapp.com",  // from Firebase
  databaseURL: "https://song-queue-12345-default-rtdb.firebaseio.com", // from Firebase
  projectId: "song-queue-12345",                   // from Firebase
  storageBucket: "song-queue-12345.appspot.com",   // from Firebase
  messagingSenderId: "123456789",                  // from Firebase
  appId: "1:123456789:web:abc123"                  // from Firebase
};

const SITE_URL = "https://yourusername.github.io/songqueue";
```

> **Important:** Update `SITE_URL` to match your actual GitHub Pages URL. This is what the QR code will point to.

### Step 5: Deploy to GitHub Pages

1. Create a new repo on GitHub (e.g., `songqueue`)
2. Push all the files to the repo:
   ```bash
   cd songqueue
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOURUSERNAME/songqueue.git
   git branch -M main
   git push -u origin main
   ```
3. Go to your repo on GitHub → **Settings** → **Pages**
4. Under "Source", select **"Deploy from a branch"**
5. Choose **main** branch, **/ (root)** folder — click Save
6. Wait a minute, then visit `https://yourusername.github.io/songqueue`

---

## Usage

### Host (the screen everyone sees)

- Open `https://yourusername.github.io/songqueue` on the display screen
- Make sure you're **logged into YouTube** in that browser (for age-restricted content)
- The QR code appears in the top-right corner
- When songs are added, click **"Start Playing"** to begin
- Songs auto-advance when they finish
- Use **Skip** to skip the current song
- Use **Clear Queue** to start fresh

### Guests (people adding songs)

- Scan the QR code or go to `https://yourusername.github.io/songqueue/submit/`
- Open the song in your music app (Spotify, Apple Music, etc.)
- Tap "Share" → "Copy Link"
- Paste the link and tap "Add"
- You can submit another song after 5 minutes

---

## Firebase Security Rules (Optional)

For longer-term use beyond 30-day test mode, set these rules in Firebase Console → Realtime Database → Rules:

```json
{
  "rules": {
    "queue": {
      ".read": true,
      ".write": true,
      "$songId": {
        ".validate": "newData.hasChildren(['title', 'status', 'submittedAt'])"
      }
    },
    "rateLimit": {
      ".read": true,
      ".write": true,
      "$deviceId": {
        ".validate": "newData.hasChild('lastSubmission')"
      }
    },
    "nowPlaying": {
      ".read": true,
      ".write": true
    }
  }
}
```

This allows public read/write but validates the data structure.

---

## File Structure

```
songqueue/
├── index.html           # Host/playback page (show on screen)
├── submit/
│   └── index.html       # Mobile submission page (QR code target)
├── js/
│   ├── config.js        # Firebase config (you edit this)
│   ├── resolver.js      # Cross-platform link → YouTube resolver
│   └── queue.js         # Firebase queue operations
└── README.md            # This file
```

## Technical Details

- **Link Resolution**: Uses the [Odesli/song.link API](https://odesli.co/) to match songs across platforms. Free, no API key required.
- **Playback**: YouTube IFrame Player API — no key needed for basic playback.
- **Real-time Sync**: Firebase Realtime Database keeps host and guest pages in sync.
- **Rate Limiting**: Device-based (localStorage fingerprint stored in Firebase). Using IP-based rate limiting isn't possible on a static site, and everyone on the same WiFi shares an IP anyway.
- **No backend required**: Everything runs client-side on GitHub Pages.

## Troubleshooting

**"Setup Required" message**: You need to add your Firebase config to `js/config.js`.

**QR code doesn't work**: Check that `SITE_URL` in `js/config.js` matches your actual GitHub Pages URL (including `https://`).

**Songs not resolving**: The Odesli API occasionally has downtime. YouTube links always work directly. If a non-YouTube link fails to resolve, it gets added as "manual play."

**YouTube player not starting**: Browsers require a user click before audio can play. The host needs to click "Start Playing" at least once.

**Queue not updating in real-time**: Check your Firebase Realtime Database rules aren't blocking reads/writes. In the Firebase console, go to Realtime Database → Rules and make sure reads and writes are allowed.
