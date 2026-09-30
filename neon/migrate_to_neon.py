"""
Script di migrazione da DATABASE.xlsx a Neon.tech PostgreSQL
USO:
  set DATABASE_URL=postgresql://user:pass@ep-xyz.neon.tech/dbname?sslmode=require
  python neon/migrate_to_neon.py
"""
import os
import sys
import json
import psycopg2
import psycopg2.extras

# Configura l'encoding di output per Windows CMD
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Aggiungi cartella principale al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_adapter import ExcelAdapter, NeonAdapter

DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")
EXCEL_PATH = os.environ.get("DB_PATH", "DATABASE.xlsx")

if not DATABASE_URL:
    print("[ERRORE] La variabile d'ambiente DATABASE_URL (o NEON_DATABASE_URL) non e' impostata.")
    print("Esempio di utilizzo:")
    print("  set \"DATABASE_URL=postgresql://username:password@ep-xyz.neon.tech/neondb?sslmode=require\"")
    print("  python neon/migrate_to_neon.py")
    sys.exit(1)

if not os.path.exists(EXCEL_PATH):
    print(f"[ERRORE] File Excel non trovato in {EXCEL_PATH}")
    sys.exit(1)

print("==> Inizio migrazione da DATABASE.xlsx a Neon PostgreSQL...")

# Inizializza adapter
excel = ExcelAdapter(EXCEL_PATH)
neon = NeonAdapter(DATABASE_URL)

print("1. Migrazione Checklist Items...")
cl_items = excel.get_checklist_items()
print(f"   Trovati {len(cl_items)} elementi di checklist in Excel.")

with neon._get_conn() as conn:
    with conn.cursor() as cur:
        # Pulisci o aggiorna
        count_cl = 0
        for item in cl_items:
            cur.execute("""
                INSERT INTO checklist_items (category, item, key, is_checkbox)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    category = EXCLUDED.category,
                    item = EXCLUDED.item,
                    is_checkbox = EXCLUDED.is_checkbox,
                    updated_at = NOW();
            """, (item['category'], item['item'], item['key'], item.get('is_checkbox', True)))
            count_cl += 1
        print(f"   [OK] {count_cl} elementi checklist inseriti/aggiornati in Neon.")

print("\n2. Migrazione Criticita DVR (DVR - RISCHI)...")
risks = excel.get_all_dvr_risks()
print(f"   Trovate {len(risks)} criticita in Excel.")

with neon._get_conn() as conn:
    with conn.cursor() as cur:
        count_risks = 0
        for r in risks:
            key_val = r.get('key') or r.get('rischio') or r.get('luogo') or ""
            img_val = r.get('image') or ""
            cur.execute("""
                INSERT INTO dvr_risks (luogo, rischio, azione, entro, key, ordine, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                r.get('luogo', ''),
                r.get('rischio', ''),
                r.get('azione', ''),
                r.get('entro', ''),
                key_val,
                r.get('ordine', 999999),
                img_val
            ))
            count_risks += 1
        print(f"   [OK] {count_risks} criticita inserite su Neon.")

print("\n3. Verifico/Creo utente admin di default...")
admin_user = neon.get_user_by_username("admin")
if not admin_user:
    from werkzeug.security import generate_password_hash
    pwd_hash = generate_password_hash("admin")
    neon.add_user("admin", pwd_hash, "admin")
    print("   [OK] Creato utente admin predefinito (username: admin, pass: admin)")
else:
    print("   [OK] Utente admin gia' esistente.")

print("\n==========================================")
print("  MIGRAZIONE COMPLETATA CON SUCCESSO!")
print("==========================================")
print("Ora puoi impostare DB_BACKEND=neon e DATABASE_URL=... per usare il tuo database in cloud gratuito su Neon.tech!")
