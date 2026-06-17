// TheFeelsData.cs — The Feels, Quest 3 native build (data layer)
// -----------------------------------------------------------------------------
// SDK-INDEPENDENT. This file does NOT touch the Meta XR SDK. It only:
//   1. defines the diary/segment data model + emotion-family colors,
//   2. measures the real-world path length (haversine over the GPX polyline),
//   3. builds duration-proportional segments along the path's arc length.
//
// The Supabase fetch (a MonoBehaviour) lives in its own file, FeelsDataLoader.cs,
// because Unity requires a component's class name to match its file name.
// The passthrough / odometer head-tracking MonoBehaviour is FeelsExperience.cs.
//
// Model decisions (artist-confirmed 2026-06-08/09):
//   * Progress  = distance-walked ODOMETER, clamped to PATH_LENGTH.
//   * Direction = walker starts at the WEST end (oldest entry, Sept 2025) and
//                 walks EAST toward "now". Entries are ordered oldest->newest,
//                 so segment 0 sits at meters=0 — no reversal required.
//   * Opacity   = intensity * 10%  -> 0.1 / 0.2 / 0.3 / 0.4 / 0.5  (brief override;
//                 this REPLACES vr.html's 0.14 + intensity*0.082 formula).
//   * PATH_LENGTH is DERIVED (haversine over the measured GPX polyline), not hardcoded.
//
// The numeric logic mirrors a Python port that was validated against live data
// (411 entries, 75 feelings, 0 color fallbacks) on 2026-06-08.
// -----------------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;

namespace TheFeels
{
    [Serializable]
    public class DiaryEntry
    {
        public string feeling;
        public int intensity;
        public string timestamp;
    }

    // JsonUtility can't parse a top-level JSON array; we wrap the response as {"items":[...]}.
    [Serializable]
    class DiaryEntryList { public DiaryEntry[] items; }

    public struct FeelingSegment
    {
        public string feeling;   // exact logged string — the atomic unit (label / animation key)
        public int intensity;    // 1..5
        public Color color;      // emotion-family color (opaque RGB)
        public float opacity;    // intensity * 0.1  (0.1 .. 0.5)
        public float startM;     // distance along path, meters (oldest entry => 0)
        public float endM;
        public float LengthM { get { return endM - startM; } }
    }

    // -------------------------------------------------------------------------
    // Feeling -> family color. Ported from vr.html's emotionWheelData, with the
    // dual-family / free-text resolutions made EXPLICIT so edit order can't flip them.
    // -------------------------------------------------------------------------
    public static class EmotionColors
    {
        public static readonly Color Default = Hex("#9d8cff"); // should never fire

        static readonly Dictionary<string, Color> Family = new Dictionary<string, Color>
        {
            { "happy",     Hex("#FFE680") },
            { "surprised", Hex("#DDA0DD") },
            { "disgusted", Hex("#90EE90") },
            { "bad",       Hex("#D3D3D3") },
            { "fearful",   Hex("#FFB347") },
            { "angry",     Hex("#FF6B6B") },
            { "sad",       Hex("#87CEEB") },
        };

        static readonly Dictionary<string, string> Map = BuildMap();

        static Dictionary<string, string> BuildMap()
        {
            var m = new Dictionary<string, string>();
            Action<string, string[]> add = (family, feelings) =>
            {
                m[family] = family;
                foreach (var f in feelings) m[f.ToLowerInvariant()] = family;
            };

            add("happy", new[] { "Playful","Aroused","Cheeky","Content","Free","Joyful","Interested","Inquisitive","Curious","Proud","Successful","Confident","Accepted","Respected","Valued","Powerful","Courageous","Creative","Peaceful","Loving","Thankful","Trusting","Sensitive","Intimate","Optimistic","Hopeful","Inspired" });
            add("surprised", new[] { "Startled","Shocked","Dismayed","Confused","Disillusioned","Perplexed","Amazed","Awe","Astonished","Excited","Eager","Energetic" });
            add("disgusted", new[] { "Disapproving","Judgmental","Embarrassed","Disappointed","Appalled","Revolted","Awful","Nauseated","Detestable","Avoidance","Hesitant","Aversion" });
            add("bad", new[] { "Bored","Indifferent","Apathetic","Busy","Pressured","Rushed","Stressed","Overwhelmed","Out of control","Tired","Sleepy","Unfocussed" });
            add("fearful", new[] { "Scared","Helpless","Frightened","Anxious","Overwhelmed","Worried","Insecure","Inadequate","Inferior","Weak","Worthless","Insignificant","Rejected","Excluded","Persecuted","Threatened","Nervous","Exposed" });
            add("angry", new[] { "Let down","Betrayed","Resentful","Humiliated","Disrespected","Ridiculed","Bitter","Indignant","Violated","Mad","Furious","Jealous","Aggressive","Provoked","Hostile","Frustrated","Infuriated","Annoyed","Distant","Withdrawn","Numb","Critical","Skeptical","Dismissive" });
            add("sad", new[] { "Hurt","Embarrassed","Disappointed","Depressed","Inferior","Empty","Guilty","Remorseful","Ashamed","Despair","Grief","Powerless","Vulnerable","Fragile","Victimized","Lonely","Isolated","Abandoned" });

            // Explicit resolutions (artist-confirmed). These OVERRIDE whatever the wheel
            // lists above produced, so the result is independent of insertion order.
            m["overwhelmed"]           = "fearful"; // appears under both Bad and Fearful
            m["inferior"]              = "sad";     // appears under both Fearful and Sad
            m["disappointed"]          = "sad";     // appears under both Disgusted and Sad
            m["embarrassed"]           = "sad";     // appears under both Disgusted and Sad
            m["anxiety"]               = "fearful"; // free-text -> anxious
            m["tired or disappointed"] = "bad";     // free-text -> tired
            return m;
        }

