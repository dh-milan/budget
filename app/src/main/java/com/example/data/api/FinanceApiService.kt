package com.example.data.api

import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Body
import retrofit2.http.Path
import retrofit2.http.Header
import retrofit2.Response
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
data class RegisterRequest(
    val email: String,
    val password: String,
    val name: String
)

@JsonClass(generateAdapter = true)
data class LoginResponse(
    val access: String,
    val refresh: String,
    val user: UserData? = null
)

@JsonClass(generateAdapter = true)
data class UserData(
    val id: String,
    val email: String,
    val full_name: String,
    val avatar_url: String?,
    val role: String,
    val is_new_user: Boolean
)

@JsonClass(generateAdapter = true)
data class GenerateReportRequest(
    val report_type: String,
    val start_date: String,
    val end_date: String,
    val file_format: String = "CSV"
)

@JsonClass(generateAdapter = true)
data class ReportResponse(
    val id: String,
    val report_type: String,
    val title: String,
    val start_date: String,
    val end_date: String,
    val file_format: String,
    val file_url: String?,
    val is_generated: Boolean,
    val generated_at: String?
)

interface FinanceApiService {
    // Auth
    @POST("auth/login/")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @POST("auth/register/")
    suspend fun register(@Body request: RegisterRequest): LoginResponse

    // Ledger (Transactions)
    @GET("ledger/transactions/")
    suspend fun getTransactions(): List<NetworkTransaction>

    @POST("ledger/transactions/")
    suspend fun createTransaction(
        @Body transaction: CreateTransactionRequest
    ): NetworkTransaction

    // Reports
    @GET("analytics/reports/")
    suspend fun getReports(): List<ReportResponse>

    @POST("analytics/reports/generate_report/")
    suspend fun generateReport(@Body request: GenerateReportRequest): ReportResponse

    @GET("analytics/reports/{reportId}/download/")
    suspend fun downloadReport(@Path("reportId") reportId: String): Response<okhttp3.ResponseBody>
}
