package com.betex.smartlamp.network

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import java.util.concurrent.TimeUnit

object RetrofitInstance {
    private var retrofit: Retrofit? = null
    private var currentUrl: String? = null

    fun getApi(baseUrl: String): LampApi {
        // Ensure URL ends with /
        val validUrl = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        
        if (retrofit == null || currentUrl != validUrl) {
            currentUrl = validUrl
            
            val logging = HttpLoggingInterceptor()
            logging.level = HttpLoggingInterceptor.Level.BODY
            
            val client = OkHttpClient.Builder()
                .addInterceptor(logging)
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .build()

            retrofit = Retrofit.Builder()
                .baseUrl(validUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }
        return retrofit!!.create(LampApi::class.java)
    }
}
