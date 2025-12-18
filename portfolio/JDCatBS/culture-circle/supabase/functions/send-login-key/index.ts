// Service Culture Circle - Send Login Key Edge Function
// Sends login key to participant via SendGrid

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const SENDGRID_API_KEY = Deno.env.get('SENDGRID_API_KEY')
  const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
  const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
  const FROM_EMAIL = Deno.env.get('FROM_EMAIL') || 'noreply@serviceculturecircle.org'
  const FROM_NAME = Deno.env.get('FROM_NAME') || 'Service Culture Circle'

  if (!SENDGRID_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return new Response(
      JSON.stringify({ error: 'Missing environment variables' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

  try {
    const { participant_id, is_resend, interview_id } = await req.json()

    if (!participant_id) {
      throw new Error('Missing participant_id')
    }

    // Get participant
    const { data: participant, error: fetchError } = await supabase
      .from('participants')
      .select('*')
      .eq('id', participant_id)
      .single()

    if (fetchError || !participant) {
      throw new Error('Participant not found')
    }

    // Determine email type
    const notificationType = is_resend ? 'key_resent' : 'new_content'
    const loginKey = participant.login_key

    // Build email content
    let subject: string
    let htmlContent: string

    if (is_resend) {
      subject = 'Your Service Culture Circle Access Key'
      htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body { font-family: 'Courier New', monospace; background: #000; color: #fff; padding: 40px; }
            .container { max-width: 500px; margin: 0 auto; }
            h1 { color: #9370DB; font-size: 18px; }
            .key-box { background: #1a1a1a; border: 1px solid #333; padding: 20px; margin: 20px 0; text-align: center; }
            .key { font-size: 24px; color: #9370DB; letter-spacing: 2px; }
            a { color: #9370DB; }
            .footer { margin-top: 30px; font-size: 12px; color: #666; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Service Culture Circle</h1>
            <p>Hello ${participant.name},</p>
            <p>Here is your requested access key:</p>
            <div class="key-box">
              <span class="key">${loginKey}</span>
            </div>
            <p>Use this key to access your interview transcript portions at the participant portal.</p>
            <p>Please keep this key secure and do not share it with others.</p>
            <div class="footer">
              <p>If you did not request this, please contact the study lead immediately.</p>
            </div>
          </div>
        </body>
        </html>
      `
    } else {
      subject = 'You Have New Content - Service Culture Circle'
      htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body { font-family: 'Courier New', monospace; background: #000; color: #fff; padding: 40px; }
            .container { max-width: 500px; margin: 0 auto; }
            h1 { color: #9370DB; font-size: 18px; }
            .key-box { background: #1a1a1a; border: 1px solid #333; padding: 20px; margin: 20px 0; text-align: center; }
            .key { font-size: 24px; color: #9370DB; letter-spacing: 2px; }
            a { color: #9370DB; }
            .footer { margin-top: 30px; font-size: 12px; color: #666; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Service Culture Circle</h1>
            <p>Hello ${participant.name},</p>
            <p>New interview transcript content is available for you to view.</p>
            <p>Your unique access key:</p>
            <div class="key-box">
              <span class="key">${loginKey}</span>
            </div>
            <p>Use this key to access the participant portal and view your interview transcript portions.</p>
            <p><strong>Important:</strong> Before accessing your content, you will need to review and accept the research consent form.</p>
            <div class="footer">
              <p>If you have questions about this research, please contact the study lead.</p>
            </div>
          </div>
        </body>
        </html>
      `
    }

    // Send email via SendGrid
    const emailResponse = await fetch('https://api.sendgrid.com/v3/mail/send', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SENDGRID_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        personalizations: [{
          to: [{ email: participant.email, name: participant.name }]
        }],
        from: { email: FROM_EMAIL, name: FROM_NAME },
        subject: subject,
        content: [{
          type: 'text/html',
          value: htmlContent
        }]
      })
    })

    const status = emailResponse.ok ? 'sent' : 'failed'
    const errorMessage = emailResponse.ok ? null : await emailResponse.text()

    // Log notification
    await supabase
      .from('notifications')
      .insert({
        participant_id,
        type: notificationType,
        interview_id: interview_id || null,
        status,
        error_message: errorMessage
      })

    // Log audit
    await supabase
      .from('audit_logs')
      .insert({
        actor_type: 'system',
        action: is_resend ? 'login_key_resent' : 'login_key_sent',
        resource_type: 'participant',
        resource_id: participant_id,
        details: {
          email: participant.email,
          notification_type: notificationType,
          success: emailResponse.ok
        }
      })

    if (!emailResponse.ok) {
      throw new Error(`SendGrid error: ${errorMessage}`)
    }

    return new Response(
      JSON.stringify({ success: true, participant_id }),
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
