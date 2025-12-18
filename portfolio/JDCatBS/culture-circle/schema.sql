-- Service Culture Circle - Supabase Database Schema
-- Run this in your Supabase SQL Editor

-- ============================================
-- ENABLE EXTENSIONS
-- ============================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- PARTICIPANTS (Interview subjects)
-- ============================================
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    login_key TEXT UNIQUE NOT NULL,
    login_key_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended')),
    notes TEXT
);

-- ============================================
-- EMAIL CHANGE REQUESTS (require study lead approval)
-- ============================================
CREATE TABLE email_change_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id UUID REFERENCES participants(id) ON DELETE CASCADE,
    old_email TEXT NOT NULL,
    new_email TEXT NOT NULL,
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    processed_at TIMESTAMPTZ,
    processed_by UUID REFERENCES auth.users(id)
);

-- ============================================
-- VOICE FINGERPRINTS (speaker identification)
-- ============================================
CREATE TABLE voice_fingerprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id UUID REFERENCES participants(id) ON DELETE CASCADE,
    embedding VECTOR(256),
    source_interview_id UUID,
    segment_duration_seconds FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    confidence_score FLOAT
);

CREATE INDEX voice_fingerprints_embedding_idx
ON voice_fingerprints USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================
-- INTERVIEWS (upload records)
-- ============================================
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    recorded_at TIMESTAMPTZ,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    uploaded_by UUID REFERENCES auth.users(id) NOT NULL,
    processing_status TEXT DEFAULT 'uploaded'
        CHECK (processing_status IN ('uploaded', 'transcribing', 'pending_review', 'completed', 'failed')),
    audio_deleted BOOLEAN DEFAULT FALSE,
    audio_deleted_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    word_count INTEGER,
    speaker_count INTEGER,
    error_message TEXT,
    metadata JSONB
);

-- ============================================
-- TRANSCRIPT SEGMENTS (individual speaker turns)
-- ============================================
CREATE TABLE transcript_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    speaker_label TEXT NOT NULL,
    participant_id UUID REFERENCES participants(id),
    start_time_ms INTEGER NOT NULL,
    end_time_ms INTEGER NOT NULL,
    content TEXT NOT NULL,
    confidence FLOAT,
    word_timestamps JSONB,
    sequence_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tagged_at TIMESTAMPTZ,
    tagged_by UUID REFERENCES auth.users(id)
);

CREATE INDEX transcript_segments_interview_idx ON transcript_segments(interview_id);
CREATE INDEX transcript_segments_participant_idx ON transcript_segments(participant_id);

-- ============================================
-- SPEAKER SUGGESTIONS (voice match predictions)
-- ============================================
CREATE TABLE speaker_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    speaker_label TEXT NOT NULL,
    participant_id UUID REFERENCES participants(id),
    similarity_score FLOAT NOT NULL,
    embedding_used UUID REFERENCES voice_fingerprints(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- CONSENT FORMS (versioned)
-- ============================================
CREATE TABLE consent_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    effective_date TIMESTAMPTZ NOT NULL,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================
-- CONSENT RECORDS (participant signatures)
-- ============================================
CREATE TABLE consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id UUID REFERENCES participants(id) ON DELETE CASCADE,
    consent_form_id UUID REFERENCES consent_forms(id),
    consented_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    signature_data TEXT,
    withdrawal_at TIMESTAMPTZ,
    withdrawal_reason TEXT
);

-- ============================================
-- AUDIT LOGS (IRB compliance)
-- ============================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    actor_type TEXT NOT NULL CHECK (actor_type IN ('study_lead', 'participant', 'system')),
    actor_id UUID,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX audit_logs_timestamp_idx ON audit_logs(timestamp DESC);
CREATE INDEX audit_logs_actor_idx ON audit_logs(actor_type, actor_id);
CREATE INDEX audit_logs_resource_idx ON audit_logs(resource_type, resource_id);

-- ============================================
-- NOTIFICATIONS (email tracking)
-- ============================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id UUID REFERENCES participants(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('new_content', 'key_resent', 'consent_reminder')),
    interview_id UUID REFERENCES interviews(id),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    sendgrid_message_id TEXT,
    status TEXT DEFAULT 'sent' CHECK (status IN ('pending', 'sent', 'delivered', 'failed')),
    error_message TEXT
);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================
ALTER TABLE participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcript_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_fingerprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE speaker_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_change_requests ENABLE ROW LEVEL SECURITY;

-- Study lead (authenticated users) have full access
CREATE POLICY "Study leads have full access to participants"
ON participants FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to interviews"
ON interviews FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to transcript_segments"
ON transcript_segments FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to consent_records"
ON consent_records FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to audit_logs"
ON audit_logs FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to consent_forms"
ON consent_forms FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to voice_fingerprints"
ON voice_fingerprints FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to speaker_suggestions"
ON speaker_suggestions FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to notifications"
ON notifications FOR ALL TO authenticated USING (true);

CREATE POLICY "Study leads have full access to email_change_requests"
ON email_change_requests FOR ALL TO authenticated USING (true);

-- ============================================
-- STORAGE BUCKET (run in Supabase Dashboard > Storage)
-- ============================================
-- Create a bucket named 'interview-audio' with:
-- - Public: OFF
-- - File size limit: 500MB
-- - Allowed MIME types: audio/mpeg, audio/wav, audio/mp4, audio/x-m4a

-- ============================================
-- INSERT DEFAULT CONSENT FORM
-- ============================================
INSERT INTO consent_forms (version, title, content, effective_date, is_active)
VALUES (
    1,
    'Service Culture Circle Research Consent',
    E'## Research Participant Consent Form\n\n### Purpose\nYou are being invited to view portions of interview transcripts in which you participated as part of the Service Culture Circle research project.\n\n### Your Rights\n- You may access only transcript portions where you are the speaker\n- You may request corrections to transcription errors\n- You may withdraw consent at any time\n- Your data will be handled according to IRB-approved protocols\n\n### Data Handling\n- Original audio recordings are deleted after transcription\n- Only text transcripts are retained\n- Access is logged for research integrity\n\n### Contact\nFor questions about this research, contact the study lead.\n\nBy proceeding, you confirm that you understand and consent to these terms.',
    NOW(),
    true
);
