import tkinter as tk
from tkinter import ttk, filedialog
from typing import List, Tuple, Callable

class ConsultaView(tk.Toplevel):
    def __init__(self, parent, data: List[Tuple], on_export: Callable[[str], None]):
        super().__init__(parent)
        self.title("Historial de Registros")
        self.geometry("1000x600")

        # Definimos columnas incluyendo 'region' (Lada)
        cols = ("nombre", "correo", "telefono", "region", "creado_en")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        
        # Configuración de encabezados
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("correo", text="Correo")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("region", text="Lada")
        self.tree.heading("creado_en", text="Fecha y Hora")
        
        # Configuración de anchos de columna
        self.tree.column("nombre", width=250)
        self.tree.column("correo", width=250)
        self.tree.column("telefono", width=120)
        self.tree.column("region", width=60, anchor="center")
        self.tree.column("creado_en", width=150)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Barra de desplazamiento vertical
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Llenamos la tabla con los datos recibidos
        # La tupla 'data' trae: (id, uid, nombre, correo, telefono, region, creado_en)
        # Usamos slicing row[2:] para saltarnos el ID y el UID (índices 0 y 1) y mostrar solo lo relevante
        for row in data:
            self.tree.insert("", "end", values=row[2:])

        # Botonera inferior
        bottom = tk.Frame(self, pady=10); bottom.pack(fill=tk.X)
        ttk.Button(bottom, text="Exportar a Excel", command=self._export).pack(side=tk.RIGHT, padx=20)
        
        # Guardamos la función de exportar que nos pasa el controlador
        self._on_export = on_export

    def _export(self):
        # Abrir diálogo para guardar archivo
        path = filedialog.asksaveasfilename(
            title="Guardar reporte",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )
        if path:
            # Llamamos a la función del modelo (vía controlador) para crear el Excel
            self._on_export(path)