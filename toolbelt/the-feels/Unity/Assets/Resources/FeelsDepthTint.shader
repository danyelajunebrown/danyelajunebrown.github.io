// FeelsDepthTint.shader — The Feels · DEPTH-DRIVEN emotion tint for passthrough MR.
// -----------------------------------------------------------------------------
// The "real prize": instead of a flat film of colour over the whole lens, this
// paints the emotion colour onto the ACTUAL real-world surfaces you can see,
// using Meta's Environment Depth API. Nearby surfaces get the strongest tint and
// it fades out with distance; empty space / sky stays clear passthrough.
//
// HOW IT WORKS (per pixel):
//   1. reproject this fragment's world position into the environment-depth
//      texture (same matrices Meta's own occlusion shaders use),
//   2. read the REAL surface distance in metres at that screen direction,
//   3. tint alpha = emotion alpha * proximity( realDist, _MaxDist ).
//
// DEPTH-NOT-READY FALLBACK: the HARD_OCCLUSION / SOFT_OCCLUSION keyword is only
// switched on by EnvironmentDepthManager once depth is actually streaming (after
// the Scene permission is granted and the first depth frame lands). Until then we
// take the #else path and behave EXACTLY like the proven flat wash, so the piece
// never shows a blank passthrough while depth warms up.
//
// Lives under Resources/ so it's guaranteed packed into the APK (no stripping).
// Tuning lives on FeelsExperience (Inspector): tint distance + flat-wash floor.
Shader "TheFeels/DepthTint"
{
    Properties
    {
        _Color    ("Tint (rgb + alpha)", Color)            = (0,0,0,0)
        _MaxDist  ("Tint reach (m): surfaces nearer than this get tinted", Float) = 8.0
        _FlatFloor("Flat wash before depth is live (0..1)", Range(0,1))  = 1.0
        _MinTint  ("Min tint floor when depth is live (0 = clear empty space, 1 = full flat)", Range(0,1)) = 0.6
    }
    SubShader
    {
        Tags
        {
            "RenderPipeline"  = "UniversalPipeline"
            "RenderType"      = "Transparent"
            "Queue"           = "Overlay"
            "IgnoreProjector" = "True"
        }

        Pass
        {
            Name "FeelsDepthTint"
            Cull Off
            ZWrite Off
            ZTest Always
            // Match the proven smoke-test wash blend (tints passthrough correctly).
            Blend SrcAlpha OneMinusSrcAlpha

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            // Keyword is toggled GLOBALLY by EnvironmentDepthManager when depth is live.
            #pragma multi_compile _ HARD_OCCLUSION SOFT_OCCLUSION
            #pragma multi_compile_instancing

            // Pulls in URP Core, the _EnvironmentDepthTexture sampler, the
            // reprojection matrices, SampleEnvironmentDepthLinear(), and the
            // META_DEPTH_* vertex macros. Resolved by package name.
            #include "Packages/com.meta.xr.sdk.core/Shaders/EnvironmentDepth/URP/EnvironmentOcclusionURP.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4  _Color;
                float  _MaxDist;
                float  _FlatFloor;
                float  _MinTint;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                META_DEPTH_VERTEX_OUTPUT(0)          // adds float3 posWorld : TEXCOORD0 when depth keyword on
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert (Attributes IN)
            {
                Varyings OUT;
                UNITY_SETUP_INSTANCE_ID(IN);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(OUT);
                OUT.positionCS = TransformObjectToHClip(IN.positionOS.xyz);
                META_DEPTH_INITIALIZE_VERTEX_OUTPUT(OUT, IN.positionOS.xyz);
                return OUT;
            }

            half4 frag (Varyings IN) : SV_Target
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(IN);

                half4 col = _Color;

            #if defined(HARD_OCCLUSION) || defined(SOFT_OCCLUSION)
                // --- depth is LIVE: tint real surfaces by proximity ---
                float4 depthSpace =
                    mul(_EnvironmentDepthReprojectionMatrices[unity_StereoEyeIndex], float4(IN.posWorld, 1.0));
                float2 depthUv  = (depthSpace.xy / depthSpace.w + 1.0) * 0.5;
                float  realDist = SampleEnvironmentDepthLinear(depthUv);   // metres; 10000 = no surface
                // nearer than _MaxDist -> tint (1 at the surface, 0 at _MaxDist);
                // no surface (realDist huge) -> 0 -> clear passthrough.
                float  prox = saturate((_MaxDist - realDist) / _MaxDist);
                // NEVER fully blank: floor the tint at _MinTint. Near surfaces rise above
                // the floor toward full strength (the depth emphasis); empty space / sky and
                // the "depth enabled but 0 frames" case (realDist reads no-surface everywhere)
                // settle to _MinTint so the emotion colour is always visible.
                col.a *= max(prox, _MinTint);
            #else
                // --- depth NOT live yet: behave like the flat wash ---
                col.a *= _FlatFloor;
            #endif

                return col;
            }
            ENDHLSL
        }
    }
    Fallback Off
}
