import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional

# Estructura: (uid, nombre, correo, telefono, region)
Record = Tuple[str, str, str, str, str]

class Modelo:
    def __init__(self, db_path: str = "registros_final.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        # Creamos la tabla con la columna 'region' para guardar la Lada
        cur.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL,
                telefono TEXT NOT NULL,
                region TEXT NOT NULL,
                creado_en TEXT NOT NULL
            )
        """)
        con.commit(); con.close()

    def save_many(self, rows: List[Record]) -> int:
        if not rows: return 0
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        # Insertamos los 5 campos de datos + fecha
        cur.executemany(
            "INSERT INTO registros (uid, nombre, correo, telefono, region, creado_en) VALUES (?, ?, ?, ?, ?, ?)",
            [(uid, n, c, t, r, now) for (uid, n, c, t, r) in rows]
        )
        con.commit(); n = cur.rowcount; con.close()
        return n

    def fetch_all(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        # Leemos todo para la consulta
        cur.execute("SELECT id, uid, nombre, correo, telefono, region, creado_en FROM registros ORDER BY id DESC")
        data = cur.fetchall(); con.close()
        return data

    def export_to_excel(self, xlsx_path: str):
        data = self.fetch_all()
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active; ws.title = "Registros"
        ws.append(["ID", "UID", "Nombre", "Correo", "Teléfono", "Lada", "Creado en"])
        for row in data: ws.append(list(row))
        wb.save(xlsx_path)

    def get_latest_by_uid(self, uid: str) -> Optional[Tuple[str, str, str, str]]:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        # Buscamos si ya existe este UID
        cur.execute(
            "SELECT nombre, correo, telefono, region FROM registros WHERE uid=? ORDER BY id DESC LIMIT 1",
            (uid,)
        )
        row = cur.fetchone(); con.close()
        return row