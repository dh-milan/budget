package com.example.data.api

import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import okhttp3.Interceptor
import com.example.BuildConfig
import android.content.Context
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys

object RetrofitClient {
    private const val TAG = "RetrofitClient"
    
    // Use build config to determine environment
    private val BASE_URL = if (BuildConfig.DEBUG) {
        "http://192.168.1.68:8000/api/v1/"  // Development
    } else {
        "https://api.wealthflow.app/api/v1/"  // Production
    }
    
    // Secure token storage using EncryptedSharedPreferences
    private const val PREF_NAME = "wealthflow_secure_prefs"
    private const val KEY_AUTH_TOKEN = "auth_token"
    
    private var securePrefs: EncryptedSharedPreferences? = null

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = if (BuildConfig.DEBUG) {
            HttpLoggingInterceptor.Level.BODY
        } else {
            HttpLoggingInterceptor.Level.NONE  // No logging in production
        }
    }

    // Auth interceptor to attach token to requests
    private val authInterceptor = Interceptor { chain ->
        val originalRequest = chain.request()
        val requestBuilder = originalRequest.newBuilder()
        
        // Add authorization header if token exists
        getAuthToken()?.let { token ->
            requestBuilder.addHeader("Authorization", "Bearer $token")
        }
        
        val request = requestBuilder.build()
        chain.proceed(request)
    }

    // Token refresh interceptor
    private val tokenRefreshInterceptor = Interceptor { chain ->
        val originalRequest = chain.request()
        val response = chain.proceed(originalRequest)
        
        // If we get 401, token might be expired - clear it
        if (response.code == 401) {
            clearAuthToken()
            Log.w(TAG, "Token expired or invalid - cleared")
        }
        
        response
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .addInterceptor(authInterceptor)
        .addInterceptor(tokenRefreshInterceptor)
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

    /**
     * Initialize secure preferences - call this from Application or MainActivity
     */
    fun initialize(context: Context) {
        if (securePrefs == null) {
            val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
            securePrefs = EncryptedSharedPreferences.create(
                PREF_NAME,
                masterKeyAlias,
                context,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            )
        }
    }

    /**
     * Save auth token securely
     */
    fun saveAuthToken(token: String) {
        securePrefs?.edit()?.putString(KEY_AUTH_TOKEN, token)?.apply()
    }

    /**
     * Get auth token securely
     */
    private fun getAuthToken(): String? {
        return securePrefs?.getString(KEY_AUTH_TOKEN, null)
    }

    /**
     * Clear auth token (on logout)
     */
    fun clearAuthToken() {
        securePrefs?.edit()?.remove(KEY_AUTH_TOKEN)?.apply()
    }
}
