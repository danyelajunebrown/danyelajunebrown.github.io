// FeelsTint.shader — The Feels · full-FOV colour wash for passthrough MR.
// URP-native, unlit, transparent, ALWAYS drawn (ZTest Always / no ZWrite), so a
// single quad parented in front of the eye uniformly tints the passthrough feed.
// Lives under Resources/ so it's guaranteed included in the APK (no stripping).
Shader "TheFeels/Tint"
{
    Properties
    {
        _Color ("Tint (rgb + alpha)", Color) = (0,0,0,0)
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
            Name "FeelsTint"
            Cull Off
            ZWrite Off
            ZTest Always
            Blend SrcAlpha OneMinusSrcAlpha

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings   { float4 positionCS : SV_POSITION; };

            Varyings vert (Attributes IN)
            {
                Varyings OUT;
                OUT.positionCS = TransformObjectToHClip(IN.positionOS.xyz);
                return OUT;
            }

            half4 frag (Varyings IN) : SV_Target
            {
                return _Color;
            }
            ENDHLSL
        }
    }
    Fallback Off
}
