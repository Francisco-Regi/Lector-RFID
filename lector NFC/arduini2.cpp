#include <SPI.h>
#include <MFRC522.h>

#define PIN_SS   5
#define PIN_RST  4
#define PIN_SCK  18
#define PIN_MISO 19
#define PIN_MOSI 23

MFRC522 mfrc522(PIN_SS, PIN_RST);
MFRC522::MIFARE_Key keyA;

// CLAVE HCE (F0010203040506)
byte SELECT_APDU[] = { 0x00, 0xA4, 0x04, 0x00, 0x07, 0xF0, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x00 };
byte GET_DATA_CMD[] = { 0x80, 0xB0, 0x00, 0x00, 0x00 }; 

void setup() {
  Serial.begin(115200);
  SPI.begin(PIN_SCK, PIN_MISO, PIN_MOSI, PIN_SS);
  mfrc522.PCD_Init();
  for (byte i = 0; i < 6; i++) keyA.keyByte[i] = 0xFF;
  Serial.println("RC522 listo - V4 con CRC");
}

String cleanString(String s) {
  String out = "";
  for (unsigned int i = 0; i < s.length(); i++) {
    char c = s[i];
    if (isAlphaNumeric(c) || c == ' ' || c == '.' || c == '@' || c == '-' || c == '_' || c == '+' || c == '{' || c == '}' || c == ':' || c == '"' || c == ',') {
      out += c;
    }
  }
  out.trim();
  return out;
}

bool tryAndroidHCE() {
  byte response[255];
  byte responseLen = 255;

  // 1. Saludo (SELECT AID)
  // IMPORTANTE: El ultimo parametro 'true' activa el chequeo CRC, obligatorio para Android
  MFRC522::StatusCode status = mfrc522.PCD_TransceiveData(
    SELECT_APDU, sizeof(SELECT_APDU),
    response, &responseLen,
    NULL, 0, true 
  );

  if (status != MFRC522::STATUS_OK) {
     // Descomenta esta linea si quieres ver si falla el saludo:
     // Serial.println("DEBUG: HCE Select fallo (Error CRC o Timeout)");
     return false; 
  }

  // 2. Verificar respuesta 90 00 (OK)
  if (responseLen >= 2 && response[responseLen-2] == 0x90 && response[responseLen-1] == 0x00) {
      Serial.println("DEBUG: HCE OK - Pidiendo datos...");
      
      byte dataResp[255];
      byte dataLen = 255;
      
      // 3. Pedir Datos
      status = mfrc522.PCD_TransceiveData(
        GET_DATA_CMD, sizeof(GET_DATA_CMD),
        dataResp, &dataLen,
        NULL, 0, true // CRC true aqui tambien
      );

      if (status == MFRC522::STATUS_OK) {
         String jsonRaw = "";
         for(int i=0; i < dataLen - 2; i++) jsonRaw += (char)dataResp[i];
         
         Serial.print("UID:CELULAR_ANDROID"); 
         Serial.println();
         Serial.print("DATA:");
         Serial.println(cleanString(jsonRaw));
         return true;
      } else {
         Serial.println("DEBUG: Fallo GET_DATA");
      }
  }
  return false;
}

void readAllMemory(byte* buffer, int& index, int maxLen) {
  // Lógica para tarjetas físicas (Mifare/NTAG)
  MFRC522::PICC_Type type = mfrc522.PICC_GetType(mfrc522.uid.sak);
  if (type == MFRC522::PICC_TYPE_MIFARE_UL) {
      for (byte page = 4; page < 30; page += 4) { 
         byte temp[18]; byte size = sizeof(temp);
         if (mfrc522.MIFARE_Read(page, temp, &size) == MFRC522::STATUS_OK) {
            for(int i=0; i<16; i++) if (index < maxLen) buffer[index++] = temp[i];
         } else { break; }
      }
  } else {
      for (byte sector = 1; sector <= 4; sector++) { 
          byte trailerBlock = sector * 4 + 3;
          if (mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &keyA, &(mfrc522.uid)) != MFRC522::STATUS_OK) continue;
          for (byte i = 0; i < 3; i++) { 
             byte block = sector * 4 + i;
             byte temp[18]; byte size = sizeof(temp);
             if (mfrc522.MIFARE_Read(block, temp, &size) == MFRC522::STATUS_OK) {
                for (byte j = 0; j < 16; j++) if (index < maxLen) buffer[index++] = temp[j];
             }
          }
      }
      mfrc522.PCD_StopCrypto1();
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

  // 1. Intentar HCE (Celular)
  if (tryAndroidHCE()) {
     mfrc522.PICC_HaltA();
     delay(2000);
     return;
  }

  // 2. Si no es celular, intentar lectura normal
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