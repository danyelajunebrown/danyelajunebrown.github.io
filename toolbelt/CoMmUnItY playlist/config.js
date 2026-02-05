// ============================================
// FIREBASE CONFIGURATION
// ============================================
// Follow the README.md instructions to set up your Firebase project,
// then replace these placeholder values with your actual config.

const firebaseConfig = {
  apiKey: "AIzaSyDtBsAJchGz_j9thU9iX2LeyaYo1b8Mmiw",
  authDomain: "song-queue-9946a.firebaseapp.com",
  databaseURL: "https://song-queue-9946a-default-rtdb.firebaseio.com",
  projectId: "song-queue-9946a",
  storageBucket: "song-queue-9946a.firebasestorage.app",
  messagingSenderId: "916921179333",
  appId: "1:916921179333:web:2dd61d4b6acb49118124ac"
};


// ============================================
// SITE URL
// ============================================
// Update this to your actual GitHub Pages URL.
// This is used for QR code generation on the host page.
// Example: "https://yourusername.github.io/songqueue"

const SITE_URL = "https://danyelajunebrown.github.io/songqueue";

// ============================================
// SETTINGS
// ============================================

const RATE_LIMIT_MS = 5 * 60 * 1000; // 5 minutes between submissions
