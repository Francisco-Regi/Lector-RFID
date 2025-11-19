# Puerto serie. Déjalo en "AUTO" para autodetectar.
SERIAL_PORT = "AUTO"          # "COM3" en Windows, "/dev/ttyACM0" en Linux, etc.
BAUDRATE = 115200
SERIAL_TIMEOUT = 0.2  # segundos

# Comportamiento cuando llega un UID que no está en DB y no llega DATA:
PROMPT_ON_UNKNOWN_UID = False       # <- SIN ventana (lo que pediste)
FILL_WITH_UID_IF_UNKNOWN = True     # <- agrega una fila usando el UID como "nombre"
