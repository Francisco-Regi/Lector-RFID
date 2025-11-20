package com.ejemplo.rfidapp

import android.content.Context
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val etNombre = findViewById<EditText>(R.id.etNombre)
        val etCorreo = findViewById<EditText>(R.id.etCorreo)
        val etTel = findViewById<EditText>(R.id.etTel)
        val etLada = findViewById<EditText>(R.id.etLada)
        val btnGuardar = findViewById<Button>(R.id.btnGuardar)

        val prefs = getSharedPreferences("MisDatosNFC", Context.MODE_PRIVATE)

        // Cargar datos guardados
        etNombre.setText(prefs.getString("nombre", ""))
        etCorreo.setText(prefs.getString("correo", ""))
        etTel.setText(prefs.getString("tel", ""))
        etLada.setText(prefs.getString("region", "+52"))

        btnGuardar.setOnClickListener {
            prefs.edit().apply {
                putString("nombre", etNombre.text.toString())
                putString("correo", etCorreo.text.toString())
                putString("tel", etTel.text.toString())
                putString("region", etLada.text.toString())
                apply()
            }
            Toast.makeText(this, "Datos guardados. ¡Acerca el cel al lector!", Toast.LENGTH_LONG).show()
        }
    }
}