        public static Color Get(string feeling)
        {
            var key = (feeling ?? "").Trim().ToLowerInvariant();
            string fam;
            Color c;
            if (Map.TryGetValue(key, out fam) && Family.TryGetValue(fam, out c)) return c;
            Debug.LogWarning("[TheFeels] No family for feeling '" + feeling + "' — DEFAULT used (should never happen).");
            return Default;
        }

        public static string FamilyOf(string feeling)
        {
            var key = (feeling ?? "").Trim().ToLowerInvariant();
            string fam;
            return Map.TryGetValue(key, out fam) ? fam : "default";
        }

        static Color Hex(string hex)
        {
            Color c;
            ColorUtility.TryParseHtmlString(hex, out c);
            return c;
        }
    }

    // -------------------------------------------------------------------------
    // Measured real-world path. PATH_LENGTH = haversine sum over the polyline.
    // Source: MapPlanner GPX, 2026-06-09 (14 points, recorded East->West).
    // Polyline length ~= 445.8 m; straight-line endpoints ~= 375 m; elevation net ~0.
    // Re-measured? Replace Pts and the length recomputes automatically.
    // -------------------------------------------------------------------------
    public static class FeelsPath
    {
        static readonly double[,] Pts =
        {
            { 42.005619, -73.921073 }, { 42.005769, -73.921294 }, { 42.005872, -73.921572 },
            { 42.005969, -73.921835 }, { 42.005901, -73.922156 }, { 42.005730, -73.922752 },
            { 42.005333, -73.923134 }, { 42.005049, -73.923394 }, { 42.004731, -73.923654 },
            { 42.004493, -73.923944 }, { 42.004413, -73.924204 }, { 42.004391, -73.924631 },
            { 42.004300, -73.924876 }, { 42.003959, -73.925029 },
        };

        public static readonly float LengthMeters = ComputeLength();

        static float ComputeLength()
        {
            double sum = 0.0;
            int n = Pts.GetLength(0);
            for (int i = 1; i < n; i++)
                sum += Haversine(Pts[i - 1, 0], Pts[i - 1, 1], Pts[i, 0], Pts[i, 1]);
            return (float)sum;
        }

        static double Haversine(double lat1, double lon1, double lat2, double lon2)
        {
            const double R = 6371000.0;
            double dLat = Deg2Rad(lat2 - lat1);
            double dLon = Deg2Rad(lon2 - lon1);
            double a = Math.Sin(dLat / 2) * Math.Sin(dLat / 2)
                     + Math.Cos(Deg2Rad(lat1)) * Math.Cos(Deg2Rad(lat2)) * Math.Sin(dLon / 2) * Math.Sin(dLon / 2);
            return 2.0 * R * Math.Asin(Math.Sqrt(a));
        }

        static double Deg2Rad(double d) { return d * Math.PI / 180.0; }
    }

    // -------------------------------------------------------------------------
    // entries (oldest->newest) -> segments along arc length.
    // duration[i] = ts[i+1] - ts[i]; last entry extends to "now".
    // -------------------------------------------------------------------------
    public static class SegmentBuilder
    {
        public static List<FeelingSegment> Build(IReadOnlyList<DiaryEntry> entries, float pathLength, DateTime nowUtc)
        {
            var segs = new List<FeelingSegment>();
            if (entries == null || entries.Count == 0) return segs;

            int n = entries.Count;
            var ts = new long[n];
            for (int i = 0; i < n; i++) ts[i] = ToUnixMs(entries[i].timestamp);
            long nowMs = ToUnixMs(nowUtc);

            var dur = new double[n];
            double total = 0.0;
            for (int i = 0; i < n; i++)
            {
                long end = (i < n - 1) ? ts[i + 1] : nowMs;
                dur[i] = Math.Max(0.0, end - ts[i]);
                total += dur[i];
            }
            if (total <= 0.0) { for (int i = 0; i < n; i++) dur[i] = 1.0; total = n; }

            double acc = 0.0;
            for (int i = 0; i < n; i++)
            {
                float startM = (float)(acc / total * pathLength);
                acc += dur[i];
                float endM = (float)(acc / total * pathLength);
                int intensity = Mathf.Clamp(entries[i].intensity, 1, 5);
                segs.Add(new FeelingSegment
                {
                    feeling = string.IsNullOrEmpty(entries[i].feeling) ? "—" : entries[i].feeling,
                    intensity = intensity,
                    color = EmotionColors.Get(entries[i].feeling),
                    opacity = intensity * 0.1f,
                    startM = startM,
                    endM = endM,
                });
            }
            return segs;
        }

        static long ToUnixMs(string iso)
        {
            // Supabase ISO 8601, e.g. "2025-09-22T23:19:17.223+00:00".
            var dto = DateTimeOffset.Parse(iso, CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal);
            return dto.ToUnixTimeMilliseconds();
        }

        static long ToUnixMs(DateTime dt)
        {
            return new DateTimeOffset(DateTime.SpecifyKind(dt, DateTimeKind.Utc)).ToUnixTimeMilliseconds();
        }
    }
}
