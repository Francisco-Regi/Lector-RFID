package com.ejemplo.rfidapp

import android.content.Context
import android.nfc.cardemulation.HostApduService
import android.os.Bundle
import android.util.Log
import org.json.JSONObject

class MyHostApduService : HostApduService() {

    override fun processCommandApdu(commandApdu: ByteArray?, extras: Bundle?): ByteArray {
        if (commandApdu == null) return hexStringToByteArray("6F00")

        val hexCommand = toHex(commandApdu)
        Log.d("HCE", "Recibido: $hexCommand")

        // 1. El Arduino dice "SELECT AID" (Hola, busco la app F001...)
        if (hexCommand.startsWith("00A40400")) {
            return hexStringToByteArray("9000") // Respondemos "OK"
        }

        // 2. El Arduino dice "GET DATA" (80B0000000)
        if (hexCommand.startsWith("80B0")) {
            // Recuperamos los datos guardados por la Activity
            val prefs = getSharedPreferences("MisDatosNFC", Context.MODE_PRIVATE)
            val json = JSONObject()
            json.put("nombre", prefs.getString("nombre", "Usuario"))
            json.put("correo", prefs.getString("correo", ""))
            json.put("telefono", prefs.getString("tel", ""))
            json.put("region", prefs.getString("region", "+52"))

            val jsonString = json.toString()
            val jsonBytes = jsonString.toByteArray(Charsets.UTF_8)
            
            // Retornamos JSON + Status OK (90 00)
            return jsonBytes + hexStringToByteArray("9000")
        }

        return hexStringToByteArray("6F00") // Error desconocido
    }

    override fun onDeactivated(reason: Int) {
        Log.d("HCE", "Desconectado: $reason")
    }

    // Utilidades Hex
    private fun toHex(bytes: ByteArray): String {
        return bytes.joinToString("") { "%02X".format(it) }
    }
    private fun hexStringToByteArray(s: String): ByteArray {
        val len = s.length
        val data = ByteArray(len / 2)
        var i = 0
        while (i < len) {
            data[i / 2] = ((Character.digit(s[i], 16) shl 4) + Character.digit(s[i + 1], 16)).toByte()
            i += 2
        }
        return data
    }
}