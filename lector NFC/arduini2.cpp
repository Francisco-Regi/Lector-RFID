#include <SPI.h>
#include <MFRC522.h>

#define PIN_SS   5
#define PIN_RST  4
#define PIN_SCK  18
#define PIN_MISO 19
#define PIN_MOSI 23

MFRC522 mfrc522(PIN_SS, PIN_RST);
MFRC522::MIFARE_Key keyDefault;
MFRC522::MIFARE_Key keyNDEF;

// CLAVE HCE (Celular)
byte SELECT_APDU[] = { 0x00, 0xA4, 0x04, 0x00, 0x07, 0xF0, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x00 };
byte GET_DATA_CMD[] = { 0x80, 0xB0, 0x00, 0x00, 0x00 }; 

void setup() {
  Serial.begin(115200);
  SPI.begin(PIN_SCK, PIN_MISO, PIN_MOSI, PIN_SS);
  mfrc522.PCD_Init();
  
  // Preparamos las dos llaves posibles
  for (byte i = 0; i < 6; i++) keyDefault.keyByte[i] = 0xFF; // Fabrica
  
  // Llave estandar NDEF (Mad)
  keyNDEF.keyByte[0] = 0xD3; keyNDEF.keyByte[1] = 0xF7; keyNDEF.keyByte[2] = 0xD3;
  keyNDEF.keyByte[3] = 0xF7; keyNDEF.keyByte[4] = 0xD3; keyNDEF.keyByte[5] = 0xF7;

  Serial.println("RC522 listo - V6 Multi-Llave");
}

String cleanString(String s) {
  String out = "";
  for (unsigned int i = 0; i < s.length(); i++) {
    char c = s[i];
    if (isAlphaNumeric(c) || c == ' ' || c == '.' || c == '@' || c == '-' || c == '_' || c == '+' || c == '{' || c == '}' || c == ':' || c == '"' || c == ',' || c == '|') {
      out += c;
    }
  }
  out.trim();
  return out;
}

bool tryAndroidHCE() {
  byte response[255];
  byte responseLen = 255;

  // Saludo con CRC activado (true)
  MFRC522::StatusCode status = mfrc522.PCD_TransceiveData(SELECT_APDU, sizeof(SELECT_APDU), response, &responseLen, NULL, 0, true);
  if (status != MFRC522::STATUS_OK) return false;

  if (responseLen >= 2 && response[responseLen-2] == 0x90 && response[responseLen-1] == 0x00) {
      byte dataResp[255];
      byte dataLen = 255;
      status = mfrc522.PCD_TransceiveData(GET_DATA_CMD, sizeof(GET_DATA_CMD), dataResp, &dataLen, NULL, 0, true);

      if (status == MFRC522::STATUS_OK) {
         String jsonRaw = "";
         for(int i=0; i < dataLen - 2; i++) jsonRaw += (char)dataResp[i];
         if (jsonRaw.length() > 5) {
             Serial.print("UID:CELULAR"); Serial.println();
             Serial.print("DATA:"); Serial.println(cleanString(jsonRaw));
             return true;
         }
      }
  }
  return false;
}

// Intenta leer un bloque con una llave especifica
bool tryReadBlock(byte block, byte* buffer, MFRC522::MIFARE_Key key) {
    MFRC522::StatusCode status;
    // Autenticacion
    status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, block, &key, &(mfrc522.uid));
    if (status != MFRC522::STATUS_OK) return false;

    // Lectura
    byte size = 18;
    status = mfrc522.MIFARE_Read(block, buffer, &size);
    if (status != MFRC522::STATUS_OK) return false;
    
    return true;
}

void readAllMemory(byte* buffer, int& index, int maxLen) {
  MFRC522::PICC_Type type = mfrc522.PICC_GetType(mfrc522.uid.sak);
  
  // --- ESTRATEGIA PARA TARJETAS MIFARE CLASSIC (Tarjetas Blancas/Llaveros) ---
  if (type != MFRC522::PICC_TYPE_MIFARE_UL) {
      for (byte sector = 1; sector <= 4; sector++) { 
          byte trailer = sector * 4 + 3;
          byte block = sector * 4; // Leemos el primer bloque del sector
          
          // Intento 1: Llave de Fabrica (FFFF...)
          bool success = false;
          if (mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailer, &keyDefault, &(mfrc522.uid)) == MFRC522::STATUS_OK) {
             success = true;
          } 
          // Intento 2: Llave NDEF (D3F7...) - Si falló la anterior
          else {
             mfrc522.PICC_HaltA(); mfrc522.PCD_StopCrypto1(); // Reiniciar comunicacion para reintentar auth
             mfrc522.PICC_WakeupA(buffer, &index); // Despertar de nuevo (truco tecnico)
             mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailer, &keyNDEF, &(mfrc522.uid));
             success = true; // Asumimos exito para intentar leer, si falla el read lo atrapa abajo
          }

          // Leemos los 3 bloques de datos del sector
          for (byte i = 0; i < 3; i++) {
             byte currentBlock = sector * 4 + i;
             byte temp[18]; byte size = sizeof(temp);
             if (mfrc522.MIFARE_Read(currentBlock, temp, &size) == MFRC522::STATUS_OK) {
                for (byte j = 0; j < 16; j++) if (index < maxLen) buffer[index++] = temp[j];
             }
          }
      }
      mfrc522.PCD_StopCrypto1();
  } 
  // --- ESTRATEGIA PARA ULTRALIGHT (Stickers) ---
  else {
      for (byte page = 4; page < 30; page += 4) { 
         byte temp[18]; byte size = sizeof(temp);
         if (mfrc522.MIFARE_Read(page, temp, &size) == MFRC522::STATUS_OK) {
            for(int i=0; i<16; i++) if (index < maxLen) buffer[index++] = temp[i];
         } else { break; }
      }
  }
}

String extractVal(String data, String label) {
   int idx = data.indexOf(label);
   if (idx == -1) return "";
   int start = idx + label.length();
   int end = data.indexOf('|', start);
   if (end == -1) end = data.length(); 
   if (end - start > 60) end = start + 60; 
   return cleanString(data.substring(start, end));
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  // 1. Celular
  if (tryAndroidHCE()) {
     mfrc522.PICC_HaltA();
     delay(2000);
     return;
  }

  // 2. Tarjeta Física
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  Serial.print("UID:"); Serial.println(uid);

  byte rawBuffer[512]; int rawIndex = 0;
  readAllMemory(rawBuffer, rawIndex, 511);

  String fullData = "";
  for (int i=0; i<rawIndex; i++) {
     char c = (char)rawBuffer[i];
     if (isPrintable(c)) fullData += c; 
  }

  String nombre = extractVal(fullData, "nombre:");
  String correo = extractVal(fullData, "correo:");
  String tel    = extractVal(fullData, "tel:");
  String region = extractVal(fullData, "region:");
  
  if (tel == "") tel = extractVal(fullData, "telefono:");

  if (nombre.length() > 0 || correo.length() > 0) {
    Serial.print("DATA:{\"nombre\":\""); Serial.print(nombre);
    Serial.print("\",\"correo\":\""); Serial.print(correo);
    Serial.print("\",\"telefono\":\""); Serial.print(tel);
    Serial.print("\",\"region\":\""); Serial.print(region);
    Serial.println("\"}");
  }

  mfrc522.PICC_HaltA(); 
  mfrc522.PCD_StopCrypto1();
  delay(1000);
}