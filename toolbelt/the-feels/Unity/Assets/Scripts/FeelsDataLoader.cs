// FeelsDataLoader.cs — The Feels · Quest 3 native build (data layer, networking half)
// -----------------------------------------------------------------------------
// Split out of TheFeelsData.cs so it lives in a file matching its class name.
// Unity REQUIRES that for a MonoBehaviour to be attachable as a component
// (Add Component button, AddComponent<T>(), and [RequireComponent] all need it).
// Functionally identical to the version that used to live in TheFeelsData.cs.
//
// SDK-INDEPENDENT: only UnityEngine + the rest of the TheFeels data layer.
// Read-only ANONYMOUS Supabase access — the RLS policy restricts anon to SELECT
// on the kiosk user's rows; the key is the public anon key (already in vr.html).
// -----------------------------------------------------------------------------

using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

namespace TheFeels
{
    // Drop this on a GameObject and call StartCoroutine(Load()) at launch.
    public class FeelsDataLoader : MonoBehaviour
    {
        const string SupabaseUrl = "https://bczevwhzlammcjomuqrg.supabase.co";
        const string KioskUserId = "ee04c688-d857-45f8-849c-2f072053cf28";
        const string AnonKey =
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJjemV2d2h6bGFtbWNqb211cXJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg1NzkzMzQsImV4cCI6MjA3NDE1NTMzNH0.m8dgNY4UdUWvCTCe1_Zn2Ifbzym9dS7NMk7jxTg0_T4";

        public IReadOnlyList<FeelingSegment> Segments { get { return _segments; } }
        public event Action<IReadOnlyList<FeelingSegment>> OnSegmentsReady;

        List<FeelingSegment> _segments = new List<FeelingSegment>();

        public IEnumerator Load()
        {
            string url = SupabaseUrl + "/rest/v1/diary_entries"
                       + "?select=feeling,intensity,timestamp"
                       + "&user_id=eq." + KioskUserId
                       + "&order=timestamp.asc";

            using (var req = UnityWebRequest.Get(url))
            {
                req.SetRequestHeader("apikey", AnonKey);
                req.SetRequestHeader("Authorization", "Bearer " + AnonKey);
                req.SetRequestHeader("Accept", "application/json");
                yield return req.SendWebRequest();

#if UNITY_2020_2_OR_NEWER
                if (req.result != UnityWebRequest.Result.Success)
#else
                if (req.isNetworkError || req.isHttpError)
#endif
                {
                    Debug.LogError("[TheFeels] load failed: " + req.error);
                    yield break;
                }

                string json = req.downloadHandler.text;
                var wrapped = "{\"items\":" + json + "}";
                var list = JsonUtility.FromJson<DiaryEntryList>(wrapped);
                var entries = (list != null && list.items != null)
                    ? new List<DiaryEntry>(list.items)
                    : new List<DiaryEntry>();

                _segments = SegmentBuilder.Build(entries, FeelsPath.LengthMeters, DateTime.UtcNow);
                Debug.Log("[TheFeels] " + entries.Count + " entries -> " + _segments.Count
                          + " segments over " + FeelsPath.LengthMeters.ToString("F1") + " m");
                if (OnSegmentsReady != null) OnSegmentsReady(_segments);
            }
        }

        // Odometer position (meters walked, 0 = start/oldest) -> the emotion you're "inside".
        public FeelingSegment SegmentAtMeters(float meters)
        {
            if (_segments.Count == 0) return default(FeelingSegment);
            meters = Mathf.Clamp(meters, 0f, FeelsPath.LengthMeters);
            for (int i = 0; i < _segments.Count; i++)
                if (meters >= _segments[i].startM && meters < _segments[i].endM)
                    return _segments[i];
            return _segments[_segments.Count - 1];
        }
    }
}
