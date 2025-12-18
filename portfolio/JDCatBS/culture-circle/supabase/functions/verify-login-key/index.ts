// Service Culture Circle - Verify Login Key Edge Function
// Verifies participant login key and returns session info

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Rate limiting: 5 attempts per minute per IP
const rateLimitMap = new Map<string, number[]>()
const RATE_LIMIT = 5
const RATE_WINDOW_MS = 60000

function checkRateLimit(ip: string): boolean {
  const now = Date.now()
  const attempts = rateLimitMap.get(ip) || []
  const recentAttempts = attempts.filter((t: number) => now - t < RATE_WINDOW_MS)

  if (recentAttempts.length >= RATE_LIMIT) {
    return false
  }

  recentAttempts.push(now)
  rateLimitMap.set(ip, recentAttempts)
  return true
}

async function hashKey(key: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(key)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
  const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return new Response(
      JSON.stringify({ error: 'Server configuration error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  // Get client IP for rate limiting
  const clientIP = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
                   req.headers.get('cf-connecting-ip') ||
                   'unknown'

  // Check rate limit
  if (!checkRateLimit(clientIP)) {
    return new Response(
      JSON.stringify({ error: 'Too many login attempts. Please try again later.' }),
      { status: 429, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

  try {
    const { login_key } = await req.json()

    if (!login_key) {
      throw new Error('Missing login key')
    }

    // Hash the key
    const keyHash = await hashKey(login_key.toUpperCase())

    // Find participant by key hash
    const { data: participant, error: fetchError } = await supabase
      .from('participants')
      .select('id, name, email, status')
      .eq('login_key_hash', keyHash)
      .single()

    if (fetchError || !participant) {
      // Log failed attempt
      await supabase.from('audit_logs').insert({
        actor_type: 'system',
        action: 'login_failed',
        resource_type: 'auth',
        details: { reason: 'invalid_key', ip: clientIP }
      })

      return new Response(
        JSON.stringify({ error: 'Invalid access key' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    if (participant.status === 'suspended') {
      await supabase.from('audit_logs').insert({
        actor_type: 'participant',
        actor_id: participant.id,
        action: 'login_blocked',
        resource_type: 'auth',
        details: { reason: 'suspended', ip: clientIP }
      })

      return new Response(
        JSON.stringify({ error: 'Account suspended. Please contact the study lead.' }),
        { status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Check consent status
    const { data: consent } = await supabase
      .from('consent_records')
      .select('id')
      .eq('participant_id', participant.id)
      .is('withdrawal_at', null)
      .single()

    // Update last login
    await supabase
      .from('participants')
      .update({
        last_login: new Date().toISOString(),
        status: 'active'
      })
      .eq('id', participant.id)

    // Log successful login
    await supabase.from('audit_logs').insert({
      actor_type: 'participant',
      actor_id: participant.id,
      action: 'login',
      resource_type: 'participant',
      resource_id: participant.id,
      ip_address: clientIP,
      user_agent: req.headers.get('user-agent')
    })

    // Generate simple session token (for client-side validation)
    const sessionToken = crypto.randomUUID()

    return new Response(
      JSON.stringify({
        success: true,
        participant: {
          id: participant.id,
          name: participant.name,
          email: participant.email
        },
        needs_consent: !consent,
        session_token: sessionToken
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
