import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

class Formulario(tk.Toplevel):
    def __init__(self, parent, uid: str, on_ok: Callable[[str, str, str, str], None]):
        super().__init__(parent)
        self.title(f"Capturar datos (UID {uid})")
        self.geometry("450x300")
        self.resizable(False, False)
        self.grab_set()

        tk.Label(self, text=f"Registro Manual - UID: {uid}", font=("Segoe UI", 10, "bold")).pack(pady=(15, 10))

        frm = tk.Frame(self)
        frm.pack(fill=tk.X, padx=20)

        # --- Campos ---
        # Nombre
        tk.Label(frm, text="Nombre completo").grid(row=0, column=0, sticky="w", pady=5)
        self.e_nombre = ttk.Entry(frm, width=35)
        self.e_nombre.grid(row=0, column=1, padx=10, pady=5)

        # Correo
        tk.Label(frm, text="Correo").grid(row=1, column=0, sticky="w", pady=5)
        self.e_correo = ttk.Entry(frm, width=35)
        self.e_correo.grid(row=1, column=1, padx=10, pady=5)

        # Lada (Combobox) - NUEVO CAMPO
        tk.Label(frm, text="Lada / País").grid(row=2, column=0, sticky="w", pady=5)
        self.cb_lada = ttk.Combobox(frm, values=["+52", "+1", "+34", "+57", "+54", "+56", "+51"], width=10, state="readonly")
        self.cb_lada.current(0) # Seleccionar +52 por defecto
        self.cb_lada.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        # Teléfono
        tk.Label(frm, text="Teléfono").grid(row=3, column=0, sticky="w", pady=5)
        self.e_tel = ttk.Entry(frm, width=35)
        self.e_tel.grid(row=3, column=1, padx=10, pady=5)

        # --- Botones ---
        btns = tk.Frame(self)
        btns.pack(pady=20)
        
        ttk.Button(btns, text="Agregar", command=lambda: self._ok(on_ok)).pack(side=tk.LEFT, padx=10)
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _ok(self, on_ok):
        n = self.e_nombre.get().strip()
        c = self.e_correo.get().strip()
        t = self.e_tel.get().strip()
        r = self.cb_lada.get().strip() # Obtenemos la Lada

        if not (n and c and t and r):
            messagebox.showwarning("Faltan datos", "Por favor completa todos los campos.")
            return
        
        # Enviamos los 4 valores: nombre, correo, telefono, region
        on_ok(n, c, t, r)
        self.destroy()