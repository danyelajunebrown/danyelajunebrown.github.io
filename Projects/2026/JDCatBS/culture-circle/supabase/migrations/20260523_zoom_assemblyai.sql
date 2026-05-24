-- Adds Zoom-import + transcription-provider tracking to interviews.
-- Safe to run more than once.

ALTER TABLE interviews
  ADD COLUMN IF NOT EXISTS transcription_provider TEXT
    CHECK (transcription_provider IN ('deepgram', 'assemblyai', 'mixed')),
  ADD COLUMN IF NOT EXISTS zoom_meeting_uuid TEXT,
  ADD COLUMN IF NOT EXISTS zoom_meeting_id   TEXT,
  ADD COLUMN IF NOT EXISTS zoom_topic        TEXT,
  ADD COLUMN IF NOT EXISTS zoom_start_time   TIMESTAMPTZ;

-- One row per Zoom meeting we've imported, to avoid double-imports.
CREATE UNIQUE INDEX IF NOT EXISTS interviews_zoom_meeting_uuid_uidx
  ON interviews(zoom_meeting_uuid)
  WHERE zoom_meeting_uuid IS NOT NULL;
