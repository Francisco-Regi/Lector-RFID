import threading, time, json
import serial
from serial.tools import list_ports
from typing import Callable, Optional
from config import SERIAL_PORT, BAUDRATE, SERIAL_TIMEOUT

MAGIC_PREFIXES = ("UID:", "RC522 listo", "DATA:")

class RC522SerialService(threading.Thread):
    """
    Lee líneas del Arduino por Serial.
    - 'UID:ABCDEF...' -> on_uid(uid)
    - 'DATA:{"nombre": "...", "correo": "...", "telefono": "..."}' -> on_payload(uid, dict)
      (uid = último UID leído)
    Autodetecta puerto si SERIAL_PORT = 'AUTO'.
    """
    def __init__(self,
                 on_uid: Callable[[str], None],
                 on_payload: Optional[Callable[[Optional[str], dict], None]] = None,
                 verbose: bool = True):
        super().__init__(daemon=True)
        self.on_uid = on_uid
        self.on_payload = on_payload
        self.verbose = verbose
        self._stop = threading.Event()
        self.ser = None
        self._port = None
        self._last_uid: Optional[str] = None

    def stop(self):
        self._stop.set()
        try:
            if self.ser and self.ser.is_open: self.ser.close()
        except: pass

    def _log(self, *a):
        if self.verbose: print("[RC522]", *a)

    def _open_specific(self, port: str):
        self._log("Intentando abrir", port)
        try:
            s = serial.Serial(port, BAUDRATE, timeout=SERIAL_TIMEOUT)
            t0 = time.time()
            while time.time() - t0 < 2.5:
                line = s.readline().decode(errors="ignore").strip()
                if any(p in line for p in MAGIC_PREFIXES):
                    self._log("Confirmado", port, "->", line)
                    self.ser = s; self._port = port
                    return True
            self._log("Sin handshake en", port, "— usando de todos modos.")
            self.ser = s; self._port = port
            return True
        except Exception as e:
            self._log("No se pudo abrir", port, e)
            return False

    def _auto_detect(self):
        for p in list_ports.comports():
            if self._open_specific(p.device): return True
        return False

    def _ensure_open(self):
        if self.ser and self.ser.is_open: return True
        if SERIAL_PORT and SERIAL_PORT != "AUTO":
            return self._open_specific(SERIAL_PORT)
        return self._auto_detect()

    def run(self):
        while not self._stop.is_set():
            try:
                if not self._ensure_open():
                    self._log("No hay puerto disponible. Reintentando…")
                    time.sleep(1.0); continue

                line = self.ser.readline().decode(errors="ignore").strip()
                if not line:
                    time.sleep(0.02); continue

                self._log("RX:", line)

                if line.startswith("UID:"):
                    uid = line.split(":", 1)[1].strip()
                    if uid:
                        self._last_uid = uid
                        self.on_uid(uid)

                elif line.startswith("DATA:") and self.on_payload:
                    try:
                        payload = json.loads(line[5:].strip())
                        self.on_payload(self._last_uid, payload)
                    except Exception as e:
                        self._log("DATA inválido:", e)

            except Exception as e:
                self._log("Error de lectura:", e)
                try:
                    if self.ser: self.ser.close()
                except: pass
                self.ser = None
                time.sleep(0.5)