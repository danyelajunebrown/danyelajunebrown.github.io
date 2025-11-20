-- Gaze Detection Study Database Schema
-- PostgreSQL 13+

-- Create database (run as superuser)
-- CREATE DATABASE gaze_study;
-- \c gaze_study;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Participants table
CREATE TABLE participants (
    id SERIAL PRIMARY KEY,
    participant_id VARCHAR(50) UNIQUE NOT NULL,
    consent_timestamp TIMESTAMP NOT NULL,
    registered_at TIMESTAMP DEFAULT NOW(),
    last_upload TIMESTAMP,
    total_events INTEGER DEFAULT 0,
    withdrawn BOOLEAN DEFAULT FALSE,
    withdrawn_at TIMESTAMP,
    
    -- Metadata (not linked to identity)
    browser VARCHAR(50),
    os VARCHAR(50),
    
    CONSTRAINT valid_participant_id CHECK (participant_id ~ '^P[a-z0-9]+$')
);

CREATE INDEX idx_participants_id ON participants(participant_id);
CREATE INDEX idx_participants_withdrawn ON participants(withdrawn);

-- Upload batches table
CREATE TABLE upload_batches (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(100) UNIQUE NOT NULL,
    participant_id VARCHAR(50) REFERENCES participants(participant_id) ON DELETE CASCADE,
    event_count INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    ip_address INET, -- For rate limiting only
    
    CONSTRAINT valid_batch_id CHECK (batch_id ~ '^batch_')
);

CREATE INDEX idx_batches_participant ON upload_batches(participant_id);
CREATE INDEX idx_batches_uploaded_at ON upload_batches(uploaded_at);

-- Events table (main research data)
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    participant_id VARCHAR(50) REFERENCES participants(participant_id) ON DELETE CASCADE,
    batch_id VARCHAR(100) REFERENCES upload_batches(batch_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    stored_at TIMESTAMP DEFAULT NOW(),
    
    -- Face detection data
    face_gaze_direction VARCHAR(20) NOT NULL CHECK (face_gaze_direction IN ('toward_camera', 'away')),
    face_size NUMERIC(8,2),
    luminance NUMERIC(8,2),
    
    -- User gaze data (CRITICAL: gaze_on_face must be FALSE)
    gaze_on_face BOOLEAN NOT NULL CHECK (gaze_on_face = FALSE),
    distance_from_face NUMERIC(8,2),
    
    -- Physiological responses
    pupil_diameter NUMERIC(5,2),
    pupil_baseline NUMERIC(5,2),
    blink_event BOOLEAN,
    
    -- Context
    context VARCHAR(50),
    url_domain VARCHAR(255),
    
    -- Quality metrics
    confidence_score NUMERIC(4,3),
    
    -- Full event data (JSON for flexibility in analysis)
    event_data JSONB,
    
    CONSTRAINT valid_event_id CHECK (event_id ~ '^evt_')
);

-- Indexes for analysis queries
CREATE INDEX idx_events_participant ON events(participant_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_gaze_direction ON events(face_gaze_direction);
CREATE INDEX idx_events_context ON events(context);
CREATE INDEX idx_events_batch ON events(batch_id);

-- Composite index for main analysis query
CREATE INDEX idx_events_analysis ON events(participant_id, face_gaze_direction, timestamp);

-- GIN index for JSON queries
CREATE INDEX idx_events_data ON events USING GIN (event_data);

-- Audit log table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    participant_id VARCHAR(50),
    performed_by VARCHAR(100),
    performed_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    details JSONB
);

CREATE INDEX idx_audit_timestamp ON audit_log(performed_at);
CREATE INDEX idx_audit_action ON audit_log(action);

-- Views for common queries

-- Participant summary view
CREATE VIEW participant_summary AS
SELECT 
    p.participant_id,
    p.consent_timestamp,
    p.total_events,
    p.last_upload,
    EXTRACT(DAY FROM (NOW() - p.consent_timestamp)) as days_active,
    COUNT(DISTINCT ub.batch_id) as total_uploads,
    SUM(CASE WHEN e.face_gaze_direction = 'toward_camera' THEN 1 ELSE 0 END) as looking_events,
    SUM(CASE WHEN e.face_gaze_direction = 'away' THEN 1 ELSE 0 END) as not_looking_events,
    AVG(e.pupil_diameter) as avg_pupil_diameter,
    AVG(e.distance_from_face) as avg_distance_from_face
FROM participants p
LEFT JOIN upload_batches ub ON p.participant_id = ub.participant_id
LEFT JOIN events e ON p.participant_id = e.participant_id
WHERE p.withdrawn = FALSE
GROUP BY p.participant_id, p.consent_timestamp, p.total_events, p.last_upload;

