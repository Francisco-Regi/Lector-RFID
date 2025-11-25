from typing import Optional
from modelo import Modelo
from vistaprincipal import MainView
from view_consulta import ConsultaView
from service_rc522_serial import RC522SerialService
from config import FILL_WITH_UID_IF_UNKNOWN
import time

class Controller:
    def __init__(self):
        self.model = Modelo() # Se conecta a la base de datos
        self.view = MainView()
        
        # Conectamos los botones de la vista a funciones de este controlador
        self.view.on_guardar = self._on_guardar
        self.view.on_consulta = self._on_consulta
        
        # Variables para evitar lecturas dobles del mismo chip en poco tiempo
        self.last_processed_uid = None
        self.processing_start_time = 0

        # Iniciamos la escucha del puerto Serial (Arduino)
        self.svc = RC522SerialService(
            on_uid=self._on_uid,
            on_payload=self._on_payload,
            verbose=True
        )
        self.svc.start()

    def _on_uid(self, uid: str):
        # Lógica anti-rebote (3 segundos de espera entre lecturas de la misma tarjeta)
        if uid == self.last_processed_uid and (time.time() - self.processing_start_time) < 3.0:
            return
        
        self.last_processed_uid = uid
        self.processing_start_time = time.time()
        print(f"--> UID Detectado: {uid}")

        # 1) Verificar si ya existe en la Base de Datos
        row = self.model.get_latest_by_uid(uid)
        if row:
            # Si existe, recuperamos los datos (nombre, correo, tel, region)
            nombre, correo, tel, region = row
            if region is None: region = ""
            
            # Mostramos en la tabla indicando que vino de la BD
            self.view.after(0, lambda: self._append(uid, nombre, correo, tel, region, f"UID {uid} (Encontrado en BD)"))
            return

        # 2) Si es nueva, avisamos que estamos esperando datos del chip NFC
        self.view.after(0, lambda: self.view.set_status(f"Leyendo memoria del Tag {uid}..."))

    #def _on_payload(self, uid: Optional[str], payload: dict):
    #    if not uid: return
        
        # Recibimos el JSON del Arduino con la información leída del chip
    #    nombre = (payload.get("nombre") or "").strip()
    #    correo = (payload.get("correo") or "").strip()
    #    tel    = (payload.get("telefono") or "").strip()
    #    region = (payload.get("region") or "").strip() # Aquí recibimos la Lada (ej: +52)
        
    #    if nombre or correo or tel or region:
    #        print(f"--> Datos recibidos: {nombre}, Lada: {region}")
    #        self.view.after(0, lambda: self._append(uid, nombre, correo, tel, region, f"UID {uid} (Leído del Tag)"))
    #    else:
    #        self.view.after(0, lambda: self.view.set_status(f"Tag {uid} vacío o sin formato."))

    def _on_payload(self, uid: Optional[str], payload: dict):
        if not uid: return
        
        # MODO DIAGNOSTICO: Mostrar qué llegó realmente
        raw = payload.get("raw_content")
        if raw:
            print(f"CONTENIDO CRUDO DE LA TARJETA: {raw}")
            # Intentar extraer datos manualmente del string crudo
            # Buscamos patrones a mano por si el JSON falló
            import re
            nombre = ""
            match = re.search(r"nombre:([a-zA-Z0-9\s]+)", raw)
            if match: nombre = match.group(1)
            
            self.view.after(0, lambda: self._append(uid, f"RAW: {nombre}", "Ver consola", "...", f"UID {uid} (Leído)"))
            return

        # (El resto del código normal...)
        nombre = (payload.get("nombre") or "").strip()
        correo = (payload.get("correo") or "").strip()
        tel    = (payload.get("telefono") or "").strip()
        region = (payload.get("region") or "").strip()
        
        if nombre or correo or tel or region:
            print(f"--> Datos recibidos: {nombre}, Lada: {region}")
            self.view.after(0, lambda: self._append(uid, nombre, correo, tel, region, f"UID {uid} (Leído del Tag)"))

    def _append(self, uid: str, nombre: str, correo: str, tel: str, region: str, status: str):
        # Agregamos a la tabla visual
        self.view.add_row(uid, nombre, correo, tel, region)
        self.view.set_status(status)

    def _on_guardar(self):
        if not self.view.buffer:
            self.view.set_status("No hay datos pendientes para guardar.")
            return
        
        # Guardamos todo el buffer en la BD
        n = self.model.save_many(self.view.buffer)
        self.view.set_status(f"Se guardaron {n} registros.")
        
        # Preguntar si cerrar o limpiar
        if self.view.ask_close_after_save():
            self.quit()
        else:
            self.view.clear_rows()
     

    def _on_consulta(self):
        # Abrimos la ventana de historial
        data = self.model.fetch_all()
        ConsultaView(self.view, data, on_export=lambda p: self.model.export_to_excel(p))

    def run(self):
        self.view.mainloop()

    def quit(self):
        try: self.svc.stop()
        except: pass
        self.view.destroy()