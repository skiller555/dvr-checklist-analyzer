import os
import sys
import json
import urllib.request
from werkzeug.security import generate_password_hash

# Aggiungi cartella principale al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_adapter import ExcelAdapter

DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL") or os.environ.get("NEON_DATABASE_URL") or "postgresql://neondb_owner:npg_pfaUWsvG6r7F@ep-autumn-darkness-b160gyre-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require"
EXCEL_PATH = os.environ.get("DB_PATH", "DATABASE.xlsx")

# Estrai hostname dall'URL
# Format: postgresql://user:pass@host/dbname...
parts = DATABASE_URL.split("@")
if len(parts) > 1:
    host_part = parts[1].split("/")[0].split(":")[0]
else:
    host_part = "ep-autumn-darkness-b160gyre-pooler.c-5.eu-central-1.aws.neon.tech"

HTTP_ENDPOINT = f"https://{host_part}/sql"

print(f"==> Inizio migrazione da {EXCEL_PATH} a Neon PostgreSQL via HTTP API...")
print(f"    Endpoint: {HTTP_ENDPOINT}")

def query_neon(sql):
    req = urllib.request.Request(
        HTTP_ENDPOINT,
        data=json.dumps({"query": sql}).encode("utf-8"),
        headers={
            "Neon-Connection-String": DATABASE_URL,
            "Content-Type": "application/json"
        }
    )
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_text = e.fp.read().decode("utf-8")
        print(f"❌ Errore HTTP {e.code}: {err_text}")
        raise

# 1. Inizializzazione Schema
print("1. Inizializzazione tabelle PostgreSQL...")
schema_statements = [
    """CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMPTZ DEFAULT NOW()
    );""",
    """CREATE TABLE IF NOT EXISTS checklist_items (
        id BIGSERIAL PRIMARY KEY,
        category TEXT NOT NULL DEFAULT 'GENERALE',
        item TEXT NOT NULL,
        key TEXT NOT NULL UNIQUE,
        is_checkbox BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );""",
    """CREATE TABLE IF NOT EXISTS dvr_risks (
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
    );"""
]

for stmt in schema_statements:
    query_neon(stmt)
print("   [OK] Schema verificato e creato su Neon.")

# 2. Migrazione Checklist Items
excel = ExcelAdapter(EXCEL_PATH)
cl_items = excel.get_checklist_items()
print(f"\n2. Migrazione {len(cl_items)} elementi di Checklist...")

count_cl = 0
for item in cl_items:
    cat = (item['category'] or 'GENERALE').replace("'", "''")
    it = (item['item'] or '').replace("'", "''")
    k = (item['key'] or '').replace("'", "''")
    cb = "TRUE" if item.get('is_checkbox', True) else "FALSE"
    
    sql = f"""
        INSERT INTO checklist_items (category, item, key, is_checkbox)
        VALUES ('{cat}', '{it}', '{k}', {cb})
        ON CONFLICT (key) DO UPDATE SET
            category = EXCLUDED.category,
            item = EXCLUDED.item,
            is_checkbox = EXCLUDED.is_checkbox,
            updated_at = NOW();
    """
    query_neon(sql)
    count_cl += 1

print(f"   [OK] {count_cl} elementi inseriti/aggiornati in Neon.")

# 3. Migrazione Criticità DVR (DVR - RISCHI)
risks = excel.get_all_dvr_risks()
print(f"\n3. Migrazione {len(risks)} criticità DVR (compreso immagini Base64)...")

count_risks = 0
for r in risks:
    l = (r.get('luogo') or '').replace("'", "''")
    ri = (r.get('rischio') or '').replace("'", "''")
    az = (r.get('azione') or '').replace("'", "''")
    en = (r.get('entro') or '').replace("'", "''")
    k = (r.get('key') or ri or l or '').replace("'", "''")
    ord_val = r.get('ordine', 999999)
    img_val = (r.get('image') or '').replace("'", "''")
    
    sql = f"""
        INSERT INTO dvr_risks (luogo, rischio, azione, entro, key, ordine, image_url)
        VALUES ('{l}', '{ri}', '{az}', '{en}', '{k}', {ord_val}, '{img_val}');
    """
    query_neon(sql)
    count_risks += 1

print(f"   [OK] {count_risks} criticità caricate su Neon.")

# 4. Utente admin
print("\n4. Configurazione utente admin predefinito...")
pwd_hash = generate_password_hash("admin").replace("'", "''")
query_neon(f"""
    INSERT INTO users (username, password_hash, role)
    VALUES ('admin', '{pwd_hash}', 'admin')
    ON CONFLICT (username) DO NOTHING;
""")
print("   [OK] Utente admin garantito (user: admin, pass: admin).")

print("\n========================================================")
print("  MIGRAZIONE SU NEON COMPLETATA CON SUCCESSO!")
print("========================================================")
