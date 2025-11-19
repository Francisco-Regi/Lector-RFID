import tkinter as tk
from tkinter import ttk, filedialog
from typing import List, Tuple, Callable

# fila: (id, uid, nombre, correo, telefono, creado_en)
class ConsultaView(tk.Toplevel):
    def __init__(self, parent, data: List[Tuple], on_export: Callable[[str], None]):
        super().__init__(parent)
        self.title("Consulta de registros")
        self.geometry("820x520")
        self.minsize(740, 480)

        cols = ("nombre", "correo", "telefono", "creado_en")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("nombre", text="Nombre completo")
        self.tree.heading("correo", text="Correo")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("creado_en", text="Creado en")
        for c, w in (("nombre", 260), ("correo", 240), ("telefono", 120), ("creado_en", 160)):
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        for _id, _uid, n, c, t, f in data:
            self.tree.insert("", "end", values=(n, c, t, f))

        bottom = tk.Frame(self); bottom.pack(fill=tk.X, pady=6)
        ttk.Button(bottom, text="descargar", command=self._export).pack(side=tk.RIGHT, padx=6)
        ttk.Button(bottom, text="cerrar", command=self.destroy).pack(side=tk.RIGHT, padx=6)
        self._on_export = on_export

    def _export(self):
        path = filedialog.asksaveasfilename(
            title="Guardar como Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if path:
            self._on_export(path)
