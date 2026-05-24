// Service Culture Circle - Process Audio Edge Function
// Transcribes audio (Deepgram or AssemblyAI), stores segments, deletes audio.
//
// Body params:
//   interview_id (required)
//   audio_path   (required)  - storage key in `interview-audio` bucket
//   provider     ('deepgram' | 'assemblyai', default 'deepgram')
//   forced_speaker_label (optional) - when set, skip diarization and label
//       every segment with this string. Used for Zoom per-participant files
//       where speaker identity is already known.
//   finalize     (default true) - if false, only insert segments + delete
//       audio; do NOT update interview metadata (word_count, status, etc.).
//       Zoom orchestrator passes false per file, then finalizes at the end.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })

  const SUPABASE_URL         = Deno.env.get('SUPABASE_URL')!
  const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  const DEEPGRAM_API_KEY     = Deno.env.get('DEEPGRAM_API_KEY')
  const ASSEMBLYAI_API_KEY   = Deno.env.get('ASSEMBLYAI_API_KEY')

  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return json({ error: 'Missing Supabase env vars' }, 500)
  }
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

  let interview_id: string | undefined
  try {
    const body = await req.json()
    interview_id = body.interview_id
    const audio_path: string = body.audio_path
    const provider: 'deepgram' | 'assemblyai' = body.provider ?? 'deepgram'
    const forced_speaker_label: string | undefined = body.forced_speaker_label
    const finalize: boolean = body.finalize !== false

    if (!interview_id || !audio_path) throw new Error('Missing interview_id or audio_path')
    if (provider === 'deepgram'   && !DEEPGRAM_API_KEY)   throw new Error('DEEPGRAM_API_KEY not set')
    if (provider === 'assemblyai' && !ASSEMBLYAI_API_KEY) throw new Error('ASSEMBLYAI_API_KEY not set')

    console.log(`Processing interview ${interview_id} via ${provider} (finalize=${finalize})`)

    await supabase.from('interviews')
      .update({ processing_status: 'transcribing', transcription_provider: provider })
      .eq('id', interview_id)

    const { data: audioData, error: downloadError } = await supabase
      .storage.from('interview-audio').download(audio_path)
    if (downloadError) throw new Error(`Download failed: ${downloadError.message}`)

    // ---- Transcribe ----
    const result = provider === 'assemblyai'
      ? await transcribeAssemblyAI(audioData, ASSEMBLYAI_API_KEY!, !!forced_speaker_label)
      : await transcribeDeepgram(audioData,   DEEPGRAM_API_KEY!,   !!forced_speaker_label)

    // ---- Determine next sequence_order so multi-file (Zoom) imports stack ----
    const { count: existingCount } = await supabase
      .from('transcript_segments')
      .select('*', { count: 'exact', head: true })
      .eq('interview_id', interview_id)
    const baseOrder = existingCount ?? 0

    const segments = result.utterances.map((u, idx) => ({
      interview_id,
      speaker_label: forced_speaker_label ?? `Speaker ${u.speaker + 1}`,
      start_time_ms: Math.round(u.start * 1000),
      end_time_ms:   Math.round(u.end   * 1000),
      content:       u.text,
      confidence:    u.confidence,
      sequence_order: baseOrder + idx,
    }))

    if (segments.length > 0) {
      const { error: insertError } = await supabase.from('transcript_segments').insert(segments)
      if (insertError) throw new Error(`Insert failed: ${insertError.message}`)
    }

    // ---- Delete audio (IRB) ----
    const { error: deleteError } = await supabase
      .storage.from('interview-audio').remove([audio_path])
    if (deleteError) console.error(`Warning: failed to delete audio: ${deleteError.message}`)

    // ---- Finalize interview metadata (unless caller will do it) ----
    if (finalize) {
      const speakerLabels = [...new Set(segments.map(s => s.speaker_label))]
      const wordCount = segments.reduce((a, s) => a + (s.content?.split(/\s+/).length || 0), 0)
      await supabase.from('interviews').update({
        processing_status: 'pending_review',
        audio_deleted:    !deleteError,
        audio_deleted_at: !deleteError ? new Date().toISOString() : null,
        duration_seconds: Math.round(result.duration),
        speaker_count:    speakerLabels.length,
        word_count:       wordCount,
      }).eq('id', interview_id)
    }

    await supabase.from('audit_logs').insert({
      actor_type: 'system',
      action: 'audio_processed',
      resource_type: 'interview',
      resource_id: interview_id,
      details: {
        provider,
        forced_speaker_label: forced_speaker_label ?? null,
        finalize,
        segments: segments.length,
        duration_seconds: result.duration,
      },
    })

    return json({
      success: true,
      interview_id,
      provider,
      segments: segments.length,
      speakers: [...new Set(segments.map(s => s.speaker_label))].length,
      duration: result.duration,
    })
  } catch (error) {
    const msg = errMsg(error)
    console.error('Processing error:', msg)
    if (interview_id) {
      try {
        await supabase.from('interviews')
          .update({ processing_status: 'failed', error_message: msg })
          .eq('id', interview_id)
      } catch (_) { /* best-effort */ }
    }
    return json({ error: msg }, 500)
  }

  function json(obj: unknown, status = 200) {
    return new Response(JSON.stringify(obj), {
      status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})

function errMsg(e: unknown): string {
  if (e instanceof Error) return e.message
  if (typeof e === 'string') return e
  try { return JSON.stringify(e) } catch { return String(e) }
}

// ============================================================================
// Transcription provider adapters - both return a normalized shape.
// ============================================================================
interface NormalizedResult {
  duration: number
  utterances: Array<{ speaker: number; start: number; end: number; text: string; confidence: number }>
}

async function transcribeDeepgram(audio: Blob, apiKey: string, skipDiarize: boolean): Promise<NormalizedResult> {
  const params = new URLSearchParams({
    model: 'nova-2', punctuate: 'true', utterances: 'true', smart_format: 'true',
    diarize: skipDiarize ? 'false' : 'true',
  })
  const res = await fetch(`https://api.deepgram.com/v1/listen?${params}`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${apiKey}`, 'Content-Type': audio.type || 'audio/mpeg' },
    body: audio,
  })
  if (!res.ok) throw new Error(`Deepgram error: ${await res.text()}`)
  const j = await res.json()
  const utts = j.results?.utterances ?? []
  return {
    duration: j.metadata?.duration ?? 0,
    utterances: utts.map((u: any) => ({
      speaker: skipDiarize ? 0 : (u.speaker ?? 0),
      start: u.start, end: u.end, text: u.transcript, confidence: u.confidence,
    })),
  }
}

async function transcribeAssemblyAI(audio: Blob, apiKey: string, skipDiarize: boolean): Promise<NormalizedResult> {
  // 1. Upload bytes
  const uploadRes = await fetch('https://api.assemblyai.com/v2/upload', {
    method: 'POST',
    headers: { 'authorization': apiKey, 'content-type': 'application/octet-stream' },
    body: audio,
  })
  if (!uploadRes.ok) throw new Error(`AssemblyAI upload: ${await uploadRes.text()}`)
  const { upload_url } = await uploadRes.json()

  // 2. Request transcription
  const startRes = await fetch('https://api.assemblyai.com/v2/transcript', {
    method: 'POST',
    headers: { 'authorization': apiKey, 'content-type': 'application/json' },
    body: JSON.stringify({
      audio_url: upload_url,
      speaker_labels: !skipDiarize,
      punctuate: true,
      format_text: true,
    }),
  })
  if (!startRes.ok) throw new Error(`AssemblyAI start: ${await startRes.text()}`)
  const { id } = await startRes.json()

  // 3. Poll until done (cap ~5 min)
  for (let i = 0; i < 100; i++) {
    await new Promise(r => setTimeout(r, 3000))
    const pr = await fetch(`https://api.assemblyai.com/v2/transcript/${id}`, {
      headers: { 'authorization': apiKey },
    })
    const t = await pr.json()
    if (t.status === 'error')     throw new Error(`AssemblyAI: ${t.error}`)
    if (t.status === 'completed') {
      // AssemblyAI returns either `utterances` (when speaker_labels=true) or
      // `words`. Normalize to utterance-shaped output.
      if (Array.isArray(t.utterances) && t.utterances.length) {
        const labelToIdx = new Map<string, number>()
        return {
          duration: (t.audio_duration ?? 0),
          utterances: t.utterances.map((u: any) => {
            if (!labelToIdx.has(u.speaker)) labelToIdx.set(u.speaker, labelToIdx.size)
            return {
              speaker: labelToIdx.get(u.speaker)!,
              start: u.start / 1000, end: u.end / 1000,
              text: u.text, confidence: u.confidence,
            }
          }),
        }
      }
      // Fallback: single utterance covering full transcript
      return {
        duration: t.audio_duration ?? 0,
        utterances: t.text ? [{
          speaker: 0, start: 0, end: t.audio_duration ?? 0,
          text: t.text, confidence: t.confidence ?? 0,
        }] : [],
      }
    }
  }
  throw new Error('AssemblyAI: timed out waiting for transcript')
}
