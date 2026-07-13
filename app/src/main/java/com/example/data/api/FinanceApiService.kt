package com.example.data.api

import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Body
import retrofit2.http.Path
import retrofit2.http.Header
import com.squareup.moshi.JsonClass

// Network Models
@JsonClass(generateAdapter = true)
data class NetworkTransaction(
    val id: String,
    val title: String,
    val amount: String, // Decimal from Django
    val category: String,
    val type: String,
    val timestamp: String,
    val note: String,
    val is_recurring: Boolean
)

@JsonClass(generateAdapter = true)
data class CreateTransactionRequest(
    val account_id: String,
    val title: String,
    val amount: String,
    val category: String,
    val type: String,
    val note: String,
    val is_recurring: Boolean
)

@JsonClass(generateAdapter = true)
data class LoginRequest(
    val email: String,
    val password: String
)

@JsonClass(generateAdapter = true)
data class LoginResponse(
    val access: String,
    val refresh: String
)

interface FinanceApiService {
    // Auth
    @POST("auth/token/")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    // Ledger (Transactions)
    @GET("ledger/transactions/")
    suspend fun getTransactions(@Header("Authorization") token: String): List<NetworkTransaction>

    @POST("ledger/transactions/")
    suspend fun createTransaction(
        @Header("Authorization") token: String,
        @Body transaction: CreateTransactionRequest
    ): NetworkTransaction
}
