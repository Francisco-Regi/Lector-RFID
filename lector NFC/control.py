from typing import List, Tuple, Optional
from modelo import Modelo
from vistaprincipal import MainView
from service_rc522_serial import RC522SerialService
from config import FILL_WITH_UID_IF_UNKNOWN
import time

class Controller:
    def __init__(self):
        self.model = Modelo()
        self.view = MainView()
        self.view.on_guardar = self._on_guardar
        self.view.on_consulta = self._on_consulta
        
        # Estado para controlar lecturas rápidas
        self.last_processed_uid = None
        self.processing_start_time = 0

        # Servicio serie
        self.svc = RC522SerialService(
            on_uid=self._on_uid,
            on_payload=self._on_payload,
            verbose=True
        )
        self.svc.start()

    def _on_uid(self, uid: str):
        # Evitar rebotes simples
        if uid == self.last_processed_uid and (time.time() - self.processing_start_time) < 3.0:
            return
        
        self.last_processed_uid = uid
        self.processing_start_time = time.time()
        
        print(f"Procesando UID: {uid}")

        # 1) Buscar en DB local
        row = self.model.get_latest_by_uid(uid)
        if row:
            nombre, correo, tel = row
            self.view.after(0, lambda: self._append(uid, nombre, correo, tel, f"UID {uid} (Encontrado en DB)"))
            return

        # 2) Si no está en DB, esperamos los datos del Arduino (DATA:...)
        # Le damos al usuario un mensaje visual de "Leyendo memoria..."
        self.view.after(0, lambda: self.view.set_status(f"UID {uid} detectado. Esperando datos de memoria..."))
        
        # Iniciamos un timer: si en 2 segundos no llega DATA, asumimos que está vacía
        self.view.after(2000, lambda: self._check_timeout(uid))

    def _on_payload(self, uid: Optional[str], payload: dict):
        # Si llega esto, el Arduino encontró texto en la tarjeta
        if not uid: return
        
        # Actualizamos la vista inmediatamente
        nombre = (payload.get("nombre") or "").strip()
        correo = (payload.get("correo") or "").strip()
        tel    = (payload.get("telefono") or "").strip()
        
        if nombre or correo or tel:
            self.view.after(0, lambda: self._append(uid, nombre, correo, tel, f"UID {uid} (Leído de Tarjeta)"))

    def _check_timeout(self, uid_checked):
        # Si pasaron 2 segundos y no hemos actualizado la vista con datos reales (chequeo simple)
        # Podrías mejorar esto con banderas, pero para simplificar:
        # Si el usuario quiere, agregamos solo el UID
        if FILL_WITH_UID_IF_UNKNOWN:
            # Solo si no se ha llenado ya (aquí una lógica simple para no duplicar si llegó data justo antes)
             pass # Dejamos que el usuario decida o implementamos lógica más compleja
             # Por ahora, el status se queda en "Esperando..." hasta que el usuario quite la tarjeta
        
    def _append(self, uid: str, nombre: str, correo: str, tel: str, status: str):
        self.view.add_row(uid, nombre, correo, tel)
        self.view.set_status(status)

    def _on_guardar(self):
        if not self.view.buffer:
            self.view.set_status("No hay datos para guardar.")
            return
        n = self.model.save_many(self.view.buffer)
        cerrar = self.view.ask_close_after_save()
        self.view.clear_rows()
        self.view.set_status(f"Guardados {n} registro(s).")
        if cerrar: self.quit()

    def _on_consulta(self):
        data = self.model.fetch_all()
        ConsultaView(self.view, data, on_export=lambda p: self.model.export_to_excel(p))

    def run(self):
        self.view.mainloop()

    def quit(self):
        try: self.svc.stop()
        except: pass
        self.view.destroy()