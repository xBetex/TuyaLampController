package com.betex.smartlamp.network

import com.betex.smartlamp.model.*
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface LampApi {
    @GET("/status")
    suspend fun getStatus(): Response<ApiResponse<StatusResponse>>

    @POST("/connect")
    suspend fun connect(): Response<ApiResponse<ConnectResponse>>

    @POST("/disconnect")
    suspend fun disconnect(): Response<ApiResponse<ConnectResponse>>

    @POST("/check")
    suspend fun checkConnection(): Response<ApiResponse<ConnectResponse>>

    @POST("/reconnect")
    suspend fun reconnect(): Response<ApiResponse<ConnectResponse>>

    @POST("/power")
    suspend fun setPower(@Body request: PowerRequest): Response<ApiResponse<Map<String, Boolean>>>

    @POST("/mode")
    suspend fun setMode(@Body request: ModeRequest): Response<ApiResponse<Map<String, String>>>

    @POST("/white")
    suspend fun setWhite(@Body request: WhiteRequest): Response<ApiResponse<Map<String, Boolean>>>

    @POST("/color")
    suspend fun setColor(@Body request: ColorRequest): Response<ApiResponse<Map<String, Any>>>

    @POST("/effects/rainbow/start")
    suspend fun startRainbow(@Body request: RainbowRequest): Response<ApiResponse<Map<String, Boolean>>>

    @POST("/effects/rainbow/stop")
    suspend fun stopRainbow(): Response<ApiResponse<Map<String, Boolean>>>
}
