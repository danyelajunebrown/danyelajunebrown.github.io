// FeelsExperience.cs — The Feels · Quest 3 native (passthrough + DEPTH tint)
// -----------------------------------------------------------------------------
// Builds on the passed smoke test. Every frame this:
//   • accumulates horizontal head movement -> metres walked (clamped 0..445.8),
//   • asks FeelsDataLoader.SegmentAtMeters(metres) which emotion you're "inside",
//   • paints that emotion's colour onto the passthrough view, and
//   • shows an in-headset debug readout AND logs a heartbeat to adb logcat
//     (filter on the device with:  adb logcat -s Unity:* | grep FeelsXP ).
//
// NEW — Meta DEPTH API tint:
//   Instead of a flat film of colour over the whole lens, the colour is painted
//   onto the ACTUAL real-world surfaces you can see (FeelsDepthTint.shader reads
//   Meta's environment-depth texture). Nearby surfaces get the strongest tint and
//   it fades out by `tintReachMeters`; empty space stays clear passthrough.
//   While depth is still warming up (or on a device without depth) the SAME shader
//   falls back to the proven flat wash, so the piece is never blank.
//
// This script stands up the Depth API itself: it requests the Scene permission and
// creates one EnvironmentDepthManager once the XR occlusion subsystem reports ready.
// The Meta "Camera Rig + Passthrough" Building Block still provides the rig; this
// just finds Camera.main (its centre-eye camera) and paints over it.
//
// SETUP: drop this ONE component on an empty GameObject. It auto-adds
// FeelsDataLoader (the Supabase/segment data layer). Nothing else to wire.
//
// TUNING for the smoke test: in the Inspector set "Meters Scale" to ~20 so the
// colours visibly cycle while you pace a small room. Set it back to 1 for the
// real install (walk the true 445.8 m).
// -----------------------------------------------------------------------------

using System.Collections;
using UnityEngine;
using UnityEngine.Android;
using Meta.XR.EnvironmentDepth;

namespace TheFeels
{
    [RequireComponent(typeof(FeelsDataLoader))]
    public class FeelsExperience : MonoBehaviour
    {
        [Header("Tuning (safe to tweak in the Inspector)")]
        [Tooltip("Multiplies real metres walked.\n1 = walk the true 445.8 m path.\nSmoke test in a small room: set ~20 so colours cycle as you pace.")]
        public float metersScale = 1f;

        [Tooltip("Distance of the colour wash in front of your eyes (m). Cosmetic.")]
        public float washDistance = 1.0f;

        [Tooltip("Show the in-headset debug readout (feeling / metres / intensity).")]
        public bool showDebug = true;

        [Header("Depth tint (Meta Depth API)")]
        [Tooltip("How far the emotion colour reaches onto REAL surfaces (metres). Surfaces nearer than this get painted; the tint fades to clear by this distance. Bigger = more of the room tinted. Ignored until depth is live (then it replaces the flat wash).")]
        public float tintReachMeters = 8f;

        [Tooltip("Floor for the depth tint so the emotion colour is NEVER fully blank: 0 = empty space stays clear passthrough (purest depth look, but can show nothing if depth drops out), 1 = whole view always washed. Near surfaces always rise above this toward full strength when depth is computing.")]
        [Range(0f, 1f)]
        public float minTint = 0.6f;

        FeelsDataLoader _loader;
        Transform _head;
        Material _tintMat;
        TextMesh _debug;

        Vector3 _lastHeadPos;
        bool _haveLastPos;
        float _meters;

        string _lastFeeling = "";
        float _logTimer;

        bool _depthReady;   // EnvironmentDepthManager has been created

        IEnumerator Start()
        {
            // Depth API needs the Scene permission. EnvironmentDepthManager re-checks
            // for the grant every frame and self-heals once it lands, but it does NOT
            // request it — we do, here, up front.
            RequestScenePermission();

            // RequireComponent normally guarantees this, but if the loader couldn't be
            // added in-editor (e.g. it was authored in a mis-named file before the split),
            // self-heal at runtime so the scene works regardless of how it was wired.
            _loader = GetComponent<FeelsDataLoader>();
            if (_loader == null) _loader = gameObject.AddComponent<FeelsDataLoader>();
            Debug.Log("[FeelsXP] loading diary entries from Supabase…");
            yield return StartCoroutine(_loader.Load());
            var segs = _loader.Segments;
            Debug.Log("[FeelsXP] ready: " + (segs != null ? segs.Count : 0)
                      + " segments over " + FeelsPath.LengthMeters.ToString("F1") + " m");
        }

