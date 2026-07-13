package com.example.data.api

import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import com.example.BuildConfig

object RetrofitClient {
    // Updated to point to your computer's local Wi-Fi IP so your physical phone can connect
    private const val BASE_URL = "http://192.168.1.68:8000/api/v1/"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        // Add auth interceptor here to attach token to requests later
        .build()

    val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(MoshiConverterFactory.create())
            .build()
    }

    val financeApi: FinanceApiService by lazy {
        retrofit.create(FinanceApiService::class.java)
    }
}
