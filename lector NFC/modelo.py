import sqlite3
from datetime import datetime
from openpyxl import Workbook
from typing import List, Tuple, Optional

Record = Tuple[str, str, str, str]  # (uid, nombre, correo, telefono)

class Modelo:
    def __init__(self, db_path: str = "registros.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL,
                telefono TEXT NOT NULL,
                creado_en TEXT NOT NULL
            )
        """)
        con.commit(); con.close()

    def save_many(self, rows: List[Record]) -> int:
        if not rows: return 0
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        cur.executemany(
            "INSERT INTO registros (uid, nombre, correo, telefono, creado_en) VALUES (?, ?, ?, ?, ?)",
            [(uid, n, c, t, now) for (uid, n, c, t) in rows]
        )
        con.commit(); n = cur.rowcount; con.close()
        return n

    def fetch_all(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT id, uid, nombre, correo, telefono, creado_en FROM registros ORDER BY id DESC")
        data = cur.fetchall(); con.close()
        return data

    def export_to_excel(self, xlsx_path: str):
        data = self.fetch_all()
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active; ws.title = "Registros"
        ws.append(["ID", "UID", "Nombre", "Correo", "Teléfono", "Creado en"])
        for row in data: ws.append(list(row))
        wb.save(xlsx_path)

    # --- NUEVO: traer el último registro guardado para ese UID ---
    def get_latest_by_uid(self, uid: str) -> Optional[Tuple[str, str, str]]:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT nombre, correo, telefono FROM registros WHERE uid=? ORDER BY id DESC LIMIT 1",
            (uid,)
        )
        row = cur.fetchone(); con.close()
        return row  # None si no existe