        void Update()
        {
            // Stand up the Depth API as soon as the XR occlusion subsystem reports it's
            // supported (a few frames after launch). Until then we run the flat wash.
            TryEnsureEnvironmentDepth();

            // The Meta rig's centre-eye camera may take a frame to appear.
            if (_head == null)
            {
                Camera cam = Camera.main;
                if (cam == null) return;
                _head = cam.transform;
                _lastHeadPos = _head.position;
                _haveLastPos = true;
                BuildVisuals();
                Debug.Log("[FeelsXP] head camera found: " + cam.name);
            }

            // --- ODOMETER: accumulate horizontal (XZ) head displacement ---
            Vector3 p = _head.position;
            if (_haveLastPos)
            {
                Vector3 d = p - _lastHeadPos;
                d.y = 0f;
                _meters = Mathf.Clamp(_meters + d.magnitude * metersScale, 0f, FeelsPath.LengthMeters);
            }
            _lastHeadPos = p;
            _haveLastPos = true;

            FeelingSegment seg = _loader.SegmentAtMeters(_meters);

            // --- TINT the passthrough view ---
            if (_tintMat != null)
            {
                Color c = seg.color;
                c.a = seg.opacity;
                _tintMat.SetColor("_Color", c);
            }

            // --- in-headset readout ---
            if (_debug != null)
            {
                if (_debug.gameObject.activeSelf != showDebug) _debug.gameObject.SetActive(showDebug);
                if (showDebug)
                {
                    string f = string.IsNullOrEmpty(seg.feeling) ? "(loading…)" : seg.feeling;
                    _debug.text = f
                        + "\nintensity " + seg.intensity
                        + "   ·   wash " + Mathf.RoundToInt(seg.opacity * 100f) + "%"
                        + "\nodometer " + _meters.ToString("F1") + " / "
                        + FeelsPath.LengthMeters.ToString("F1") + " m"
                        + "\ndepth " + (_depthReady ? "on" : "warming…");
                }
            }

            // --- adb logcat heartbeat (lets me verify on-device behaviour) ---
            _logTimer += Time.deltaTime;
            if (seg.feeling != _lastFeeling)
            {
                _lastFeeling = seg.feeling;
                Debug.Log("[FeelsXP] @ " + _meters.ToString("F1") + "m -> '" + seg.feeling
                          + "' i" + seg.intensity + " a" + seg.opacity.ToString("F2")
                          + " rgb(" + Mathf.RoundToInt(seg.color.r * 255f) + ","
                          + Mathf.RoundToInt(seg.color.g * 255f) + ","
                          + Mathf.RoundToInt(seg.color.b * 255f) + ")");
            }
            else if (_logTimer >= 2f)
            {
                _logTimer = 0f;
                Debug.Log("[FeelsXP] walking… " + _meters.ToString("F1") + "m  '" + seg.feeling
                          + "'  depth=" + (_depthReady ? "on" : "off"));
            }
        }

