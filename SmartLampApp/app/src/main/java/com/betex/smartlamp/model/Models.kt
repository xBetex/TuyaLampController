package com.betex.smartlamp.model

data class ApiResponse<T>(
    val ok: Boolean,
    val data: T?,
    val error: String?
)

data class StatusResponse(
    val connected: Boolean
)

data class ConnectResponse(
    val connected: Boolean
)

data class PowerRequest(
    val on: Boolean
)

data class ModeRequest(
    val mode: String
)

data class WhiteRequest(
    val brightness: Int? = null,
    val temperature: Int? = null
)

data class ColorRequest(
    val hex: String,
    val brightness: Int // 0-1000
)

data class RainbowRequest(
    val speed: Float,
    val h_min: Float,
    val h_max: Float,
    val use_custom: Boolean = false,
    val colors: List<String> = emptyList()
)
