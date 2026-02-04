// ============================================
// CROSS-PLATFORM SONG LINK RESOLVER
// ============================================
// Takes a link from Spotify, Apple Music, SoundCloud, YouTube, etc.
// and resolves it to a YouTube video for unified playback.
// Uses the Odesli (song.link) API — free, no key needed.

const ODESLI_API = "https://api.song.link/v1-alpha.1/links";

const PLATFORM_NAMES = {
  youtube: "YouTube",
  spotify: "Spotify",
  appleMusic: "Apple Music",
  soundcloud: "SoundCloud",
  tidal: "Tidal",
  deezer: "Deezer",
  unknown: "Link",
  invalid: "Invalid",
};

const PLATFORM_COLORS = {
  youtube: "#FF0000",
  spotify: "#1DB954",
  appleMusic: "#FC3C44",
  soundcloud: "#FF5500",
  tidal: "#000000",
  deezer: "#A238FF",
  unknown: "#888888",
};

// Detect which platform a URL belongs to
function detectPlatform(url) {
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase();
    if (host.includes("youtube.com") || host.includes("youtu.be"))
      return "youtube";
    if (host.includes("spotify.com")) return "spotify";
    if (host.includes("music.apple.com")) return "appleMusic";
    if (host.includes("soundcloud.com")) return "soundcloud";
    if (host.includes("tidal.com")) return "tidal";
    if (host.includes("deezer.com")) return "deezer";
    return "unknown";
  } catch {
    return "invalid";
  }
}

// Extract a YouTube video ID from various YouTube URL formats
function extractYouTubeId(url) {
  const patterns = [
    /(?:youtube\.com\/watch\?.*v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})/,
    /youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})/,
    /music\.youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})/,
  ];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

// Get metadata for a YouTube video via the free oEmbed endpoint
async function getYouTubeMetadata(videoId) {
  try {
    const url = `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`;
    const response = await fetch(url);
    if (!response.ok) throw new Error("oEmbed failed");
    const data = await response.json();
    return {
      title: data.title || "Unknown Title",
      artist: data.author_name || "",
      thumbnailUrl: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
    };
  } catch {
    return {
      title: "Unknown Title",
      artist: "",
      thumbnailUrl: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
    };
  }
}

// Clean up song title — remove common YouTube junk from titles
function cleanTitle(title, artist) {
  if (!title) return "Unknown Title";
  // Remove common suffixes like (Official Video), [Lyrics], etc.
  let cleaned = title
    .replace(
      /\s*[\(\[](official\s*(music\s*)?video|lyrics?|audio|visualizer|hd|hq|official|music\s*video)[\)\]]/gi,
      ""
    )
    .replace(/\s*-\s*topic$/gi, "")
    .trim();
  // If artist is in the title like "Artist - Song", try to split
  if (artist && cleaned.toLowerCase().startsWith(artist.toLowerCase() + " - ")) {
    cleaned = cleaned.substring(artist.length + 3).trim();
  }
  return cleaned || title;
}

// ============================================
// MAIN RESOLVER FUNCTION
// ============================================
// Takes any music URL, returns normalized song data with YouTube ID

async function resolveLink(url) {
  // Clean the URL
  url = url.trim();
  if (!url.startsWith("http")) {
    url = "https://" + url;
  }

  const platform = detectPlatform(url);

  if (platform === "invalid") {
    throw new Error(
      "That doesn't look like a valid URL. Paste a link from YouTube, Spotify, Apple Music, or SoundCloud."
    );
  }

  if (platform === "unknown") {
    throw new Error(
      "Platform not recognized. Try a link from YouTube, Spotify, Apple Music, SoundCloud, Tidal, or Deezer."
    );
  }

  // --- YouTube links: resolve directly ---
  if (platform === "youtube") {
    const videoId = extractYouTubeId(url);
    if (!videoId) throw new Error("Couldn't read that YouTube link. Try copying the full URL.");
    const meta = await getYouTubeMetadata(videoId);
    return {
      title: cleanTitle(meta.title, meta.artist),
      artist: meta.artist,
      youtubeId: videoId,
      thumbnailUrl: meta.thumbnailUrl,
      originalUrl: url,
      platform: "youtube",
      manualPlay: false,
    };
  }

  // --- Other platforms: use Odesli API ---
  try {
    const response = await fetch(
      `${ODESLI_API}?url=${encodeURIComponent(url)}&userCountry=US`
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Song not found. Double-check the link and try again.");
      }
      throw new Error("Song lookup service is temporarily unavailable. Try again in a moment.");
    }

    const data = await response.json();

    // Extract metadata from the first available entity
    const entities = data.entitiesByUniqueId || {};
    const firstEntity = Object.values(entities)[0] || {};
    const title = firstEntity.title || "Unknown Title";
    const artist = firstEntity.artistName || "";
    const thumbnailUrl = firstEntity.thumbnailUrl || "";

    // Look for a YouTube equivalent
    const youtubeLink =
      data.linksByPlatform?.youtube || data.linksByPlatform?.youtubeMusic;

    if (youtubeLink && youtubeLink.url) {
      const videoId = extractYouTubeId(youtubeLink.url);
      const ytThumb = videoId
        ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`
        : "";
      return {
        title: cleanTitle(title, artist),
        artist,
        youtubeId: videoId,
        thumbnailUrl: ytThumb || thumbnailUrl,
        originalUrl: url,
        platform,
        manualPlay: !videoId,
      };
    }

    // No YouTube match — manual play fallback
    return {
      title: cleanTitle(title, artist),
      artist,
      youtubeId: null,
      thumbnailUrl,
      originalUrl: url,
      platform,
      manualPlay: true,
    };
  } catch (error) {
    // If it's one of our user-friendly errors, rethrow
    if (
      error.message.includes("not found") ||
      error.message.includes("unavailable") ||
      error.message.includes("not recognized")
    ) {
      throw error;
    }
    // Network or unexpected error — fallback to manual play
    console.error("Resolver error:", error);
    return {
      title: "Unknown Track",
      artist: "",
      youtubeId: null,
      thumbnailUrl: "",
      originalUrl: url,
      platform,
      manualPlay: true,
    };
  }
}
