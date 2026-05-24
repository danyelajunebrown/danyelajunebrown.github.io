// Imports a single Zoom meeting's per-participant audio files as ONE interview,
// transcribing each file separately with the speaker label = participant name.
// No acoustic diarization required.
//
// Body params:
//   meeting_uuid (required)  - Zoom meeting UUID
//   provider     ('deepgram' | 'assemblyai', default 'deepgram')
//   uploaded_by  (required, uuid) - auth.users.id of the importer
//
// Requires Zoom recording setting "Record a separate audio file for each
// participant" to be ON; otherwise there's only one mixed file and we fall
// back to ordinary diarization on that.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { getZoomToken, zoomGet } from "../_shared/zoom.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })

  const SUPABASE_URL         = Deno.env.get('SUPABASE_URL')!
  const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

  let interviewId: string | undefined
  try {
    const body = await req.json()
    const meetingUuid: string = body.meeting_uuid
    const provider: 'deepgram' | 'assemblyai' = body.provider ?? 'deepgram'
    const uploadedBy: string = body.uploaded_by
    if (!meetingUuid || !uploadedBy) throw new Error('meeting_uuid and uploaded_by are required')

    const token = await getZoomToken()

    // Zoom requires double-URL-encoding when a meeting UUID contains / or +.
    const safeUuid = encodeURIComponent(encodeURIComponent(meetingUuid))
    const meeting = await zoomGet(`/meetings/${safeUuid}/recordings`, token)

    const audioFiles = (meeting.recording_files ?? []).filter((f: any) =>
      f.recording_type === 'audio_only' && (f.file_extension === 'M4A' || f.file_extension === 'MP3')
    )
    if (!audioFiles.length) throw new Error('No audio recording files on this meeting')

    // Per-participant files have participant_audio_user_name set; pick those if
    // present, else fall back to the single mixed file.
    const perParticipant = audioFiles.filter((f: any) => f.participant_audio_user_name)
    const filesToProcess = perParticipant.length ? perParticipant : audioFiles
    const useForcedLabels = perParticipant.length > 0

    // Create the interview row (or reuse if we already imported this meeting)
    const { data: existing } = await supabase.from('interviews')
      .select('id').eq('zoom_meeting_uuid', meetingUuid).maybeSingle()
    if (existing) {
      return json({ error: 'Meeting already imported', interview_id: existing.id }, 409)
    }

    const { data: interview, error: insertErr } = await supabase.from('interviews')
      .insert({
        title: meeting.topic || `Zoom meeting ${meeting.id}`,
        description: useForcedLabels
          ? `Zoom import; ${filesToProcess.length} per-participant audio files`
          : `Zoom import; single mixed-audio file (diarized)`,
        recorded_at: meeting.start_time,
        uploaded_by: uploadedBy,
        processing_status: 'uploaded',
        zoom_meeting_uuid: meetingUuid,
        zoom_meeting_id: String(meeting.id),
        zoom_topic: meeting.topic,
        zoom_start_time: meeting.start_time,
        transcription_provider: provider,
      }).select().single()
    if (insertErr) throw new Error(`Create interview: ${insertErr.message}`)
    interviewId = interview.id

    // Download each Zoom file, upload to our bucket, then call process-audio.
    let totalSegments = 0
    let totalDuration = 0
    const speakerLabels = new Set<string>()

    for (const f of filesToProcess) {
      const label = f.participant_audio_user_name || 'Speaker'
      speakerLabels.add(label)

      // Zoom download URLs require the bearer token
      const dl = await fetch(`${f.download_url}?access_token=${token}`)
      if (!dl.ok) throw new Error(`Zoom download ${f.id}: ${dl.status}`)
      const blob = await dl.blob()

      const safeName = label.replace(/[^a-zA-Z0-9._-]/g, '_')
      const audioPath = `${interview.id}/${safeName}_${f.id}.${(f.file_extension || 'M4A').toLowerCase()}`

      const { error: upErr } = await supabase.storage
        .from('interview-audio').upload(audioPath, blob, { contentType: 'audio/mp4' })
      if (upErr) throw new Error(`Upload to storage: ${upErr.message}`)

      // Call process-audio with forced_speaker_label so no diarization is done.
      const res = await fetch(`${SUPABASE_URL}/functions/v1/process-audio`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          interview_id: interview.id,
          audio_path: audioPath,
          provider,
          forced_speaker_label: useForcedLabels ? label : undefined,
          finalize: false,
        }),
      })
      const out = await res.json()
      if (!res.ok || out.error) throw new Error(`process-audio (${label}): ${out.error ?? res.status}`)
      totalSegments += out.segments ?? 0
      totalDuration = Math.max(totalDuration, out.duration ?? 0)
    }

    // Finalize the interview now that all files have been transcribed.
    const { data: allSegs } = await supabase.from('transcript_segments')
      .select('content').eq('interview_id', interview.id)
    const wordCount = (allSegs ?? []).reduce(
      (a, s: any) => a + (s.content?.split(/\s+/).length || 0), 0)

    await supabase.from('interviews').update({
      processing_status: 'pending_review',
      audio_deleted: true, // process-audio deletes per file
      audio_deleted_at: new Date().toISOString(),
      duration_seconds: Math.round(totalDuration),
      speaker_count: speakerLabels.size,
      word_count: wordCount,
    }).eq('id', interview.id)

    await supabase.from('audit_logs').insert({
      actor_type: 'system',
      action: 'zoom_meeting_imported',
      resource_type: 'interview',
      resource_id: interview.id,
      details: {
        zoom_meeting_uuid: meetingUuid,
        files_processed: filesToProcess.length,
        per_participant: useForcedLabels,
        provider,
        speakers: [...speakerLabels],
      },
    })

    return json({
      success: true,
      interview_id: interview.id,
      files_processed: filesToProcess.length,
      per_participant: useForcedLabels,
      speakers: [...speakerLabels],
      segments: totalSegments,
    })
  } catch (error) {
    const msg = errMsg(error)
    console.error('zoom-import-recording error:', msg)
    if (interviewId) {
      try {
        await supabase.from('interviews')
          .update({ processing_status: 'failed', error_message: msg })
          .eq('id', interviewId)
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
