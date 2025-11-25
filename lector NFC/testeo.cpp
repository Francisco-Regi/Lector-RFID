#include <SPI.h>
#include <MFRC522.h>

#define PIN_SS   5
#define PIN_RST  4
MFRC522 mfrc522(PIN_SS, PIN_RST);
MFRC522::MIFARE_Key keyA;

void setup() {
  Serial.begin(115200);
  SPI.begin(18, 19, 23, 5); // SCK, MISO, MOSI, SS
  mfrc522.PCD_Init();
  for (byte i = 0; i < 6; i++) keyA.keyByte[i] = 0xFF;
  Serial.println("--- MODO DIAGNOSTICO ---");
  Serial.println("Acerca una tarjeta o celular para ver su contenido RAW...");
}

void dumpMemory() {
  MFRC522::PICC_Type type = mfrc522.PICC_GetType(mfrc522.uid.sak);
  String rawContent = "";
  
  // Leer Mifare Classic (Sectores 1 y 2)
  if (type != MFRC522::PICC_TYPE_MIFARE_UL) {
      for (byte sector = 1; sector <= 2; sector++) {
          byte trailer = sector * 4 + 3;
          if (mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailer, &keyA, &(mfrc522.uid)) == MFRC522::STATUS_OK) {
              for (byte b = 0; b < 3; b++) {
                  byte buffer[18]; byte size = sizeof(buffer);
                  if (mfrc522.MIFARE_Read(sector * 4 + b, buffer, &size) == MFRC522::STATUS_OK) {
                      for (byte i = 0; i < 16; i++) {
                          if (isPrintable((char)buffer[i])) rawContent += (char)buffer[i];
                          else rawContent += ".";
                      }
                  }
              }
          }
      }
  } 
  // Leer Ultralight (Stickers / Celulares viejos)
  else {
      for (byte page = 4; page < 20; page += 4) {
          byte buffer[18]; byte size = sizeof(buffer);
          if (mfrc522.MIFARE_Read(page, buffer, &size) == MFRC522::STATUS_OK) {
              for (byte i = 0; i < 16; i++) {
                  if (isPrintable((char)buffer[i])) rawContent += (char)buffer[i];
                  else rawContent += ".";
              }
          }
      }
  }
  
  Serial.println("\n--- CONTENIDO ENCONTRADO ---");
  Serial.println(rawContent);
  Serial.println("----------------------------");
  
  // Verificamos si tiene el formato correcto
  if (rawContent.indexOf("nombre:") != -1) Serial.println("✅ FORMATO CORRECTO DETECTADO");
  else Serial.println("❌ FORMATO INCORRECTO O TARJETA VACIA");
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  Serial.print("UID LEIDO: ");
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(mfrc522.uid.uidByte[i], HEX);
  }
  Serial.println();

  dumpMemory();
  
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  delay(2000);
}