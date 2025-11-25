#include <SPI.h>
#include <MFRC522.h>

#define PIN_SS   5
#define PIN_RST  4
MFRC522 mfrc522(PIN_SS, PIN_RST);
MFRC522::MIFARE_Key keyDefault;
MFRC522::MIFARE_Key keyNDEF;

// CLAVE HCE (Celular)
byte SELECT_APDU[] = { 0x00, 0xA4, 0x04, 0x00, 0x07, 0xF0, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x00 };
byte GET_DATA_CMD[] = { 0x80, 0xB0, 0x00, 0x00, 0x00 }; 

void setup() {
  Serial.begin(115200);
  SPI.begin(18, 19, 23, 5);
  mfrc522.PCD_Init();
  for (byte i = 0; i < 6; i++) keyDefault.keyByte[i] = 0xFF;
  keyNDEF.keyByte[0] = 0xD3; keyNDEF.keyByte[1] = 0xF7; keyNDEF.keyByte[2] = 0xD3;
  keyNDEF.keyByte[3] = 0xF7; keyNDEF.keyByte[4] = 0xD3; keyNDEF.keyByte[5] = 0xF7;
  Serial.println("RC522 Debug Raw");
}

String cleanString(String s) {
  String out = "";
  for (unsigned int i = 0; i < s.length(); i++) {
    char c = s[i];
    if (isAlphaNumeric(c) || c == ' ' || c == ':' || c == '@' || c == '.' || c == '-' || c == '_' || c == '+' || c == '|' || c == '{' || c == '}' || c == '"') {
      out += c;
    } else {
      out += "."; // Reemplazar basura con puntos
    }
  }
  return out;
}

bool tryAndroidHCE() {
  byte response[255]; byte len = 255;
  if (mfrc522.PCD_TransceiveData(SELECT_APDU, sizeof(SELECT_APDU), response, &len, NULL, 0, true) != MFRC522::STATUS_OK) return false;
  
  if (len >= 2 && response[len-2] == 0x90) {
      byte data[255]; byte dlen = 255;
      if (mfrc522.PCD_TransceiveData(GET_DATA_CMD, sizeof(GET_DATA_CMD), data, &dlen, NULL, 0, true) == MFRC522::STATUS_OK) {
         String raw = "";
         for(int i=0; i < dlen - 2; i++) raw += (char)data[i];
         Serial.print("UID:CELULAR_DEBUG"); Serial.println();
         Serial.print("DATA:{\"raw_content\":\"");
         Serial.print(cleanString(raw));
         Serial.println("\"}");
         return true;
      }
  }
  return false;
}

void readAllMemory() {
  MFRC522::PICC_Type type = mfrc522.PICC_GetType(mfrc522.uid.sak);
  String fullText = "";

  // Leer primeros 4 sectores (Mifare Classic)
  if (type != MFRC522::PICC_TYPE_MIFARE_UL) {
      for (byte s = 1; s <= 4; s++) { 
          byte t = s * 4 + 3;
          // Probar llave NDEF primero (la más probable si usaste celular para grabar)
          byte atqa[2]; byte len=2; mfrc522.PICC_WakeupA(atqa, &len);
          if (mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, t, &keyNDEF, &(mfrc522.uid)) != MFRC522::STATUS_OK) {
             // Si falla, probar Default
             mfrc522.PICC_HaltA(); mfrc522.PCD_StopCrypto1(); mfrc522.PICC_WakeupA(atqa, &len);
             if (mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, t, &keyDefault, &(mfrc522.uid)) != MFRC522::STATUS_OK) continue;
          }
          for (byte i = 0; i < 3; i++) {
             byte b[18]; byte sz = 18;
             if (mfrc522.MIFARE_Read(s * 4 + i, b, &sz) == MFRC522::STATUS_OK) {
                for (byte j = 0; j < 16; j++) fullText += (char)b[j];
             }
          }
      }
  } else { // Ultralight
      for (byte p = 4; p < 40; p += 4) { 
         byte b[18]; byte sz = 18;
         if (mfrc522.MIFARE_Read(p, b, &sz) == MFRC522::STATUS_OK) {
            for(int i=0; i<16; i++) fullText += (char)b[i];
         }
      }
  }
  
  // Mandar TODO lo que encontró a Python, aunque sea basura
  Serial.print("DATA:{\"raw_content\":\"");
  Serial.print(cleanString(fullText));
  Serial.println("\"}");
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  if (tryAndroidHCE()) { mfrc522.PICC_HaltA(); delay(2000); return; }

  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  Serial.print("UID:"); Serial.println(uid);

  readAllMemory();

  mfrc522.PICC_HaltA(); 
  mfrc522.PCD_StopCrypto1();
  delay(2000);
}