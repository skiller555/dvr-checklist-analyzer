import os
import sys
import json
import urllib.request
from werkzeug.security import generate_password_hash, check_password_hash

h = generate_password_hash("admin")
print("Generated hash:", h)

url = "postgresql://neondb_owner:npg_pfaUWsvG6r7F@ep-autumn-darkness-b160gyre-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require"
parts = url.split("@")
host_part = parts[1].split("/")[0].split(":")[0]
endpoint = f"https://{host_part}/sql"

sql = f"UPDATE users SET password_hash = '{h}' WHERE username = 'admin';"

req = urllib.request.Request(
    endpoint,
    data=json.dumps({"query": sql}).encode("utf-8"),
    headers={
        "Neon-Connection-String": url,
        "Content-Type": "application/json"
    }
)
res = urllib.request.urlopen(req)
print("Update response:", res.read().decode("utf-8"))

# Test query back
req2 = urllib.request.Request(
    endpoint,
    data=json.dumps({"query": "SELECT password_hash FROM users WHERE username = 'admin';"}).encode("utf-8"),
    headers={
        "Neon-Connection-String": url,
        "Content-Type": "application/json"
    }
)
res2 = urllib.request.urlopen(req2)
row = json.loads(res2.read().decode("utf-8"))["rows"][0]
db_hash = row["password_hash"]
print("Stored hash in DB:", db_hash)
print("VERIFICATION OF LOGIN 'admin':", check_password_hash(db_hash, "admin"))
