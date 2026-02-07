package com.betex.smartlamp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.betex.smartlamp.ui.MainViewModel

@Composable
fun ConnectScreen(
    viewModel: MainViewModel,
    onNavigateToControls: () -> Unit
) {
    val state by viewModel.uiState.collectAsState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Connect to Lamp",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        OutlinedTextField(
            value = state.baseUrl,
            onValueChange = { viewModel.updateBaseUrl(it) },
            label = { Text("Base URL (e.g. http://192.168.1.5:8765)") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
             Button(onClick = { viewModel.checkConnection() }) { Text("Check Status") }
             Button(onClick = { viewModel.connect() }) { Text("Connect Device") }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
             OutlinedButton(onClick = { viewModel.disconnect() }) { Text("Disconnect") }
             OutlinedButton(onClick = { viewModel.reconnect() }) { Text("Reconnect") }
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = if(state.isConnected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.errorContainer
            )
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = if(state.isConnected) "Status: Connected" else "Status: Disconnected",
                    style = MaterialTheme.typography.titleMedium
                )
                if (state.error != null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Error: ${state.error}",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Button(
            onClick = onNavigateToControls, 
            enabled = state.isConnected,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Go to Light Controls")
        }
    }
}
