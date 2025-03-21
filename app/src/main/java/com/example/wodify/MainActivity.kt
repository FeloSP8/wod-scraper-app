package com.example.wodify

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FitnessCenter
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.example.wodify.ui.theme.WodifyTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Inicializar Python
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        
        setContent {
            WodifyTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    WodScraperScreen()
                }
            }
        }
    }
}

@Composable
fun WodScraperScreen() {
    var wodText by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Título
        Text(
            text = "WOD Scraper",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(bottom = 16.dp)
        )
        
        // Logos
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color(0xFF6650a4)
            )
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Image(
                    painter = painterResource(id = R.drawable.n8_logo),
                    contentDescription = "Box N8 Logo",
                    modifier = Modifier.size(100.dp)
                )
                Image(
                    painter = painterResource(id = R.drawable.crossfitdb_logo),
                    contentDescription = "CrossFitDB Logo",
                    modifier = Modifier.size(100.dp)
                )
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Botón para obtener WODs
        Button(
            onClick = {
                scope.launch {
                    isLoading = true
                    wodText = withContext(Dispatchers.IO) {
                        try {
                            val py = Python.getInstance()
                            val module = py.getModule("wod_scraper")
                            module.callAttr("main").toString()
                        } catch (e: Exception) {
                            "Error: ${e.message}"
                        }
                    }
                    isLoading = false
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
        ) {
            Row(
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Default.FitnessCenter,
                    contentDescription = "Obtener WODs",
                    modifier = Modifier.size(24.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Obtener WODs")
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Indicador de carga
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(48.dp)
            )
        }
        
        // Resultados
        if (wodText.isNotEmpty()) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(8.dp)
            ) {
                Text(
                    text = wodText,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    textAlign = TextAlign.Start
                )
            }
        }
    }
}