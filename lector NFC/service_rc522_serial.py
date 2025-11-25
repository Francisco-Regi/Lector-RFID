import threading, time, json, re
import serial
from serial.tools import list_ports
from typing import Callable, Optional
from config import SERIAL_PORT, BAUDRATE, SERIAL_TIMEOUT

class RC522SerialService(threading.Thread):
    """
    Servicio robusto para leer Arduino.
    Usa expresiones regulares para encontrar JSONs incluso si hay ruido.
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
        self._last_uid = None

    def stop(self):
        self._stop.set()
        if self.ser:
            try: self.ser.close()
            except: pass

    def _log(self, *args):
        if self.verbose: print("[RC522]", *args)

    def _connect(self):
        # Intentar conectar
        port = SERIAL_PORT
        if port == "AUTO":
            ports = list(list_ports.comports())
            if not ports: return False
            # Priorizar dispositivos con nombres conocidos
            for p in ports:
                if "Arduino" in p.description or "CH340" in p.description or "CP210x" in p.description:
                    port = p.device
                    break
            else:
                port = ports[0].device # Si no, el primero que encuentre
        
        try:
            self._log(f"Conectando a {port}...")
            self.ser = serial.Serial(port, BAUDRATE, timeout=SERIAL_TIMEOUT)
            time.sleep(2) # Esperar reinicio del Arduino
            self._log("Conectado.")
            return True
        except Exception as e:
            self._log(f"Error conectando a {port}: {e}")
            return False

    def run(self):
        while not self._stop.is_set():
            if not self.ser or not self.ser.is_open:
                if not self._connect():
                    time.sleep(2)
                    continue

            try:
                # Leer línea y limpiar basura
                raw = self.ser.readline()
                try:
                    line = raw.decode('utf-8', errors='ignore').strip()
                except:
                    continue

                if not line: continue
                
                self._log(f"RX Raw: {line}") # Ver todo lo que llega para debug

                # 1. Detectar UID
                # Acepta formatos: "UID:123456" o "UID: 123456"
                if "UID:" in line:
                    parts = line.split("UID:")
                    if len(parts) > 1:
                        # Tomar la parte derecha, quitar espacios y tomar solo lo hexadecimal
                        candidate = parts[1].strip().split(" ")[0]
                        if len(candidate) >= 8: # Un UID suele tener al menos 8 chars
                            self._last_uid = candidate
                            self.on_uid(self._last_uid)

                # 2. Detectar JSON (Datos del celular)
                # Usamos Regex para buscar algo que empiece con { y termine con }
                # Esto es mucho más seguro que buscar "DATA:"
                json_match = re.search(r'\{.*\}', line)
                if json_match and self.on_payload:
                    json_str = json_match.group(0)
                    try:
                        data = json.loads(json_str)
                        # Verificamos que tenga al menos un campo clave para confirmar
                        if "nombre" in data or "telefono" in data:
                            self._log("JSON Válido encontrado:", data)
                            self.on_payload(self._last_uid, data)
                    except json.JSONDecodeError:
                        self._log("JSON malformado, ignorando.")

            except Exception as e:
                self._log("Error en loop:", e)
                if self.ser: self.ser.close()
                self.ser = None
                time.sleep(1)