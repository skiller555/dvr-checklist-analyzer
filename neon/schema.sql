-- ============================================
-- DVR Checklist Analyzer - Neon PostgreSQL Schema
-- ============================================

-- Tabella: users (Gestione utenti per login)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella: checklist_items (Elementi di checklist)
CREATE TABLE IF NOT EXISTS checklist_items (
    id BIGSERIAL PRIMARY KEY,
    category TEXT NOT NULL DEFAULT 'GENERALE',
    item TEXT NOT NULL,
    key TEXT NOT NULL UNIQUE,
    is_checkbox BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella: dvr_risks (Criticità DVR e foto)
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

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_checklist_items_key ON checklist_items(key);
CREATE INDEX IF NOT EXISTS idx_checklist_items_category ON checklist_items(category);
CREATE INDEX IF NOT EXISTS idx_dvr_risks_ordine ON dvr_risks(ordine);
CREATE INDEX IF NOT EXISTS idx_dvr_risks_key ON dvr_risks(key);
