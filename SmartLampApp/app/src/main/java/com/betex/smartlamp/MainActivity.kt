package com.betex.smartlamp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.betex.smartlamp.ui.LampApp
import com.betex.smartlamp.ui.theme.SmartLampTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SmartLampTheme {
                LampApp()
            }
        }
    }
}
