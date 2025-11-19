#include <SPI.h>
#include <MFRC522.h>

// ---- Pines ESP32 (VSPI) ----
#define PIN_SS   5
#define PIN_RST  4
#define PIN_SCK  18
#define PIN_MISO 19
#define PIN_MOSI 23

MFRC522 mfrc522(PIN_SS, PIN_RST);
MFRC522::MIFARE_Key keyA;

// --- Helpers ---
String bytesToHex(const byte* b, byte len) {
  String s = "";
  for (byte i = 0; i < len; i++) {
    if (b[i] < 0x10) s += "0";
    s += String(b[i], HEX);
  }
  s.toUpperCase();
  return s;
}

// Limpia caracteres no imprimibles que rompen el JSON
String cleanString(String s) {
  String out = "";
  for (unsigned int i = 0; i < s.length(); i++) {
    char c = s[i];
    if (isAlphaNumeric(c) || isPunct(c) || c == ' ') {
      out += c;
    }
  }
  out.trim();
  return out;
}

void setup() {
  Serial.begin(115200);
  SPI.begin(PIN_SCK, PIN_MISO, PIN_MOSI, PIN_SS);
  mfrc522.PCD_Init();
  
  // Clave por defecto 0xFFFFFFFFFFFF
  for (byte i = 0; i < 6; i++) keyA.keyByte[i] = 0xFF;
  
  Serial.println("RC522 listo");
}

// Lee bloques MIFARE Classic (Sectores 1 y 2 suelen tener los datos NDEF simples)
bool readSector(byte sector, byte* buffer, byte& index, int maxLen) {
  byte trailerBlock = sector * 4 + 3;
  MFRC522::StatusCode status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &keyA, &(mfrc522.uid));
  
  if (status != MFRC522::STATUS_OK) {
    return false;
  }

  for (byte i = 0; i < 3; i++) { // Bloques 0, 1, 2 del sector
    byte blockAddr = sector * 4 + i;
    byte tempBuf[18];
    byte size = sizeof(tempBuf);
    status = mfrc522.MIFARE_Read(blockAddr, tempBuf, &size);
    if (status == MFRC522::STATUS_OK) {
      for (byte j = 0; j < 16; j++) {
        if (index < maxLen) buffer[index++] = tempBuf[j];
      }
    }
  }
  
  mfrc522.PCD_StopCrypto1(); // Importante parar crypto por sector
  return true;
}

void loop() {
  // Resetear loop si no hay tarjeta
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    delay(50);
    return;
  }

  String uid = bytesToHex(mfrc522.uid.uidByte, mfrc522.uid.size);
  Serial.print("UID:"); Serial.println(uid);

  // Intentar leer datos (Solo Mifare Classic 1K/4K por simplicidad del ejemplo)
  // Para Ultralight (stickers baratos) la lógica es leer páginas 4 en adelante.
  MFRC522::PICC_Type piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
  
  String fullData = "";
  byte rawBuffer[256]; // Buffer temporal
  byte rawIndex = 0;

  if (piccType == MFRC522::PICC_TYPE_MIFARE_1K) {
    // Leemos sectores 1, 2 y 3 donde suele estar el mensaje NDEF
    readSector(1, rawBuffer, rawIndex, 255);
    readSector(2, rawBuffer, rawIndex, 255);
    readSector(3, rawBuffer, rawIndex, 255);
  } 
  else if (piccType == MFRC522::PICC_TYPE_MIFARE_UL) {
    // Lectura para stickers Ultralight (comunes en celulares)
    for (byte page = 4; page < 20; page += 4) { 
       byte buffer[18];
       byte size = sizeof(buffer);
       if (mfrc522.MIFARE_Read(page, buffer, &size) == MFRC522::STATUS_OK) {
         for(int i=0; i<16; i++) {
            if (rawIndex < 255) rawBuffer[rawIndex++] = buffer[i];
         }
       }
    }
  }

  // Convertir buffer a String limpiando caracteres raros para buscar
  // Convertimos todo a char imprimible para buscar las keywords
  for (int i=0; i<rawIndex; i++) {
     char c = (char)rawBuffer[i];
     if (isPrintable(c)) fullData += c;
     else fullData += " "; // Reemplazar bytes de control con espacio
  }

  // Búsqueda "sucia" pero efectiva para el formato: nombre:Juan
  // La WebApp escribe: "en..nombre:Juan..correo:xx..tel:xx"
  
  String nombre = "";
  String correo = "";
  String tel = "";

  // Helper lambdas para extraer
  auto extractVal = [&](String label) -> String {
    int idx = fullData.indexOf(label);
    if (idx == -1) return "";
    int start = idx + label.length();
    // Buscamos hasta el próximo label o fin de linea
    int end = start;
    while (end < fullData.length()) {
       // Detenerse si encontramos otra etiqueta conocida o caracter extraño
       if (fullData.substring(end).startsWith("correo:")) break;
       if (fullData.substring(end).startsWith("tel:")) break;
       if (fullData.substring(end).startsWith("nombre:")) break;
       end++;
    }
    return cleanString(fullData.substring(start, end));
  };

  nombre = extractVal("nombre:");
  correo = extractVal("correo:");
  tel    = extractVal("tel:");
  
  // Fallback: intentar "telefono:" si "tel:" no existe
  if (tel == "") tel = extractVal("telefono:");

  if (nombre.length() > 0 || correo.length() > 0) {
    Serial.print("DATA:{\"nombre\":\"");
    Serial.print(nombre);
    Serial.print("\",\"correo\":\"");
    Serial.print(correo);
    Serial.print("\",\"telefono\":\"");
    Serial.print(tel);
    Serial.println("\"}");
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  delay(2000); // Evitar lecturas múltiples muy rápidas
}