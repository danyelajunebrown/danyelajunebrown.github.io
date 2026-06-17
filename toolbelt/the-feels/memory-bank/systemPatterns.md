# System Patterns

## Architecture (native Unity app)
One scene, one MonoBehaviour you place; everything else self-wires.

**Assets/Scripts/**
- **TheFeelsData.cs** — SDK-independent data model. `EmotionColors` (feeling→family→
  color), `FeelsPath` (haversine length over a 14-point GPX polyline = ~445.8 m),
  `SegmentBuilder` (entries→duration-proportional segments), `FeelingSegment` struct.
- **FeelsDataLoader.cs** — MonoBehaviour. Anonymous read-only Supabase fetch of
  `diary_entries`; builds the segment list; `SegmentAtMeters(m)` returns the emotion
  you're "inside."
- **FeelsExperience.cs** — THE component. Drop it on one empty GameObject; it
  `[RequireComponent]`s FeelsDataLoader. Per frame: odometer → segment → tint + debug
  readout + adb heartbeat. Also stands up the Depth API.

**Assets/Resources/**
- **FeelsDepthTint.shader** (`TheFeels/DepthTint`) — the tint. Depth-live path tints
  real surfaces by proximity; `#else` path is the flat wash. Under Resources/ so it
  can't be stripped from the APK.
- **FeelsTint.shader** — older flat-only shader, kept as a fallback in the load chain.

**Assets/Editor/**
- **FeelsBuild.cs** — headless Android build entry (`FeelsBuild.Android`).
- **FeelsDepthSetup.cs** — headless enable of the two OpenXR features the Depth API
  needs (Meta Quest: Occlusion + Session).

**Assets/Plugins/Android/AndroidManifest.xml** — declares
`com.oculus.permission.USE_SCENE` + supported devices (quest3s).

## Rendering pattern (the tint)
- ONE quad, parented to the head camera, 1 m in front (`washDistance`), scale 40,
  `ZTest Always` → a full-FOV color film that's never clipped.
- Material = FeelsDepthTint; `_Color` set each frame to (emotion color, opacity =
  intensity × 0.1).
- The shader reprojects each pixel's world position into Meta's environment-depth
  texture and reads the real surface distance there:
  - **depth live** (HARD/SOFT_OCCLUSION keyword on): `prox =
    saturate((_MaxDist − realDist) / _MaxDist)`; near surfaces strong, far/empty clear.
    Floored at `_MinTint` so it's never fully blank.
  - **depth not live** (`#else`): flat wash at `_FlatFloor` (uniform film).
- The keyword is toggled GLOBALLY by `EnvironmentDepthManager` only once depth is
  actually streaming. `depth=on` in the heartbeat only means the manager was created —
  it does NOT prove frames are flowing or the keyword is set.

## Odometer (progress model) — artist-confirmed
- `_meters = clamp(_meters + horizontalHeadDisplacement * metersScale, 0, 445.8)`.
  `d.y` zeroed (vertical ignored).
- Starts at 0 on every fresh launch; accumulates movement in ANY direction; resets only
  on relaunch. Can begin anywhere on the path.
- `metersScale`: code default **1** (true walk); the SCENE serializes **20** (dev
  smoke-test value that amplifies pacing in a small room). Set to 1 for the install.
- Direction model: oldest entry (Sept 2025) sits at meters=0; walking accumulates
  toward "now."
- Known robustness gap: a tracking glitch/teleport inflates `d.magnitude` and can jump
  the odometer (saw 4 zone changes in 0.125 s). Should clamp per-frame displacement.

## Data flow
- Supabase `diary_entries` (feeling, intensity, timestamp, user_id), fetched
  oldest→newest, anon read-only RLS.
- `SegmentBuilder`: duration[i] = ts[i+1] − ts[i] (last → now); segment arc-length ∝
  duration; color from family map; opacity = intensity × 0.1.
- Same backend + same user_id as the WebXR prototype — the data layer was ported from
  `vr.html` and validated against live data (411 entries, 75 feelings, 0 fallbacks,
  2026-06-08). Count grows as new feelings are logged.

## Emotion → color (7 families)
happy `#FFE680` · surprised `#DDA0DD` · disgusted `#90EE90` · bad `#D3D3D3` ·
fearful `#FFB347` · angry `#FF6B6B` · sad `#87CEEB`. Dual-family feelings resolved
explicitly (overwhelmed→fearful; inferior/disappointed/embarrassed→sad) so edit order
can't flip them.
