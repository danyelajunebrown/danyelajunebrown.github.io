-- ============================================
-- PORTFOLIO SCHEMA + LIVE DATA MIGRATION
-- Generated from live backup 20260521_205725 (old project qugdliacaizpvbzcdmpi)
-- Run this ONCE in the NEW Supabase project: Dashboard > SQL Editor
-- ============================================

CREATE TABLE portfolio_projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date TEXT,
    year INTEGER,
    materials TEXT[] DEFAULT '{}',
    description TEXT DEFAULT '',
    score_dearness INTEGER,
    score_completeness INTEGER,
    score_cost INTEGER,
    score_themes TEXT[] DEFAULT '{}',
    score_genres TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE portfolio_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT NOT NULL REFERENCES portfolio_projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    media_type TEXT NOT NULL CHECK (media_type IN ('image', 'video', 'youtube', 'pdf')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX portfolio_media_project_idx ON portfolio_media(project_id);
CREATE INDEX portfolio_media_sort_idx ON portfolio_media(project_id, sort_order);

CREATE OR REPLACE FUNCTION update_portfolio_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_portfolio_updated_at
BEFORE UPDATE ON portfolio_projects
FOR EACH ROW
EXECUTE FUNCTION update_portfolio_updated_at();

-- Row Level Security
ALTER TABLE portfolio_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_media ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read portfolio projects" ON portfolio_projects FOR SELECT TO anon USING (true);
CREATE POLICY "Public read portfolio media" ON portfolio_media FOR SELECT TO anon USING (true);
CREATE POLICY "Auth full access portfolio projects" ON portfolio_projects FOR ALL TO authenticated USING (true);
CREATE POLICY "Auth full access portfolio media" ON portfolio_media FOR ALL TO authenticated USING (true);
CREATE POLICY "Anon insert portfolio projects" ON portfolio_projects FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Anon update portfolio projects" ON portfolio_projects FOR UPDATE TO anon USING (true);
CREATE POLICY "Anon delete portfolio projects" ON portfolio_projects FOR DELETE TO anon USING (true);
CREATE POLICY "Anon insert portfolio media" ON portfolio_media FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Anon update portfolio media" ON portfolio_media FOR UPDATE TO anon USING (true);
CREATE POLICY "Anon delete portfolio media" ON portfolio_media FOR DELETE TO anon USING (true);

-- ============================================
-- LIVE DATA (13 projects, 17 media records)
-- ============================================

INSERT INTO portfolio_projects (id, title, date, year, materials, description, score_dearness, score_completeness, score_cost, score_themes, score_genres, created_at, updated_at) VALUES
('mhlkxak16ypk6s7mzus', 'Asili', '', 2025, '{}', '', 100, NULL, 80, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmhw0r238o1o1uqec7', 'DBT Skills Group Blues', '2025', 2025, '{"camshow"}', 'fuck u marsha', NULL, 50, 0, '{"autonomy","access","neurogender"}', '{"performance-set"}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmihqby7fy2kk47bul', 'untitled (battle shaun khan''s ball 10.11.25)', '10.11.2025', 2025, '{}', 'FEM QUEEN - Gluttony- Bring it in a any fast food worker uniform.', NULL, NULL, 0, '{}', '{"costume-set","ballroom"}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmm0wvgt7fp4c9dhj', 'Eye Always Feel Like', '2024', 2025, '{"survey responses"}', '', NULL, NULL, 62, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmnevpefmpu0i04foq', 'untitled (RIP Dream Johnson)', '2025', 2025, '{"live performance","tshirt","inkjet transfer","modpodge"}', '', 85, NULL, NULL, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmnlxiwo6t5t0hanz', 'The NLA', '2021', 2025, '{}', '', NULL, NULL, 70, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmyj4sj6tf2yxxshp', 'NLA31599', '2023', 2025, '{}', '', 62, NULL, NULL, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmymaoi54uqpu6gjzq', 'dysaesthesia aethiopica', '', 2025, '{}', '', NULL, NULL, NULL, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmyqz01vyunq4e277', 'Homeody', '2025', 2025, '{"uv ink","performance score"}', '', NULL, NULL, NULL, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmyx1zy8tzl4us8v9', 'Rocket Science', '2025', 2025, '{"uv ink","performance score"}', '', NULL, NULL, NULL, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmz137rayvntk7t9qs', 'Do We See With Eyes Or With The Psyche?', '2025', 2025, '{"choreography","projection"}', '', NULL, NULL, NULL, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmz2yj2hnf3tqi0cbc', 'STUDIO PRACTICE', '2024', 2025, '{"cam show","set"}', '', NULL, NULL, NULL, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00'),
('mhmz5mhkh4rolpk9tcu', 'Trying It', '2024', 2025, '{}', '', NULL, NULL, NULL, '{}', '{}', '2026-04-05T22:25:48.085336+00:00', '2026-04-05T22:25:48.085336+00:00');

INSERT INTO portfolio_media (id, project_id, url, media_type, sort_order, created_at) VALUES
('6b8c25d8-cd90-48b4-816d-cbe751fa5783', 'mhlkxak16ypk6s7mzus', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762321841628-IMG_2915.MOV', 'video', 0, '2026-04-05T22:25:48.085336+00:00'),
('eedbbe40-4414-49c0-b057-15499ba2571f', 'mhlkxak16ypk6s7mzus', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762386625767-image%203.jpg', 'image', 1, '2026-04-05T22:25:48.085336+00:00'),
('66c6b6b2-3cd5-42d7-8455-3d9848324609', 'mhmhw0r238o1o1uqec7', 'https://pub-f9bb84bd43c343799213e3bfbc9436c5.r2.dev/1762382501007-DBT Skills Group Blues (2025).mp4', 'video', 0, '2026-04-05T22:25:48.085336+00:00'),
('d16aafb8-aed6-4cc4-b387-885446e749fe', 'mhmihqby7fy2kk47bul', 'https://pub-f9bb84bd43c343799213e3bfbc9436c5.r2.dev/1762380903785-10.11.25_battle.mp4', 'video', 0, '2026-04-05T22:25:48.085336+00:00'),
('4b88995b-2ac8-4036-82c6-67532459770a', 'mhmihqby7fy2kk47bul', 'https://pub-f9bb84bd43c343799213e3bfbc9436c5.r2.dev/1762383981649-10.11.25_tens.mp4', 'video', 1, '2026-04-05T22:25:48.085336+00:00'),
('3998932c-951c-4d04-b532-34f8fd82965e', 'mhmm0wvgt7fp4c9dhj', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762384158825-Eye%20Always%20Feel%20Like%20(Survey%20Responses).jpg', 'image', 0, '2026-04-05T22:25:48.085336+00:00'),
('5013060b-2e1f-4eb6-9861-64c722a0a5a6', 'mhmnevpefmpu0i04foq', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762386487537-IMG_3360.jpeg', 'image', 0, '2026-04-05T22:25:48.085336+00:00'),
('7faf5a2d-c31c-47fe-ba7f-eee44fcc3555', 'mhmnevpefmpu0i04foq', 'VL3bCHgXNmo', 'youtube', 1, '2026-04-05T22:25:48.085336+00:00'),
('25e8aee5-8742-4874-80b5-8f646063c974', 'mhmnlxiwo6t5t0hanz', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762386814270-Danyela8.JPG', 'image', 0, '2026-04-05T22:25:48.085336+00:00'),
('ff94ce03-ed45-4b11-bae6-e0b2280c105d', 'mhmyj4sj6tf2yxxshp', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762405164173-IMG_0134.HEIC', 'image', 0, '2026-04-05T22:25:48.085336+00:00'),
('82ed1d77-f23c-4188-be3f-f96309b957a9', 'mhmymaoi54uqpu6gjzq', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762405305773-dysaesthesia%20aethiopica.jpeg', 'image', 0, '2026-04-05T22:25:48.085336+00:00'),
('71fc5d84-517e-4955-9517-7423e7725c61', 'mhmymaoi54uqpu6gjzq', '7huAtaUxn_c', 'youtube', 1, '2026-04-05T22:25:48.085336+00:00'),
('01c55e3c-69d1-43b7-b7d8-b4deb486f402', 'mhmyqz01vyunq4e277', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762405527571-IMG_1097.heic', 'image', 0, '2026-04-05T22:25:48.085336+00:00'),
('5fe6c0e0-ab42-42fe-99d4-899fee504ff2', 'mhmyx1zy8tzl4us8v9', 'https://raw.githubusercontent.com/danyelajunebrown/danyelajunebrown.github.io/main/assets/1762405808933-IMG_1099.heic', 'image', 0, '2026-04-05T22:25:48.085336+00:00'),
('fa197052-e9b3-45f6-a1c2-11c421fddb8f', 'mhmz137rayvntk7t9qs', 'xxY8zy6TYU4', 'youtube', 0, '2026-04-05T22:25:48.085336+00:00'),
('fc0fe2ce-748e-4116-ab78-ea3703dacd01', 'mhmz2yj2hnf3tqi0cbc', 'BRNuK34OCKI', 'youtube', 0, '2026-04-05T22:25:48.085336+00:00'),
('20562d4a-8e10-4e33-ae72-63eb85f54e05', 'mhmz5mhkh4rolpk9tcu', 'Y6KGaAbHYRc', 'youtube', 0, '2026-04-05T22:25:48.085336+00:00');