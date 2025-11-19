import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

class CaptureDialog(tk.Toplevel):
    def __init__(self, parent, uid: str, on_ok: Callable[[str, str, str], None]):
        super().__init__(parent)
        self.title(f"Capturar datos (UID {uid})")
        self.geometry("420x240"); self.resizable(False, False)
        self.grab_set()

        tk.Label(self, text=f"UID: {uid}", font=("Segoe UI", 10, "bold")).pack(pady=(10, 6))

        frm = tk.Frame(self); frm.pack(fill=tk.X, padx=12)
        tk.Label(frm, text="Nombre completo").grid(row=0, column=0, sticky="w")
        tk.Label(frm, text="Correo").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Label(frm, text="Teléfono").grid(row=2, column=0, sticky="w", pady=(8, 0))

        self.e_nombre = ttk.Entry(frm, width=40); self.e_nombre.grid(row=0, column=1, padx=6)
        self.e_correo = ttk.Entry(frm, width=40); self.e_correo.grid(row=1, column=1, padx=6, pady=(8, 0))
        self.e_tel    = ttk.Entry(frm, width=40); self.e_tel.grid(row=2, column=1, padx=6, pady=(8, 0))

        btns = tk.Frame(self); btns.pack(pady=12)
        ttk.Button(btns, text="Agregar", command=lambda: self._ok(on_ok)).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=6)

    def _ok(self, on_ok):
        n = self.e_nombre.get().strip()
        c = self.e_correo.get().strip()
        t = self.e_tel.get().strip()
        if not (n and c and t):
            messagebox.showwarning("Faltan datos", "Completa todos los campos.")
            return
        on_ok(n, c, t)
        self.destroy()
