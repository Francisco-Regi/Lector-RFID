import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Tuple

# Definimos la estructura de una fila: (uid, nombre, correo, telefono, region)
Row = Tuple[str, str, str, str, str]

class MainView(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Registro RFID/NFC")
        self.geometry("950x550")
        self.minsize(850, 480)

        # Configuración de estilos
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=25)

        # --- Encabezado Verde ---
        header = tk.Frame(self, bg="#4ade80", height=40); header.pack(fill=tk.X)
        header.pack_propagate(False) # Evita que el frame se encoja
        
        lbl = tk.Label(header, text="CONTROL DE ACCESO Y REGISTRO", bg="#4ade80", fg="white", font=("Segoe UI", 12, "bold"))
        lbl.pack(side=tk.LEFT, padx=15)

        # --- Tabla Central ---
        wrap = tk.Frame(self); wrap.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Columnas de la tabla (interno)
        cols = ("nombre","correo","telefono","region")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", height=15)
        
        # Encabezados visibles
        self.tree.heading("nombre", text="NOMBRE COMPLETO")
        self.tree.heading("correo", text="CORREO ELECTRÓNICO")
        self.tree.heading("telefono", text="TELÉFONO")
        self.tree.heading("region", text="LADA")
        
        # Ancho de columnas
        self.tree.column("nombre", width=260)
        self.tree.column("correo", width=240)
        self.tree.column("telefono", width=140, anchor="center")
        self.tree.column("region", width=80, anchor="center")

        # Scrollbar
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Panel de Botones Inferior ---
        bottom = tk.Frame(self, bg="#f1f5f9", height=60); bottom.pack(fill=tk.X, pady=0)
        
        self.btn_consulta = ttk.Button(bottom, text="📂 Ver Historial")
        self.btn_guardar = ttk.Button(bottom, text="💾 Guardar Registros")
        
        self.btn_consulta.pack(side=tk.LEFT, padx=15, pady=15)
        self.btn_guardar.pack(side=tk.LEFT, padx=5, pady=15)

        # --- Barra de Estado ---
        self.status_bar = tk.Label(self, text="Esperando lectura de tarjeta...", bd=1, relief=tk.SUNKEN, anchor="w", bg="#e2e8f0", font=("Segoe UI", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Placeholders para los callbacks del controlador
        self.on_guardar: Callable[[], None] = lambda: None
        self.on_consulta: Callable[[], None] = lambda: None
        self.btn_guardar.configure(command=self.on_guardar)
        self.btn_consulta.configure(command=self.on_consulta)

        # Memoria temporal de datos
        self.buffer: List[Row] = []

    def add_row(self, uid: str, nombre: str, correo: str, telefono: str, region: str):
        # Insertar visualmente al principio
        self.tree.insert("", "0", values=(nombre, correo, telefono, region))
        # Guardar en memoria
        self.buffer.append((uid, nombre, correo, telefono, region))

    def clear_rows(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.buffer.clear()

    def ask_close_after_save(self) -> bool:
        return messagebox.askyesno("Guardado Exitoso", "Los datos han sido guardados.\n¿Deseas salir del sistema?")

    def set_status(self, text: str):
        self.status_bar.config(text=f" {text}")