import os
import sys
import json
import urllib.request
from werkzeug.security import generate_password_hash

new_password = sys.argv[1] if len(sys.argv) > 1 else "admin"

url = "postgresql://neondb_owner:npg_pfaUWsvG6r7F@ep-autumn-darkness-b160gyre-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require"
parts = url.split("@")
host_part = parts[1].split("/")[0].split(":")[0]
endpoint = f"https://{host_part}/sql"

pwd_hash = generate_password_hash(new_password).replace("'", "''")

sql = f"UPDATE users SET password_hash = '{pwd_hash}' WHERE username = 'admin';"

req = urllib.request.Request(
    endpoint,
    data=json.dumps({"query": sql}).encode("utf-8"),
    headers={
        "Neon-Connection-String": url,
        "Content-Type": "application/json"
    }
)

res = urllib.request.urlopen(req)
print(f"[OK] Password per utente 'admin' aggiornata a: '{new_password}'")
