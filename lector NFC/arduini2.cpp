#include <SPI.h>
#include <MFRC522.h>

#define PIN_SS   5
#define PIN_RST  4
#define PIN_SCK  18
#define PIN_MISO 19
#define PIN_MOSI 23

MFRC522 mfrc522(PIN_SS, PIN_RST);
MFRC522::MIFARE_Key keyA;

// --- CONFIGURACIÓN HCE (ANDROID) ---
// Este AID debe coincidir EXACTAMENTE con el xml de la App Android
// F0010203040506 es un ID de ejemplo privado
byte SELECT_APDU[] = { 0x00, 0xA4, 0x04, 0x00, 0x07, 0xF0, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x00 };

// Comando personalizado para pedir datos "Dame Datos" (0xB0)
byte GET_DATA_CMD[] = { 0x80, 0xB0, 0x00, 0x00, 0x00 }; 

void setup() {
  Serial.begin(115200);
  SPI.begin(PIN_SCK, PIN_MISO, PIN_MOSI, PIN_SS);
  mfrc522.PCD_Init();
  for (byte i = 0; i < 6; i++) keyA.keyByte[i] = 0xFF;
  Serial.println("RC522 listo (Modo Híbrido)");
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

// Intenta hablar con un celular Android vía APDU
bool tryAndroidHCE() {
  byte response[255];
  byte responseLen = 255;

  // 1. Enviar SELECT AID (Despertar a la app)
  MFRC522::StatusCode status = mfrc522.PCD_TransceiveData(
    SELECT_APDU, sizeof(SELECT_APDU),
    response, &responseLen,
    NULL, 0, false
  );

  if (status != MFRC522::STATUS_OK) return false;

  // 2. Si responde 90 00 (OK), pedimos los datos
  // Checamos los ultimos 2 bytes (Status Word)
  if (responseLen >= 2 && response[responseLen-2] == 0x90 && response[responseLen-1] == 0x00) {
      
      byte dataResp[255];
      byte dataLen = 255;
      
      // Enviar comando "DAME DATOS"
      status = mfrc522.PCD_TransceiveData(
        GET_DATA_CMD, sizeof(GET_DATA_CMD),
        dataResp, &dataLen,
        NULL, 0, false
      );

      if (status == MFRC522::STATUS_OK) {
         String jsonRaw = "";
         for(int i=0; i < dataLen - 2; i++) { // -2 para quitar el status word final
            jsonRaw += (char)dataResp[i];
         }
         
         // La app manda el JSON directo, así que lo enviamos a Python
         // Formato esperado: {"nombre":"...","region":"..."}
         if (jsonRaw.length() > 5) {
             Serial.print("UID:CELULAR_ANDROID"); // UID Ficticio
             Serial.println();
             Serial.print("DATA:");
             Serial.println(cleanString(jsonRaw));
             return true;
         }
      }
  }
  return false;
}

// ... (Aquí irían tus funciones readAllMemory y extractVal del código anterior para tarjetas físicas)
// Por brevedad, asumo que las mantienes o las combinas.

void loop() {
  // Reiniciar loop de hardware
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  // Primero: Intentamos hablar con Android (Protocolo ISO 14443-4)
  if (tryAndroidHCE()) {
     // Si funcionó, paramos y esperamos
     mfrc522.PICC_HaltA();
     delay(3000);
     return;
  }

  // Segundo: Si no es Android, leemos como tarjeta normal (Tu código anterior)
  // ... (Pega aquí la lógica de lectura de memoria de tu arduini.cpp anterior)
  // ...
  
  // Para debug simple si solo pruebas Android:
  // Serial.println("No es App Android, es tarjeta normal.");
  
  mfrc522.PICC_HaltA();
  delay(500);
}