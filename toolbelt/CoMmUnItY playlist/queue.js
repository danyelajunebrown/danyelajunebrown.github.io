// ============================================
// QUEUE MANAGEMENT — Firebase Realtime Database
// ============================================

let db = null;
let queueRef = null;
let rateLimitRef = null;
let nowPlayingRef = null;
let firebaseReady = false;

// Initialize Firebase and get database references
function initFirebase() {
  try {
    if (!firebase.apps.length) {
      firebase.initializeApp(FIREBASE_CONFIG);
    }
    db = firebase.database();
    queueRef = db.ref("queue");
    rateLimitRef = db.ref("rateLimit");
    nowPlayingRef = db.ref("nowPlaying");
    firebaseReady = true;
    console.log("Firebase initialized");
    return true;
  } catch (error) {
    console.error("Firebase init failed:", error);
    firebaseReady = false;
    return false;
  }
}

// ============================================
// DEVICE FINGERPRINT (for rate limiting)
// ============================================
// Uses a random ID stored in localStorage.
// At a day center on shared WiFi, IP-based limiting would
// block everyone since they share the same public IP.
// This device-based approach is honest-system but works for the context.

function getDeviceId() {
  let id = localStorage.getItem("songqueue_device_id");
  if (!id) {
    id =
      "d_" +
      Date.now().toString(36) +
      "_" +
      Math.random().toString(36).substring(2, 10);
    localStorage.setItem("songqueue_device_id", id);
  }
  return id;
}

// ============================================
// RATE LIMITING
// ============================================

// Check if the current device is rate-limited.
// Returns remaining ms if limited, 0 if OK to submit.
async function checkRateLimit() {
  const deviceId = getDeviceId();
  const snapshot = await rateLimitRef.child(deviceId).once("value");
  const data = snapshot.val();

  if (!data || !data.lastSubmission) return 0;

  const elapsed = Date.now() - data.lastSubmission;
  if (elapsed < RATE_LIMIT_MS) {
    return RATE_LIMIT_MS - elapsed;
  }
  return 0;
}

// Record a submission timestamp for rate limiting
async function updateRateLimit() {
  const deviceId = getDeviceId();
  await rateLimitRef.child(deviceId).set({
    lastSubmission: firebase.database.ServerValue.TIMESTAMP,
  });
}

// ============================================
// QUEUE OPERATIONS
// ============================================

// Add a resolved song to the queue
async function addToQueue(songData) {
  // Enforce rate limit
  const remaining = await checkRateLimit();
  if (remaining > 0) {
    const error = new Error("RATE_LIMITED");
    error.remaining = remaining;
    throw error;
  }

  const entry = {
    title: songData.title || "Unknown Title",
    artist: songData.artist || "",
    youtubeId: songData.youtubeId || null,
    originalUrl: songData.originalUrl || "",
    platform: songData.platform || "unknown",
    thumbnailUrl: songData.thumbnailUrl || "",
    manualPlay: songData.manualPlay || false,
    status: "waiting", // waiting → playing → played
    submittedAt: firebase.database.ServerValue.TIMESTAMP,
    deviceId: getDeviceId(),
  };

  const newRef = await queueRef.push(entry);
  await updateRateLimit();

  return { id: newRef.key, ...entry };
}

// Update a song's status
async function updateSongStatus(songId, status) {
  await queueRef.child(songId).update({ status });
}

// Set the currently playing song
async function setNowPlaying(songId) {
  if (songId) {
    await nowPlayingRef.set({
      queueId: songId,
      startedAt: firebase.database.ServerValue.TIMESTAMP,
    });
  } else {
    await nowPlayingRef.remove();
  }
}

// Remove a song from the queue
async function removeSong(songId) {
  await queueRef.child(songId).remove();
}

// Clear the entire queue (host only)
async function clearQueue() {
  await queueRef.remove();
  await nowPlayingRef.remove();
}

// Reset any "playing" songs back to "waiting" (for host page reload)
async function resetPlayingToWaiting() {
  const snapshot = await queueRef
    .orderByChild("status")
    .equalTo("playing")
    .once("value");
  const updates = {};
  snapshot.forEach((child) => {
    updates[child.key + "/status"] = "waiting";
  });
  if (Object.keys(updates).length > 0) {
    await queueRef.update(updates);
  }
  await nowPlayingRef.remove();
}

// ============================================
// REAL-TIME LISTENERS
// ============================================

// Listen to all queue changes. Callback receives the full sorted queue array.
function onQueueChange(callback) {
  queueRef.orderByChild("submittedAt").on("value", (snapshot) => {
    const queue = [];
    snapshot.forEach((child) => {
      queue.push({ id: child.key, ...child.val() });
    });
    callback(queue);
  });
}

// Listen to now-playing changes
function onNowPlayingChange(callback) {
  nowPlayingRef.on("value", (snapshot) => {
    callback(snapshot.val());
  });
}

// ============================================
// QUEUE HELPERS
// ============================================

// Get songs by status from a queue array
function getByStatus(queue, status) {
  return queue.filter((s) => s.status === status);
}

// Get the next waiting song
function getNextWaiting(queue) {
  return queue.find((s) => s.status === "waiting");
}

// Get the currently playing song
function getCurrentlyPlaying(queue) {
  return queue.find((s) => s.status === "playing");
}

// Format time remaining for rate limit display
function formatTimeRemaining(ms) {
  const totalSeconds = Math.ceil(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}
