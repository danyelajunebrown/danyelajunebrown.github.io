// FeelsDepthSetup.cs — one-shot HEADLESS enablement for the Meta Depth API.
// -----------------------------------------------------------------------------
// Turns on the "Meta Quest: Occlusion" OpenXR feature (AROcclusionFeature) for
// Android WITHOUT opening the Unity GUI. That feature is the gate that makes
// EnvironmentDepthManager.IsSupported return true at runtime (it creates the
// XROcclusionSubsystem that the Depth API reads from). Everything else the depth
// path needs is already in the project; this just flips the one switch.
//
// Run it like:
//   UNITY=/Applications/Unity/Hub/Editor/6000.0.76f1/Unity.app/Contents/MacOS/Unity
//   "$UNITY" -batchmode -quit \
//            -projectPath "<this Unity project>" \
//            -executeMethod FeelsDepthSetup.Enable \
//            -logFile /tmp/feels_depthsetup.log
//
// Exits 0 if the feature is found AND enabled, 1 otherwise (so the shell can tell
// whether it worked). Idempotent: safe to run repeatedly.
using UnityEditor;
using UnityEditor.XR.OpenXR.Features;
using UnityEngine;

public static class FeelsDepthSetup
{
    // The Meta Depth API (OpenXR path) needs BOTH of these features enabled.
    // Occlusion creates the depth/occlusion subsystem; Session is its required
    // dependency (OpenXR build validation hard-fails the build without it).
    static readonly string[] RequiredFeatureIds =
    {
        "com.unity.openxr.feature.arfoundation-meta-occlusion", // "Meta Quest: Occlusion"
        "com.unity.openxr.feature.arfoundation-meta-session",   // "Meta Quest: Session"
    };

    public static void Enable()
    {
        // Make sure the OpenXR settings asset knows about every installed feature
        // for the Android build target before we go looking for ours.
        FeatureHelpers.RefreshFeatures(BuildTargetGroup.Android);

        bool allOk = true;
        bool changed = false;

        foreach (string id in RequiredFeatureIds)
        {
            var f = FeatureHelpers.GetFeatureWithIdForBuildTarget(BuildTargetGroup.Android, id);
            if (f == null)
            {
                Debug.LogError("[FeelsDepthSetup] FAILED: feature not found for Android (id=" + id
                               + "). Is com.unity.xr.meta-openxr installed?");
                allOk = false;
                continue;
            }

            if (!f.enabled)
            {
                f.enabled = true;
                EditorUtility.SetDirty(f);
                changed = true;
                Debug.Log("[FeelsDepthSetup] enabled '" + f.name + "' (" + id + ") for Android.");
            }
            else
            {
                Debug.Log("[FeelsDepthSetup] '" + f.name + "' already enabled for Android (no-op).");
            }
        }

        if (changed)
        {
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[FeelsDepthSetup] saved OpenXR settings.");
        }

        Debug.Log("[FeelsDepthSetup] DONE allFound=" + allOk);
        EditorApplication.Exit(allOk ? 0 : 1);
    }
}
