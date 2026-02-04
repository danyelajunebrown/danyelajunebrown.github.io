// ============================================
// FIREBASE CONFIGURATION
// ============================================
// Follow the README.md instructions to set up your Firebase project,
// then replace these placeholder values with your actual config.

const FIREBASE_CONFIG = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  databaseURL: "https://YOUR_PROJECT-default-rtdb.firebaseio.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// ============================================
// SITE URL
// ============================================
// Update this to your actual GitHub Pages URL.
// This is used for QR code generation on the host page.
// Example: "https://yourusername.github.io/songqueue"

const SITE_URL = "https://YOUR_USERNAME.github.io/songqueue";

// ============================================
// SETTINGS
// ============================================

const RATE_LIMIT_MS = 5 * 60 * 1000; // 5 minutes between submissions
