package com.betex.smartlamp.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.betex.smartlamp.ui.navigation.Screen
import com.betex.smartlamp.ui.screens.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LampApp(viewModel: MainViewModel = viewModel()) {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val showBottomBar = currentRoute in listOf(Screen.White.route, Screen.Color.route, Screen.Effects.route)

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Smart Lamp") },
                actions = {
                    // Show a settings/disconnect button even when inside controls
                    if (showBottomBar) {
                        IconButton(onClick = { navController.navigate(Screen.Connect.route) }) {
                            Icon(Icons.Default.Settings, contentDescription = "Connect Settings")
                        }
                    }
                }
            )
        },
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    NavigationBarItem(
                        selected = currentRoute == Screen.White.route,
                        onClick = { 
                            navController.navigate(Screen.White.route) {
                                popUpTo(Screen.White.route) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(Icons.Default.Highlight, contentDescription = "White") },
                        label = { Text("White") }
                    )
                    NavigationBarItem(
                        selected = currentRoute == Screen.Color.route,
                        onClick = { 
                            navController.navigate(Screen.Color.route) {
                                popUpTo(Screen.White.route) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(Icons.Default.ColorLens, contentDescription = "Color") },
                        label = { Text("Color") }
                    )
                    NavigationBarItem(
                        selected = currentRoute == Screen.Effects.route,
                        onClick = { 
                            navController.navigate(Screen.Effects.route) {
                                popUpTo(Screen.White.route) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(Icons.Default.AutoAwesome, contentDescription = "Effects") },
                        label = { Text("Effects") }
                    )
                }
            }
        }
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Connect.route,
            modifier = Modifier.padding(padding)
        ) {
            composable(Screen.Connect.route) {
                ConnectScreen(
                    viewModel = viewModel,
                    onNavigateToControls = { navController.navigate(Screen.White.route) }
                )
            }
            composable(Screen.White.route) { WhiteScreen(viewModel) }
            composable(Screen.Color.route) { ColorScreen(viewModel) }
            composable(Screen.Effects.route) { EffectsScreen(viewModel) }
        }
    }
}
