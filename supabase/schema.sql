-- ============================================
-- DVR Checklist Analyzer - Supabase Schema
-- ============================================

-- Tabella: checklist_items
-- Sostituisce il foglio "CHECK LIST" di Excel
CREATE TABLE IF NOT EXISTS checklist_items (
    id BIGSERIAL PRIMARY KEY,
    category TEXT NOT NULL DEFAULT 'GENERALE',
    item TEXT NOT NULL,
    key TEXT NOT NULL UNIQUE,
    is_checkbox BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella: dvr_risks
-- Sostituisce il foglio "DVR - RISCHI" di Excel
-- Le immagini sono riferite come URL su Supabase Storage
CREATE TABLE IF NOT EXISTS dvr_risks (
    id BIGSERIAL PRIMARY KEY,
    luogo TEXT DEFAULT '',
    rischio TEXT NOT NULL DEFAULT '',
    azione TEXT DEFAULT '',
    entro TEXT DEFAULT '',
    key TEXT DEFAULT '',
    ordine INTEGER DEFAULT 999999,
    image_url TEXT DEFAULT '',
    is_falso BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indici per velocizzare le ricerche
CREATE INDEX IF NOT EXISTS idx_checklist_items_key ON checklist_items(key);
CREATE INDEX IF NOT EXISTS idx_checklist_items_category ON checklist_items(category);
CREATE INDEX IF NOT EXISTS idx_dvr_risks_ordine ON dvr_risks(ordine);
CREATE INDEX IF NOT EXISTS idx_dvr_risks_key ON dvr_risks(key);

-- Trigger per aggiornare updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_checklist_items_updated_at ON checklist_items;
CREATE TRIGGER update_checklist_items_updated_at
    BEFORE UPDATE ON checklist_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dvr_risks_updated_at ON dvr_risks;
CREATE TRIGGER update_dvr_risks_updated_at
    BEFORE UPDATE ON dvr_risks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - permette lettura e scrittura a tutti per la migrazione iniziale
ALTER TABLE checklist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE dvr_risks ENABLE ROW LEVEL SECURITY;

-- Policy per lettura pubblica a tutti
CREATE POLICY "Lettura pubblica checklist_items" ON checklist_items
    FOR SELECT USING (true);

CREATE POLICY "Lettura pubblica dvr_risks" ON dvr_risks
    FOR SELECT USING (true);

-- Policy per scrittura con anon key (per app pubblica condivisa)
CREATE POLICY "Scrittura anon checklist_items" ON checklist_items
    FOR INSERT WITH CHECK (auth.role() = 'anon');

CREATE POLICY "Scrittura anon dvr_risks" ON dvr_risks
    FOR INSERT WITH CHECK (auth.role() = 'anon');

CREATE POLICY "Aggiornamento anon dvr_risks" ON dvr_risks
    FOR UPDATE USING (auth.role() = 'anon');

CREATE POLICY "Cancellazione anon dvr_risks" ON dvr_risks
    FOR DELETE USING (auth.role() = 'anon');

-- Storage bucket per le immagini delle criticità
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'risk-images',
    'risk-images',
    true,
    5242880,
    ARRAY['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
) ON CONFLICT (id) DO NOTHING;

-- Policy per il bucket: pubblico in lettura e scrittura per app condivisa
CREATE POLICY "Public read for risk-images" ON storage.objects
    FOR SELECT USING (bucket_id = 'risk-images');

CREATE POLICY "Anonymous upload for risk-images" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'risk-images');

CREATE POLICY "Anonymous update for risk-images" ON storage.objects
    FOR UPDATE USING (bucket_id = 'risk-images');

CREATE POLICY "Anonymous delete for risk-images" ON storage.objects
    FOR DELETE USING (bucket_id = 'risk-images');
