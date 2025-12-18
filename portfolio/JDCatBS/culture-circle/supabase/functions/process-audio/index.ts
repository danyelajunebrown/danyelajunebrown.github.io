// Service Culture Circle - Process Audio Edge Function
// Transcribes audio using Deepgram, stores transcript, deletes audio

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const DEEPGRAM_API_KEY = Deno.env.get('DEEPGRAM_API_KEY')
  const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
  const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

  if (!DEEPGRAM_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return new Response(
      JSON.stringify({ error: 'Missing environment variables' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

  try {
    const { interview_id, audio_path } = await req.json()

    if (!interview_id || !audio_path) {
      throw new Error('Missing interview_id or audio_path')
    }

    console.log(`Processing interview ${interview_id}`)

    // 1. Update status to transcribing
    await supabase
      .from('interviews')
      .update({ processing_status: 'transcribing' })
      .eq('id', interview_id)

    // 2. Get audio file from storage
    const { data: audioData, error: downloadError } = await supabase
      .storage
      .from('interview-audio')
      .download(audio_path)

    if (downloadError) {
      throw new Error(`Failed to download audio: ${downloadError.message}`)
    }

    console.log(`Downloaded audio file: ${audio_path}`)

    // 3. Send to Deepgram with diarization
    const deepgramResponse = await fetch(
      'https://api.deepgram.com/v1/listen?model=nova-2&diarize=true&punctuate=true&utterances=true&smart_format=true',
      {
        method: 'POST',
        headers: {
          'Authorization': `Token ${DEEPGRAM_API_KEY}`,
          'Content-Type': audioData.type || 'audio/mpeg'
        },
        body: audioData
      }
    )

    if (!deepgramResponse.ok) {
      const errorText = await deepgramResponse.text()
      throw new Error(`Deepgram API error: ${errorText}`)
    }

    const transcript = await deepgramResponse.json()
    console.log(`Transcription complete. Duration: ${transcript.metadata?.duration}s`)

    // 4. Process utterances into segments
    const utterances = transcript.results?.utterances || []
    const segments = utterances.map((utt: any, idx: number) => ({
      interview_id,
      speaker_label: `Speaker ${utt.speaker + 1}`, // Deepgram uses 0-based indexing
      start_time_ms: Math.round(utt.start * 1000),
      end_time_ms: Math.round(utt.end * 1000),
      content: utt.transcript,
      confidence: utt.confidence,
      sequence_order: idx
    }))

    console.log(`Created ${segments.length} transcript segments`)

    // 5. Insert transcript segments
    if (segments.length > 0) {
      const { error: insertError } = await supabase
        .from('transcript_segments')
        .insert(segments)

      if (insertError) {
        throw new Error(`Failed to insert segments: ${insertError.message}`)
      }
    }

    // 6. Get unique speakers
    const speakerLabels = [...new Set(segments.map((s: any) => s.speaker_label))]

    // 7. DELETE the audio file permanently (IRB compliance)
    const { error: deleteError } = await supabase
      .storage
      .from('interview-audio')
      .remove([audio_path])

    if (deleteError) {
      console.error(`Warning: Failed to delete audio: ${deleteError.message}`)
      // Continue anyway - we can retry deletion later
    } else {
      console.log(`Audio file deleted: ${audio_path}`)
    }

    // 8. Update interview status
    const wordCount = segments.reduce((acc: number, seg: any) => {
      return acc + (seg.content?.split(/\s+/).length || 0)
    }, 0)

    await supabase
      .from('interviews')
      .update({
        processing_status: 'pending_review',
        audio_deleted: !deleteError,
        audio_deleted_at: !deleteError ? new Date().toISOString() : null,
        duration_seconds: Math.round(transcript.metadata?.duration || 0),
        speaker_count: speakerLabels.length,
        word_count: wordCount
      })
      .eq('id', interview_id)

    // 9. Log the action
    await supabase
      .from('audit_logs')
      .insert({
        actor_type: 'system',
        action: 'audio_processed',
        resource_type: 'interview',
        resource_id: interview_id,
        details: {
          duration_seconds: transcript.metadata?.duration,
          speaker_count: speakerLabels.length,
          segment_count: segments.length,
          word_count: wordCount,
          audio_deleted: !deleteError
        }
      })

    return new Response(
      JSON.stringify({
        success: true,
        interview_id,
        segments: segments.length,
        speakers: speakerLabels.length,
        duration: transcript.metadata?.duration
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Processing error:', error)

    // Try to update interview status to failed
    try {
      const { interview_id } = await req.json().catch(() => ({}))
      if (interview_id) {
        await supabase
          .from('interviews')
          .update({
            processing_status: 'failed',
            error_message: error.message
          })
          .eq('id', interview_id)
      }
    } catch (e) {
      console.error('Failed to update interview status:', e)
    }

    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
