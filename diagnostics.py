import sys, traceback, io, json, os

print("=== DIAGNOSTICA DVR CHECKLIST ANALYZER ===\n")

# 1. Imports
try:
    import fitz
    print("[OK] fitz (PyMuPDF) importato")
except Exception as e:
    print("[ERRORE] fitz:", e)

try:
    from google import genai
    from google.genai import types
    print("[OK] google.genai importato")
except Exception as e:
    print("[ERRORE] google.genai:", e)

try:
    import openpyxl
    print("[OK] openpyxl importato")
except Exception as e:
    print("[ERRORE] openpyxl:", e)

# 2. Config file check
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
print(f"\nConfig path: {config_path}")
if os.path.exists(config_path):
    with open(config_path) as f:
        data = json.load(f)
    key = data.get('api_key','')
    print(f"[OK] API Key trovata - lunghezza: {len(key)} caratteri, inizio: {key[:8]}...")
else:
    print("[ERRORE] config.json NON trovato!")

# 3. DATABASE path check
DB_PATH = r"C:\Users\d.delisa.CONTEA\Desktop\DATABASE.xlsx"
print(f"\nDatabase path: {DB_PATH}")
if os.path.exists(DB_PATH):
    wb = openpyxl.load_workbook(DB_PATH, data_only=True)
    print(f"[OK] DATABASE.xlsx aperto - fogli: {wb.sheetnames}")
else:
    print("[ERRORE] DATABASE.xlsx NON trovato!")

# 4. Simulate PDF conversion with a simple test image
print("\n=== Test conversione PDF (con test.pdf se esiste) ===")
test_pdf = r"C:\Users\d.delisa.CONTEA\Desktop\Check-list.pdf"
if os.path.exists(test_pdf):
    try:
        doc = fitz.open(test_pdf)
        print(f"[OK] PDF aperto: {len(doc)} pagine")
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=100)
        img_data = pix.tobytes("png")
        print(f"[OK] Pagina convertita: {len(img_data)} bytes")
    except Exception as e:
        print("[ERRORE] Conversione PDF:", e)
        traceback.print_exc()
else:
    print("[INFO] Check-list.pdf non trovato sul Desktop, salto il test di conversione")

# 5. Test Gemini call with a dummy image to check API key validity
print("\n=== Test connessione API Gemini ===")
if os.path.exists(config_path):
    with open(config_path) as f:
        data = json.load(f)
    key = data.get('api_key','')
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents='Di solo: "OK"'
        )
        print(f"[OK] API Gemini risponde: {response.text.strip()}")
    except Exception as e:
        print("[ERRORE] Chiamata API Gemini:", e)
        traceback.print_exc()
else:
    print("[SKIP] config.json assente, impossibile testare API")

print("\n=== DIAGNOSTICA COMPLETATA ===")
