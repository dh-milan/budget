package com.example.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.ui.theme.glassmorphism
import com.example.ui.theme.shimmerEffect
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

enum class ScannerState {
    CAMERA,
    PROCESSING,
    CONFIRMATION
}

data class ScannedReceiptData(
    var merchantName: String = "",
    var totalAmount: String = "",
    var date: String = "",
    var category: String = "Groceries"
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReceiptScannerScreen(
    onDismiss: () -> Unit,
    onSaveReceipt: (ScannedReceiptData) -> Unit
) {
    var currentState by remember { mutableStateOf(ScannerState.CAMERA) }
    var scannedData by remember { mutableStateOf(ScannedReceiptData()) }
    val coroutineScope = rememberCoroutineScope()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(
                    text = when(currentState) {
                        ScannerState.CAMERA -> "Scan Receipt"
                        ScannerState.PROCESSING -> "Analyzing..."
                        ScannerState.CONFIRMATION -> "Confirm Details"
                    }, 
                    fontWeight = FontWeight.Bold
                )},
                navigationIcon = {
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "Close")
                    }
                },
                modifier = Modifier.glassmorphism(cornerRadius = 0.dp)
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            when (currentState) {
                ScannerState.CAMERA -> {
                    // Placeholder for CameraX Preview
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color.Black),
                        contentAlignment = Alignment.BottomCenter
                    ) {
                        Text(
                            text = "[ Camera Viewfinder ]",
                            color = Color.White.copy(alpha = 0.5f),
                            modifier = Modifier.align(Alignment.Center)
                        )
                        
                        FloatingActionButton(
                            onClick = {
                                currentState = ScannerState.PROCESSING
                                coroutineScope.launch {
                                    // Simulate OCR API Call delay
                                    delay(2000)
                                    scannedData = ScannedReceiptData(
                                        merchantName = "Walmart Supercenter",
                                        totalAmount = "142.50",
                                        date = "2026-07-12",
                                        category = "Groceries"
                                    )
                                    currentState = ScannerState.CONFIRMATION
                                }
                            },
                            modifier = Modifier.padding(bottom = 48.dp).size(72.dp),
                            shape = RoundedCornerShape(36.dp),
                            containerColor = MaterialTheme.colorScheme.primary
                        ) {
                            Icon(Icons.Default.CameraAlt, contentDescription = "Take Photo", modifier = Modifier.size(32.dp))
                        }
                    }
                }
                
                ScannerState.PROCESSING -> {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.Center,
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator(modifier = Modifier.size(64.dp))
                        Spacer(modifier = Modifier.height(24.dp))
                        Text("Extracting merchant & total via AI...", style = MaterialTheme.typography.titleMedium)
                        
                        // Shimmer placeholders to simulate data extraction
                        Spacer(modifier = Modifier.height(32.dp))
                        Box(modifier = Modifier.fillMaxWidth(0.6f).height(40.dp).clip(RoundedCornerShape(8.dp)).shimmerEffect())
                        Spacer(modifier = Modifier.height(16.dp))
                        Box(modifier = Modifier.fillMaxWidth(0.4f).height(40.dp).clip(RoundedCornerShape(8.dp)).shimmerEffect())
                    }
                }
                
                ScannerState.CONFIRMATION -> {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        OutlinedTextField(
                            value = scannedData.merchantName,
                            onValueChange = { scannedData = scannedData.copy(merchantName = it) },
                            label = { Text("Merchant") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        
                        OutlinedTextField(
                            value = scannedData.totalAmount,
                            onValueChange = { scannedData = scannedData.copy(totalAmount = it) },
                            label = { Text("Total Amount ($)") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        
                        OutlinedTextField(
                            value = scannedData.date,
                            onValueChange = { scannedData = scannedData.copy(date = it) },
                            label = { Text("Date") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        
                        OutlinedTextField(
                            value = scannedData.category,
                            onValueChange = { scannedData = scannedData.copy(category = it) },
                            label = { Text("AI Suggested Category") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        
                        Spacer(modifier = Modifier.weight(1f))
                        
                        Button(
                            onClick = { onSaveReceipt(scannedData) },
                            modifier = Modifier.fillMaxWidth().height(56.dp),
                            shape = RoundedCornerShape(16.dp)
                        ) {
                            Icon(Icons.Default.Check, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Save Transaction", style = MaterialTheme.typography.titleMedium)
                        }
                    }
                }
            }
        }
    }
}
