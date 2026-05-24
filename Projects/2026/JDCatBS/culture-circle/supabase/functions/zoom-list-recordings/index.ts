// Lists the study lead's recent Zoom cloud recordings (last 30 days by default).
// Returns the minimum the dashboard needs to render a list + import button.
//
// Body params:
//   from (optional, YYYY-MM-DD)   default = 30 days ago
//   to   (optional, YYYY-MM-DD)   default = today

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { getZoomToken, zoomGet } from "../_shared/zoom.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })

  try {
    const body = req.method === 'POST' ? await req.json().catch(() => ({})) : {}
    const today = new Date()
    const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
    const from = body.from ?? monthAgo.toISOString().slice(0, 10)
    const to   = body.to   ?? today.toISOString().slice(0, 10)

    const token = await getZoomToken()
    const data = await zoomGet(`/users/me/recordings?from=${from}&to=${to}&page_size=100`, token)

    // Surface only what we need; per-participant audio is recording_type
    // 'audio_only' with multiple files keyed by participant.
    const meetings = (data.meetings ?? []).map((m: any) => ({
      uuid: m.uuid,
      id: String(m.id),
      topic: m.topic,
      start_time: m.start_time,
      duration: m.duration,
      total_size: m.total_size,
      recording_files: (m.recording_files ?? []).map((f: any) => ({
        id: f.id,
        recording_type: f.recording_type,
        file_type: f.file_type,
        file_extension: f.file_extension,
        file_size: f.file_size,
        download_url: f.download_url,
        participant_audio_user_name: f.participant_audio_user_name ?? null,
      })),
    }))

    return json({ from, to, meetings })
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error)
    console.error('zoom-list-recordings error:', msg)
    return json({ error: msg }, 500)
  }

  function json(obj: unknown, status = 200) {
    return new Response(JSON.stringify(obj), {
      status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
