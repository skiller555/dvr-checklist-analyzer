# DVR Checklist Analyzer - Guida Deploy Online

## Architettura Online vs Locale

| Componente | Locale | Online |
|------------|--------|--------|
| Frontend | Flask `templates/` | Netlify (static) |
| Backend API | Flask locale | Docker (Fly.io / Render / VPS) |
| Database | DATABASE.xlsx | Supabase PostgreSQL |
| Immagini | Embed in Excel | Supabase Storage |
| OCR | Tesseract locale | Tesseract (ottimizzato) |

## Deploy Locale (sviluppo)

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

## Deploy Online - Passo 1: Supabase

1. Crea progetto su [supabase.com](https://supabase.com)
2. Esegui SQL da `supabase/schema.sql` nell'SQL Editor
3. Copia `SUPABASE_URL` e `SUPABASE_KEY` (anon key)
4. Carica `DATABASE.xlsx` nella cartella del progetto

## Deploy Online - Passo 2: Migrazione Dati

```bash
pip install python-dotenv  # se non già installato
set SUPABASE_URL=https://tuo-progetto.supabase.co
set SUPABASE_KEY=eyJ...  # anon key
python supabase/migrate_to_supabase.py
```

Verifica in Supabase Dashboard > Table Editor che le tabelle siano popolate.

## Deploy Online - Passo 3: Backend Docker

### Opzione A: Fly.io (consigliato)

```bash
fly launch
fly secrets set SUPABASE_URL=... SUPABASE_KEY=...
fly deploy
```

### Opzione B: Render

- Connetti repo GitHub
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`
- Env vars: `SUPABASE_URL`, `SUPABASE_KEY`, `DB_BACKEND=supabase`

### Opzione C: VPS

```bash
docker build -t dvr-analyzer .
docker run -p 5000:5000 \
  -e SUPABASE_URL=... \
  -e SUPABASE_KEY=... \
  -e DB_BACKEND=supabase \
  dvr-analyzer
```

## Deploy Online - Passo 4: Frontend Netlify

1. Pusha il repo su GitHub
2. In Netlify: New site from Git
3. Build settings:
   - Build command: `cd frontend && node scripts/build-for-netlify.js`
   - Publish directory: `dist/frontend`
4. In Netlify: Site settings > Environment variables
   - `API_BASE`: `https://tuo-backend.fly.dev` (URL del backend)
5. Deploy

Il file `netlify.toml` già configura proxy e redirect.

## Variabili d'Ambiente

| Variabile | Locale | Online | Note |
|-----------|--------|--------|------|
| `DB_BACKEND` | `local` | `supabase` | default: `local` |
| `DB_PATH` | `./DATABASE.xlsx` | - | solo locale |
| `SUPABASE_URL` | - | `https://...` | Supabase project URL |
| `SUPABASE_KEY` | - | `eyJ...` | Supabase anon/public key |
| `FLASK_ENV` | `development` | `production` | |
| `PORT` | `5000` | `$PORT` | |

## Struttura Progetto Aggiornata

```
dvr_checklist_analyzer/
├── app.py                    ← Backend Flask (modificato, adapter DB)
├── db_adapter.py             ← Nuovo: astrazione Excel ↔ Supabase
├── requirements.txt          ← Aggiornato con supabase, gunicorn, opencv
├── Dockerfile                ← Nuovo: deploy containerizzato
├── docker-compose.yml        ← Nuovo: test locale multi-service
├── netlify.toml              ← Nuovo: config Netlify
├── frontend/
│   ├── package.json          ← Nuovo: build script
│   └── scripts/
│       └── build-for-netlify.js  ← Nuovo: transpila Jinja2 → static
├── supabase/
│   ├── schema.sql            ← Nuovo: schema PostgreSQL + RLS
│   └── migrate_to_supabase.py ← Nuovo: migrazione dati Excel → Supabase
├── .env.example              ← Nuovo: template env vars
├── static/
│   ├── app.js                ← Modificato: API_BASE configurabile
│   └── styles.css
├── templates/
│   └── index.html            ← Serve da base per build frontend
├── DATABASE.xlsx             ← Database originale
├── Tesseract-OCR/            ← OCR portatile (solo locale)
└── dist/
    └── frontend/             ← Generato da build script (per Netlify)
```

## Rollback a Funzionamento Locale

Se `DB_BACKEND` non è definito o è `local`, l'app usa il vecchio comportamento con `DATABASE.xlsx`. Nessuna modifica al codice Excel esistente.

## Costi Stimati

- **Supabase Free Tier**: 500 MB DB, 1 GB Storage, 2 progetti
- **Fly.io Free**: 3 shared VMs (per deploy backend)
- **Netlify Free**: 100 GB bandwidth, 300 build min/mese

Totale: **0€/mese** per uso base.
