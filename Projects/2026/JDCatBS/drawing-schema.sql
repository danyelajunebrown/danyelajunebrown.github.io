-- ============================================
-- JDCatBS INTERACTIVE MAP — DRAWING DATA
-- Run this once in Supabase Dashboard > SQL Editor
-- (project hbhorkrfndwsnwdhxotd).
-- Replaces the old GitHub-API auto-save that required an exposed token.
-- ============================================

CREATE TABLE IF NOT EXISTS jdcatbs_drawing (
    id          TEXT PRIMARY KEY DEFAULT 'main',
    paths       JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE jdcatbs_drawing ENABLE ROW LEVEL SECURITY;

-- The map page is password-gated client-side; the anon key is public by design.
-- Mirror the portfolio tables: allow anon read + write to this single table.
CREATE POLICY "Public read jdcatbs drawing"
ON jdcatbs_drawing FOR SELECT TO anon USING (true);

CREATE POLICY "Anon insert jdcatbs drawing"
ON jdcatbs_drawing FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Anon update jdcatbs drawing"
ON jdcatbs_drawing FOR UPDATE TO anon USING (true);
