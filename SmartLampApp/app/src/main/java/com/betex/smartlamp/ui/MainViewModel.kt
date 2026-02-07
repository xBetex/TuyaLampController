package com.betex.smartlamp.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.betex.smartlamp.data.PreferencesManager
import com.betex.smartlamp.model.*
import com.betex.smartlamp.network.RetrofitInstance
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val prefs = PreferencesManager(application)
    
    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            val url = prefs.baseUrl.first()
            _uiState.value = _uiState.value.copy(baseUrl = url)
            checkConnection()
        }
    }

    fun updateBaseUrl(url: String) {
        _uiState.value = _uiState.value.copy(baseUrl = url)
        viewModelScope.launch {
            prefs.saveBaseUrl(url)
        }
    }

    private fun getApi() = RetrofitInstance.getApi(_uiState.value.baseUrl)

    fun checkConnection() {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                val response = getApi().getStatus()
                if (response.isSuccessful && response.body()?.ok == true) {
                    val connected = response.body()?.data?.connected == true
                    _uiState.value = _uiState.value.copy(isConnected = connected, isLoading = false)
                } else {
                    _uiState.value = _uiState.value.copy(isConnected = false, isLoading = false, error = "Status check failed")
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(isConnected = false, isLoading = false, error = e.localizedMessage)
            }
        }
    }

    fun connect() {
        performAction { getApi().connect() }
    }
    
    fun disconnect() {
        performAction { getApi().disconnect() }
    }

    fun reconnect() {
        performAction { getApi().reconnect() }
    }

    fun setPower(on: Boolean) {
        performAction { getApi().setPower(PowerRequest(on)) }
    }

    fun setMode(mode: String) {
        performAction { getApi().setMode(ModeRequest(mode)) }
    }

    fun setWhite(brightness: Int?, temperature: Int?) {
        performAction { getApi().setWhite(WhiteRequest(brightness, temperature)) }
    }

    fun setColor(hex: String, brightness: Int) {
        performAction { getApi().setColor(ColorRequest(hex, brightness)) }
    }

    fun startRainbow(speed: Float, hMin: Float, hMax: Float) {
        performAction { getApi().startRainbow(RainbowRequest(speed, hMin, hMax)) }
    }
    
    fun stopRainbow() {
        performAction { getApi().stopRainbow() }
    }

    private fun <T> performAction(action: suspend () -> retrofit2.Response<ApiResponse<T>>) {
        viewModelScope.launch {
            try {
                // _uiState.value = _uiState.value.copy(isLoading = true) // Optional: don't block UI for every slider move
                val response = action()
                if (response.isSuccessful && response.body()?.ok == true) {
                    // Success
                     _uiState.value = _uiState.value.copy(error = null)
                     // If it was connect/disconnect, update status?
                     // Ideally we re-fetch status or trust response
                } else {
                    _uiState.value = _uiState.value.copy(error = response.body()?.error ?: "Request failed")
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = e.localizedMessage)
            } finally {
                // _uiState.value = _uiState.value.copy(isLoading = false)
            }
        }
    }
    
    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}

data class UiState(
    val baseUrl: String = "",
    val isConnected: Boolean = false,
    val isLoading: Boolean = false,
    val error: String? = null
)
