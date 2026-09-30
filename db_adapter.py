"""
Database abstraction layer per DVR Checklist Analyzer.
Supporta tre backend:
- 'local': Excel locale + JSON utenti
- 'neon': Neon.tech PostgreSQL (100% Gratuito Cloud)
- 'supabase': Supabase PostgreSQL + Storage
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import re
import os
import json


class DatabaseAdapter(ABC):
    @abstractmethod
    def get_checklist_items(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_all_dvr_risks(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def match_risks(self, checked_keys: List[str]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_database_risk(self, risk: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_all_users(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_user(self, username: str, password_hash: str, role: str = 'user') -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        pass


class ExcelAdapter(DatabaseAdapter):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._checklist_cache = None
        self._risks_cache = None
        self._images_cache = None
        self._users_path = os.path.join(os.path.expanduser("~"), "Documents", "CONTEA DVR Analyzer", "users.json")

    def _get_images_map(self):
        if self._images_cache is not None:
            return self._images_cache
        self._images_cache = {}
        if not os.path.exists(self.db_path):
            return self._images_cache

        try:
            import zipfile
            import xml.etree.ElementTree as ET
            import base64

            with zipfile.ZipFile(self.db_path, 'r') as z:
                if 'xl/drawings/drawing9.xml' not in z.namelist():
                    return self._images_cache
                rels = z.read('xl/drawings/_rels/drawing9.xml.rels').decode('utf-8')
                root = ET.fromstring(rels)
                rid_to_img = {}
                for rel in root:
                    rid_to_img[rel.attrib['Id']] = rel.attrib['Target'].replace('../', 'xl/')

                d9 = z.read('xl/drawings/drawing9.xml').decode('utf-8')
                root_d9 = ET.fromstring(d9)
                ns = {
                    'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
                    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
                }
                for anchor in root_d9.findall('xdr:oneCellAnchor', ns):
                    frm = anchor.find('xdr:from', ns)
                    blip = anchor.find('.//a:blip', ns)
                    if frm is not None and blip is not None:
                        r = frm.find('xdr:row', ns)
                        embed = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                        if r is not None and embed:
                            row_num = int(r.text) + 1
                            p = rid_to_img.get(embed)
                            if p and p in z.namelist():
                                b = z.read(p)
                                mime = 'image/png' if p.endswith('.png') else 'image/jpeg'
                                b64 = base64.b64encode(b).decode('utf-8')
                                self._images_cache[row_num] = f"data:{mime};base64,{b64}"
        except Exception as e:
            print("Errore estrazione immagini Excel:", e)
        return self._images_cache

    def _read_checklist(self):
        if self._checklist_cache is not None:
            return self._checklist_cache
        self._checklist_cache = []
        try:
            import openpyxl
            wb = openpyxl.load_workbook(self.db_path, data_only=True)
            if 'CHECK LIST' not in wb.sheetnames:
                return self._checklist_cache
            ws = wb['CHECK LIST']
            for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
                if r_idx < 4:
                    continue
                cat = row[0] or ""
                item = row[1]
                if item is None:
                    continue
                is_cb = isinstance(row[2], bool)
                key = row[6] if row[6] is not None else f"{cat} {item}"
                self._checklist_cache.append({
                    'category': str(cat).strip(),
                    'item': str(item).strip(),
                    'key': str(key).strip(),
                    'is_checkbox': is_cb
                })
        except Exception as e:
            print("Errore lettura checklist:", e)
        return self._checklist_cache

    def _read_risks(self):
        if self._risks_cache is not None:
            return self._risks_cache
        self._risks_cache = []
        try:
            import openpyxl
            wb = openpyxl.load_workbook(self.db_path, data_only=True)
            if 'DVR - RISCHI' not in wb.sheetnames:
                return self._risks_cache
            ws = wb['DVR - RISCHI']
            imgs = self._get_images_map()
            for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
                if r_idx < 2:
                    continue
                rn = r_idx + 1
                luogo = row[0] or ""
                rischio = row[1] or ""
                azione = row[2] or ""
                entro = row[4] or ""
                key = row[5] or ""
                raw_ord = row[7] if len(row) > 7 else None
                try:
                    ordine = int(raw_ord) if raw_ord is not None else 999999
                except:
                    ordine = 999999
                img = imgs.get(rn)
                if luogo or rischio or azione:
                    self._risks_cache.append({
                        'luogo': str(luogo).strip(), 'rischio': str(rischio).strip(),
                        'azione': str(azione).strip(), 'entro': str(entro).strip(),
                        'key': str(key).strip(), 'ordine': ordine, 'image': img
                    })
        except Exception as e:
            print("Errore lettura rischi:", e)
        return self._risks_cache

    def get_checklist_items(self):
        return self._read_checklist()

    def get_all_dvr_risks(self):
        risks = self._read_risks()
        risks.sort(key=lambda x: x.get('ordine', 999999))
        return risks

    def match_risks(self, checked_keys: List[str]) -> List[Dict[str, Any]]:
        risks = self.get_all_dvr_risks()
        matched = []
        used = set()
        norm_ck = [self._normalize(k) for k in checked_keys]
        for i, ck in enumerate(checked_keys):
            n = norm_ck[i]
            if not n:
                continue
            for j, r in enumerate(risks):
                if j in used:
                    continue
                nr = self._normalize(r['key'])
                if nr == n or n in nr or nr in n:
                    matched.append({**r, 'key': ck})
                    used.add(j)
                    break
        matched.sort(key=lambda x: x.get('ordine', 999999))
        return matched

    def add_database_risk(self, risk: Dict[str, Any]) -> Dict[str, Any]:
        import openpyxl
        wb = openpyxl.load_workbook(self.db_path)
        ws = wb['DVR - RISCHI']
        ord_val = risk.get('ordine', 999999)
        try:
            ordine = int(ord_val) if ord_val is not None else 999999
        except:
            ordine = 999999
        key_val = risk.get('rischio') or risk.get('luogo') or ""
        new_row = [
            risk.get('luogo', ''),
            risk.get('rischio', ''),
            risk.get('azione', ''),
            None,
            risk.get('entro', ''),
            key_val,
            'FALSO',
            ordine
        ]
        ws.append(new_row)
        wb.save(self.db_path)
        self._risks_cache = None
        return {"success": True, "message": "Criticità salvata in Excel."}

    def _read_users(self):
        if not os.path.exists(self._users_path):
            return []
        try:
            with open(self._users_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _write_users(self, users):
        os.makedirs(os.path.dirname(self._users_path), exist_ok=True)
        with open(self._users_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        users = self._read_users()
        for u in users:
            if u.get('username') == username:
                return u
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        users = self._read_users()
        for u in users:
            if str(u.get('id')) == str(user_id):
                return u
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        return self._read_users()

    def add_user(self, username: str, password_hash: str, role: str = 'user') -> Dict[str, Any]:
        users = self._read_users()
        if any(u.get('username') == username for u in users):
            return {"success": False, "error": "Username già esistente"}
        new_id = max([u.get('id', 0) for u in users], default=0) + 1
        new_user = {
            "id": new_id,
            "username": username,
            "password_hash": password_hash,
            "role": role
        }
        users.append(new_user)
        self._write_users(users)
        return {"success": True, "id": new_id}

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        users = self._read_users()
        users = [u for u in users if str(u.get('id')) != str(user_id)]
        self._write_users(users)
        return {"success": True}

    @staticmethod
    def _normalize(k):
        if not k:
            return ""
        k = str(k).lower().strip()
        k = re.sub(r'\(.*?\)', '', k)
        k = re.sub(r'[^a-z0-9\s]', ' ', k)
        return " ".join(k.split())


class NeonAdapter(DatabaseAdapter):
    def __init__(self, database_url: str):
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        self.database_url = database_url
        self.init_schema()

    def _get_conn(self):
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(self.database_url, cursor_factory=psycopg2.extras.RealDictCursor, connect_timeout=3)
        conn.autocommit = True
        return conn

    def _execute_http(self, sql: str, fetchall=False, fetchone=False):
        import json
        import urllib.request
        parts = self.database_url.split("@")
        host_part = parts[1].split("/")[0].split(":")[0] if len(parts) > 1 else "ep-autumn-darkness-b160gyre-pooler.c-5.eu-central-1.aws.neon.tech"
        endpoint = f"https://{host_part}/sql"

        req = urllib.request.Request(
            endpoint,
            data=json.dumps({"query": sql}).encode("utf-8"),
            headers={
                "Neon-Connection-String": self.database_url,
                "Content-Type": "application/json"
            }
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode("utf-8"))
        if fetchall or fetchone:
            rows = data.get("rows", [])
            if fetchone:
                return rows[0] if rows else None
            return rows
        return None

    def _execute_sql(self, sql: str, fetchall=False, fetchone=False):
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    if fetchall:
                        return cur.fetchall()
                    if fetchone:
                        return cur.fetchone()
                    return None
        except Exception:
            return self._execute_http(sql, fetchall=fetchall, fetchone=fetchone)

    def init_schema(self):
        statements = [
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
        for stmt in statements:
            try:
                self._execute_sql(stmt)
            except Exception as e:
                print("Inizializzazione schema Neon/PostgreSQL:", e)

    def get_checklist_items(self) -> List[Dict[str, Any]]:
        rows = self._execute_sql("SELECT category, item, key, is_checkbox FROM checklist_items ORDER BY category, id;", fetchall=True) or []
        return [
            {
                'category': r['category'] or '',
                'item': r['item'] or '',
                'key': r['key'] or '',
                'is_checkbox': bool(r['is_checkbox'])
            }
            for r in rows
        ]

    def get_all_dvr_risks(self) -> List[Dict[str, Any]]:
        rows = self._execute_sql("SELECT luogo, rischio, azione, entro, key, ordine, image_url FROM dvr_risks ORDER BY ordine, id;", fetchall=True) or []
        return [
            {
                'luogo': r['luogo'] or '',
                'rischio': r['rischio'] or '',
                'azione': r['azione'] or '',
                'entro': r['entro'] or '',
                'key': r['key'] or '',
                'ordine': r['ordine'] if r['ordine'] is not None else 999999,
                'image': r['image_url'] or ''
            }
            for r in rows
        ]

    def match_risks(self, checked_keys: List[str]) -> List[Dict[str, Any]]:
        risks = self.get_all_dvr_risks()
        matched = []
        used = set()
        norm_ck = [self._normalize(k) for k in checked_keys]
        for i, ck in enumerate(checked_keys):
            n = norm_ck[i]
            if not n:
                continue
            for j, r in enumerate(risks):
                if j in used:
                    continue
                nr = self._normalize(r['key'])
                if nr == n or n in nr or nr in n:
                    matched.append({**r, 'key': ck})
                    used.add(j)
                    break
        matched.sort(key=lambda x: x.get('ordine', 999999))
        return matched

    def add_database_risk(self, risk: Dict[str, Any]) -> Dict[str, Any]:
        ord_val = risk.get('ordine', 999999)
        try:
            ordine = int(ord_val) if ord_val is not None else 999999
        except:
            ordine = 999999
        key_val = (risk.get('rischio') or risk.get('luogo') or "").replace("'", "''")
        luogo = (risk.get('luogo') or '').replace("'", "''")
        rischio = (risk.get('rischio') or '').replace("'", "''")
        azione = (risk.get('azione') or '').replace("'", "''")
        entro = (risk.get('entro') or '').replace("'", "''")
        img = (risk.get('image') or '').replace("'", "''")

        sql = f"""
            INSERT INTO dvr_risks (luogo, rischio, azione, entro, key, ordine, image_url)
            VALUES ('{luogo}', '{rischio}', '{azione}', '{entro}', '{key_val}', {ordine}, '{img}')
            RETURNING id;
        """
        row = self._execute_sql(sql, fetchone=True)
        return {"success": True, "message": "Criticità salvata su Neon PostgreSQL.", "id": row['id'] if row and 'id' in row else None}

    @staticmethod
    def _normalize(k):
        if not k:
            return ""
        k = str(k).lower().strip()
        k = re.sub(r'\(.*?\)', '', k)
        k = re.sub(r'[^a-z0-9\s]', ' ', k)
        return " ".join(k.split())

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        u = (username or '').replace("'", "''")
        row = self._execute_sql(f"SELECT id, username, password_hash, role, created_at FROM users WHERE username = '{u}' LIMIT 1;", fetchone=True)
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            row = self._execute_sql(f"SELECT id, username, password_hash, role, created_at FROM users WHERE id = {int(user_id)} LIMIT 1;", fetchone=True)
            return dict(row) if row else None
        except Exception:
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        rows = self._execute_sql("SELECT id, username, role, created_at FROM users ORDER BY username;", fetchall=True) or []
        return [dict(r) for r in rows]

    def add_user(self, username: str, password_hash: str, role: str = 'user') -> Dict[str, Any]:
        try:
            u = (username or '').replace("'", "''")
            p = (password_hash or '').replace("'", "''")
            r = (role or 'user').replace("'", "''")
            row = self._execute_sql(f"INSERT INTO users (username, password_hash, role) VALUES ('{u}', '{p}', '{r}') RETURNING id;", fetchone=True)
            return {"success": True, "id": row['id'] if row and 'id' in row else None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        try:
            self._execute_sql(f"DELETE FROM users WHERE id = {int(user_id)};")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


class SupabaseAdapter(DatabaseAdapter):
    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.client = create_client(url, key)

    def get_checklist_items(self) -> List[Dict[str, Any]]:
        resp = self.client.table("checklist_items").select("*").order("category").execute()
        data = resp.data or []
        return [
            {
                'category': r.get('category', ''),
                'item': r.get('item', ''),
                'key': r.get('key', ''),
                'is_checkbox': r.get('is_checkbox', True)
            }
            for r in data
        ]

    def get_all_dvr_risks(self) -> List[Dict[str, Any]]:
        resp = self.client.table("dvr_risks").select("*").order("ordine").execute()
        data = resp.data or []
        return [
            {
                'luogo': r.get('luogo', ''),
                'rischio': r.get('rischio', ''),
                'azione': r.get('azione', ''),
                'entro': r.get('entro', ''),
                'key': r.get('key', ''),
                'ordine': r.get('ordine', 999999),
                'image': r.get('image_url', '')
            }
            for r in data
        ]

    def match_risks(self, checked_keys: List[str]) -> List[Dict[str, Any]]:
        risks = self.get_all_dvr_risks()
        matched = []
        used = set()
        norm_ck = [self._normalize(k) for k in checked_keys]
        for i, ck in enumerate(checked_keys):
            n = norm_ck[i]
            if not n:
                continue
            for j, r in enumerate(risks):
                if j in used:
                    continue
                nr = self._normalize(r['key'])
                if nr == n or n in nr or nr in n:
                    matched.append({**r, 'key': ck})
                    used.add(j)
                    break
        matched.sort(key=lambda x: x.get('ordine', 999999))
        return matched

    def add_database_risk(self, risk: Dict[str, Any]) -> Dict[str, Any]:
        ord_val = risk.get('ordine', 999999)
        try:
            ordine = int(ord_val) if ord_val is not None else 999999
        except:
            ordine = 999999
        key_val = risk.get('rischio') or risk.get('luogo') or ""
        data = {
            "luogo": risk.get('luogo', ''),
            "rischio": risk.get('rischio', ''),
            "azione": risk.get('azione', ''),
            "entro": risk.get('entro', ''),
            "key": key_val,
            "ordine": ordine,
            "image_url": risk.get('image', '')
        }
        result = self.client.table("dvr_risks").insert(data).execute()
        return {"success": True, "message": "Criticità salvata su Supabase.", "id": result.data[0]['id'] if result.data else None}

    @staticmethod
    def _normalize(k):
        if not k:
            return ""
        k = str(k).lower().strip()
        k = re.sub(r'\(.*?\)', '', k)
        k = re.sub(r'[^a-z0-9\s]', ' ', k)
        return " ".join(k.split())

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        resp = self.client.table("users").select("*").eq("username", username).limit(1).execute()
        data = resp.data or []
        return data[0] if data else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            resp = self.client.table("users").select("*").eq("id", int(user_id)).limit(1).execute()
            data = resp.data or []
            return data[0] if data else None
        except Exception:
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        resp = self.client.table("users").select("id, username, role, created_at").order("username").execute()
        return resp.data or []

    def add_user(self, username: str, password_hash: str, role: str = 'user') -> Dict[str, Any]:
        try:
            resp = self.client.table("users").insert({
                "username": username,
                "password_hash": password_hash,
                "role": role
            }).execute()
            return {"success": True, "id": resp.data[0]['id'] if resp.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        try:
            self.client.table("users").delete().eq("id", user_id).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_adapter(backend: str = "local", **kwargs) -> DatabaseAdapter:
    b = backend.lower()
    if b in ["neon", "postgres", "postgresql"]:
        url = kwargs.get("database_url") or kwargs.get("url") or os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL", "")
        if not url:
            raise ValueError("DATABASE_URL / NEON_DATABASE_URL richiesto per backend='neon'")
        return NeonAdapter(url)
    elif b == "supabase":
        url = kwargs.get("supabase_url") or kwargs.get("url") or os.environ.get("SUPABASE_URL", "")
        key = kwargs.get("supabase_key") or kwargs.get("key") or os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError("Supabase URL e KEY richiesti per backend='supabase'")
        return SupabaseAdapter(url, key)
    elif b == "local":
        db_path = kwargs.get("db_path", "DATABASE.xlsx")
        return ExcelAdapter(db_path)
    else:
        raise ValueError(f"Backend '{backend}' non supportato. Usa 'local', 'neon', o 'supabase'.")