-- Context breakdown view
CREATE VIEW context_breakdown AS
SELECT 
    context,
    COUNT(*) as event_count,
    COUNT(DISTINCT participant_id) as participant_count,
    AVG(pupil_diameter) as avg_pupil,
    AVG(distance_from_face) as avg_distance
FROM events
GROUP BY context;

-- Daily statistics view
CREATE VIEW daily_stats AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_events,
    COUNT(DISTINCT participant_id) as active_participants,
    SUM(CASE WHEN face_gaze_direction = 'toward_camera' THEN 1 ELSE 0 END) as looking_events,
    SUM(CASE WHEN face_gaze_direction = 'away' THEN 1 ELSE 0 END) as not_looking_events,
    AVG(pupil_diameter) as avg_pupil,
    AVG(confidence_score) as avg_confidence
FROM events
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Functions

-- Function to safely delete participant data (for withdrawal)
CREATE OR REPLACE FUNCTION delete_participant_data(p_participant_id VARCHAR)
RETURNS TABLE(deleted_events INTEGER, deleted_batches INTEGER) AS $$
DECLARE
    v_events INTEGER;
    v_batches INTEGER;
BEGIN
    -- Delete events
    DELETE FROM events WHERE participant_id = p_participant_id;
    GET DIAGNOSTICS v_events = ROW_COUNT;
    
    -- Delete batches
    DELETE FROM upload_batches WHERE participant_id = p_participant_id;
    GET DIAGNOSTICS v_batches = ROW_COUNT;
    
    -- Mark participant as withdrawn
    UPDATE participants 
    SET withdrawn = TRUE, withdrawn_at = NOW()
    WHERE participant_id = p_participant_id;
    
    -- Log withdrawal
    INSERT INTO audit_log (action, participant_id, details)
    VALUES ('WITHDRAWAL', p_participant_id, 
            jsonb_build_object('events_deleted', v_events, 'batches_deleted', v_batches));
    
    RETURN QUERY SELECT v_events, v_batches;
END;
$$ LANGUAGE plpgsql;

-- Function to get participant statistics
CREATE OR REPLACE FUNCTION get_participant_stats(p_participant_id VARCHAR)
RETURNS TABLE(
    total_events BIGINT,
    looking_events BIGINT,
    not_looking_events BIGINT,
    avg_pupil NUMERIC,
    avg_distance NUMERIC,
    contexts JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_events,
        SUM(CASE WHEN face_gaze_direction = 'toward_camera' THEN 1 ELSE 0 END) as looking_events,
        SUM(CASE WHEN face_gaze_direction = 'away' THEN 1 ELSE 0 END) as not_looking_events,
        AVG(pupil_diameter) as avg_pupil,
        AVG(distance_from_face) as avg_distance,
        jsonb_object_agg(context, cnt) as contexts
    FROM (
        SELECT 
            face_gaze_direction,
            pupil_diameter,
            distance_from_face,
            context,
            COUNT(*) as cnt
        FROM events
        WHERE participant_id = p_participant_id
        GROUP BY face_gaze_direction, pupil_diameter, distance_from_face, context
    ) subq;
END;
$$ LANGUAGE plpgsql;

-- Triggers

-- Update last_upload timestamp
CREATE OR REPLACE FUNCTION update_last_upload()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE participants 
    SET last_upload = NOW()
    WHERE participant_id = NEW.participant_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_last_upload
AFTER INSERT ON upload_batches
FOR EACH ROW
EXECUTE FUNCTION update_last_upload();

-- Audit log for data access
CREATE OR REPLACE FUNCTION log_event_access()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'SELECT' THEN
        -- Log would go here if we track SELECTs
        -- (Typically done at application level for performance)
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Grants (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO gaze_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gaze_app;

-- Sample data for testing (DO NOT USE IN PRODUCTION)
-- INSERT INTO participants (participant_id, consent_timestamp)
-- VALUES ('Ptest123abc', NOW() - INTERVAL '30 days');

-- Useful queries for monitoring

-- Check data quality
-- SELECT 
--     COUNT(*) as total_events,
--     COUNT(DISTINCT participant_id) as unique_participants,
--     AVG(confidence_score) as avg_confidence,
--     SUM(CASE WHEN gaze_on_face = TRUE THEN 1 ELSE 0 END) as invalid_events
-- FROM events;

-- Check upload activity
-- SELECT 
--     DATE(uploaded_at) as date,
--     COUNT(*) as uploads,
--     SUM(event_count) as events
-- FROM upload_batches
-- WHERE uploaded_at > NOW() - INTERVAL '7 days'
-- GROUP BY DATE(uploaded_at)
-- ORDER BY date DESC;

-- Check participant retention
-- SELECT 
--     EXTRACT(DAY FROM (NOW() - consent_timestamp)) as days_since_consent,
--     COUNT(*) as participants
-- FROM participants
-- WHERE withdrawn = FALSE
-- GROUP BY days_since_consent
-- ORDER BY days_since_consent;
