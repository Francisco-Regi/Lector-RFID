import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Tuple

Row = Tuple[str, str, str, str]  # (uid, nombre, correo, telefono)

class MainView(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RFID RC522 - Captura")
        self.geometry("760x520")
        self.minsize(720, 480)

        # Encabezado verde
        header = tk.Frame(self, bg="#a6e3a1"); header.pack(fill=tk.X)
        for i, txt in enumerate(("nombre", "correo", "telefono")):
            tk.Label(header, text=txt, bg="#a6e3a1", font=("Segoe UI", 11, "bold")).grid(
                row=0, column=i, sticky="ew", padx=(10 if i==0 else 0, 10), pady=6
            )
            header.grid_columnconfigure(i, weight=1)

        # Tabla + Scroll
        wrap = tk.Frame(self); wrap.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(wrap, columns=("nombre","correo","telefono"), show="headings", height=15)
        self.tree.heading("nombre", text="nombre completo")
        self.tree.heading("correo", text="correo")
        self.tree.heading("telefono", text="telefono")
        self.tree.column("nombre", width=300, anchor="w")
        self.tree.column("correo", width=240, anchor="w")
        self.tree.column("telefono", width=160, anchor="center")

        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Botones inferiores
        bottom = tk.Frame(self); bottom.pack(fill=tk.X, pady=4)
        self.btn_consulta = ttk.Button(bottom, text="consulta")
        self.btn_guardar = ttk.Button(bottom, text="guardar")
        self.btn_consulta.pack(side=tk.LEFT, padx=6)
        self.btn_guardar.pack(side=tk.LEFT, padx=6)

        # Estado
        self.status = tk.Label(self, text="Esperando tag...", anchor="w")
        self.status.pack(fill=tk.X, padx=8, pady=2)

        # Callbacks (los asigna el controlador)
        self.on_guardar: Callable[[], None] = lambda: None
        self.on_consulta: Callable[[], None] = lambda: None
        self.btn_guardar.configure(command=self.on_guardar)
        self.btn_consulta.configure(command=self.on_consulta)

        # Buffer (oculto) que incluye el UID junto a lo visible
        self.buffer: List[Row] = []

    # ---- API usada por el controlador ----
    def add_row(self, uid: str, nombre: str, correo: str, telefono: str):
        self.tree.insert("", "end", values=(nombre, correo, telefono))
        self.buffer.append((uid, nombre, correo, telefono))

    def clear_rows(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.buffer.clear()

    def ask_close_after_save(self) -> bool:
        return messagebox.askyesno(
            "Cerrar sistema",
            "Los datos se guardarán. ¿Deseas cerrar el sistema?"
        )

    def set_status(self, text: str):
        self.status.config(text=text)
