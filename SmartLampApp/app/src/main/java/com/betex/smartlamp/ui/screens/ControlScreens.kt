package com.betex.smartlamp.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.betex.smartlamp.ui.MainViewModel
import kotlin.math.roundToInt

@Composable
fun WhiteScreen(viewModel: MainViewModel) {
    var brightness by remember { mutableFloatStateOf(0.5f) }
    var temperature by remember { mutableFloatStateOf(0.5f) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("White Light Control", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(32.dp))
        
        Text("Brightness: ${(brightness * 100).toInt()}%")
        Slider(
            value = brightness,
            onValueChange = { brightness = it },
            onValueChangeFinished = { 
                viewModel.setWhite((brightness * 1000).toInt(), (temperature * 100).toInt())
                viewModel.setMode("white")
            },
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text("Temperature: Warm <-> Cool")
        Slider(
            value = temperature,
            onValueChange = { temperature = it },
            onValueChangeFinished = { 
                viewModel.setWhite((brightness * 1000).toInt(), (temperature * 100).toInt())
                viewModel.setMode("white")
            },
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        Button(
            onClick = { 
                 viewModel.setMode("white")
                 viewModel.setWhite((brightness * 1000).toInt(), (temperature * 100).toInt())
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Apply White Mode")
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Button(onClick = { viewModel.setPower(true) }) { Text("Power ON") }
            Button(onClick = { viewModel.setPower(false) }, colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)) { Text("Power OFF") }
        }
    }
}

@Composable
fun ColorScreen(viewModel: MainViewModel) {
    var red by remember { mutableFloatStateOf(1f) }
    var green by remember { mutableFloatStateOf(0f) }
    var blue by remember { mutableFloatStateOf(0f) }
    var brightness by remember { mutableFloatStateOf(1.0f) }
    
    val currentColor = Color(red, green, blue)
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Static Color", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(24.dp))
        
        // Preview
        Box(
            modifier = Modifier
                .size(100.dp)
                .background(currentColor, CircleShape)
                .border(2.dp, Color.Gray, CircleShape)
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text("Red")
        Slider(value = red, onValueChange = { red = it }, colors = SliderDefaults.colors(thumbColor = Color.Red, activeTrackColor = Color.Red))
        
        Text("Green")
        Slider(value = green, onValueChange = { green = it }, colors = SliderDefaults.colors(thumbColor = Color.Green, activeTrackColor = Color.Green))
        
        Text("Blue")
        Slider(value = blue, onValueChange = { blue = it }, colors = SliderDefaults.colors(thumbColor = Color.Blue, activeTrackColor = Color.Blue))
        
        Spacer(modifier = Modifier.height(16.dp))
        Text("Brightness: ${(brightness * 100).toInt()}%")
        Slider(value = brightness, onValueChange = { brightness = it })
        
        Spacer(modifier = Modifier.height(24.dp))
        Button(
            onClick = {
                // Convert to Hex
                val r = (red * 255).roundToInt()
                val g = (green * 255).roundToInt()
                val b = (blue * 255).roundToInt()
                val hex = String.format("#%02x%02x%02x", r, g, b)
                
                viewModel.setColor(hex, (brightness * 1000).toInt())
                viewModel.setMode("color") // Assume "color" mode or similar is triggered by setColor usually, but explicit mode set doesn't hurt or might be needed.
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Apply Color")
        }
    }
}

@Composable
fun EffectsScreen(viewModel: MainViewModel) {
    var speed by remember { mutableFloatStateOf(50f) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Effects", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(32.dp))
        
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Rainbow Effect", style = MaterialTheme.typography.titleLarge)
                Spacer(modifier = Modifier.height(16.dp))
                
                Text("Speed: ${speed.toInt()}")
                Slider(
                    value = speed, 
                    onValueChange = { speed = it }, 
                    valueRange = 0f..100f
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(), 
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Button(
                        onClick = { viewModel.startRainbow(speed, 0f, 1f) }
                    ) { Text("Start") }
                    
                    Button(
                        onClick = { viewModel.stopRainbow() },
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                    ) { Text("Stop") }
                }
            }
        }
    }
}