        void BuildVisuals()
        {
            // --- colour-wash quad: parented to the head, always-on-top, fills FOV ---
            // Depth-driven tint (paints REAL surfaces via Meta's depth texture). Falls
            // back to the proven flat wash shader if the depth shader isn't in the build.
            Shader sh = Resources.Load<Shader>("FeelsDepthTint");
            if (sh == null) sh = Shader.Find("TheFeels/DepthTint");
            if (sh == null) sh = Resources.Load<Shader>("FeelsTint");
            if (sh == null) sh = Shader.Find("TheFeels/Tint");
            _tintMat = new Material(sh) { name = "FeelsTintMat" };
            _tintMat.SetColor("_Color", new Color(0f, 0f, 0f, 0f));
            if (_tintMat.HasProperty("_MaxDist"))   _tintMat.SetFloat("_MaxDist", Mathf.Max(0.1f, tintReachMeters));
            if (_tintMat.HasProperty("_FlatFloor")) _tintMat.SetFloat("_FlatFloor", 1f);
            if (_tintMat.HasProperty("_MinTint"))   _tintMat.SetFloat("_MinTint", Mathf.Clamp01(minTint));
            _tintMat.renderQueue = 4000;

            GameObject quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
            quad.name = "FeelsTintWash";
            Collider col = quad.GetComponent<Collider>();
            if (col != null) Destroy(col);

            MeshRenderer mr = quad.GetComponent<MeshRenderer>();
            mr.sharedMaterial = _tintMat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            mr.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
            mr.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;

            Transform qt = quad.transform;
            qt.SetParent(_head, false);
            qt.localPosition = new Vector3(0f, 0f, washDistance);
            qt.localRotation = Quaternion.identity;
            qt.localScale = new Vector3(40f, 40f, 1f); // huge; ZTest Always = never clipped

            // --- in-headset debug text: parented to head, facing back at the eye ---
            GameObject go = new GameObject("FeelsDebug");
            Transform tt = go.transform;
            tt.SetParent(_head, false);
            tt.localPosition = new Vector3(0f, -0.28f, 0.8f);
            // A TextMesh's READABLE face points down its local -Z. Parented to the
            // head and placed at +Z in front of the eye, that -Z face is ALREADY
            // looking back at the eye, so identity = upright, front-facing, readable.
            // The old Euler(0,180,0) (meant to "face the eye") spun the readable face
            // AWAY -> the eye saw the BACK of the glyphs through the double-sided font
            // shader = mirror-flipped text. Identity fixes the flip.
            tt.localRotation = Quaternion.identity;
            tt.localScale = Vector3.one;

            _debug = go.AddComponent<TextMesh>();
            _debug.text = "(loading…)";
            _debug.anchor = TextAnchor.MiddleCenter;
            _debug.alignment = TextAlignment.Center;
            _debug.fontSize = 100;
            _debug.characterSize = 0.02f;
            _debug.color = Color.white;

            Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (font != null)
            {
                _debug.font = font;
                MeshRenderer dmr = go.GetComponent<MeshRenderer>();
                Material tm = new Material(font.material);
                tm.renderQueue = 4100; // draw OVER the wash
                dmr.sharedMaterial = tm;
            }
        }

        // --- Depth API plumbing ------------------------------------------------

        // Ask the OS for the Scene permission the Depth API requires. The
        // EnvironmentDepthManager polls for the grant every frame and switches the
        // depth texture + occlusion keyword on by itself once it lands.
        void RequestScenePermission()
        {
            if (Application.platform != RuntimePlatform.Android) return;
            const string perm = "com.oculus.permission.USE_SCENE";
            if (Permission.HasUserAuthorizedPermission(perm))
            {
                Debug.Log("[FeelsXP] Scene permission already granted.");
                return;
            }
            Debug.Log("[FeelsXP] requesting Scene permission (Depth API)…");
            Permission.RequestUserPermission(perm);
        }

        // Create exactly one EnvironmentDepthManager once the XR occlusion subsystem
        // is up. HardOcclusion = the lighter path (no soft-edge preprocessing); our
        // shader only needs the raw depth texture, which both modes publish.
        void TryEnsureEnvironmentDepth()
        {
            if (_depthReady) return;
            if (!EnvironmentDepthManager.IsSupported) return; // not yet / unsupported -> flat wash
            if (FindAnyObjectByType<EnvironmentDepthManager>() != null) { _depthReady = true; return; }

            var go = new GameObject("FeelsEnvironmentDepth");
            var mgr = go.AddComponent<EnvironmentDepthManager>();
            mgr.OcclusionShadersMode = OcclusionShadersMode.HardOcclusion;
            _depthReady = true;
            Debug.Log("[FeelsXP] EnvironmentDepthManager created (HardOcclusion). "
                      + "Depth tint engages once Scene permission + first depth frame land.");
        }
    }
}
