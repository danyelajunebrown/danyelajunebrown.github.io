// FeelsBuild.cs — one-shot HEADLESS Android build for The Feels (Quest 3S).
// Lets us rebuild the APK from a single terminal command, no GUI clicking and
// no dependence on the flaky external SSD. Run it like:
//
//   UNITY=/Applications/Unity/Hub/Editor/6000.0.76f1/Unity.app/Contents/MacOS/Unity
//   "$UNITY" -batchmode -quit \
//            -projectPath "<this Unity project>" \
//            -buildTarget Android \
//            -executeMethod FeelsBuild.Android \
//            -logFile /tmp/feels_build.log
//
// Output APK defaults to ~/Desktop/TheFeels.apk; override the directory with the
// FEELS_OUT environment variable. Exits 0 on success, 1 on failure (so the shell
// can tell whether the build worked).
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class FeelsBuild
{
    public static void Android()
    {
        string[] scenes = EditorBuildSettings.scenes
            .Where(s => s.enabled)
            .Select(s => s.path)
            .ToArray();

        string outDir = System.Environment.GetEnvironmentVariable("FEELS_OUT");
        if (string.IsNullOrEmpty(outDir)) outDir = "/Users/danyelabrown/Desktop";
        string outPath = Path.Combine(outDir, "TheFeels.apk");

        var opts = new BuildPlayerOptions
        {
            scenes = scenes,
            locationPathName = outPath,
            target = BuildTarget.Android,
            targetGroup = BuildTargetGroup.Android,
            options = BuildOptions.None,
        };

        Debug.Log("[FeelsBuild] starting Android build -> " + outPath
                  + "  scenes=[" + string.Join(", ", scenes) + "]");

        BuildReport report = BuildPipeline.BuildPlayer(opts);
        BuildSummary s = report.summary;

        Debug.Log("[FeelsBuild] result=" + s.result
                  + " errors=" + s.totalErrors
                  + " warnings=" + s.totalWarnings
                  + " sizeBytes=" + s.totalSize
                  + " time=" + s.totalTime
                  + " out=" + s.outputPath);

        EditorApplication.Exit(s.result == BuildResult.Succeeded ? 0 : 1);
    }
}
