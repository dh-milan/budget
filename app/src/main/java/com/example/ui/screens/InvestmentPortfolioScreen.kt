package com.example.ui.screens

import android.graphics.Color as AndroidColor
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ShowChart
import androidx.compose.material.icons.filled.TrendingDown
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.example.ui.theme.glassmorphism
import com.github.mikephil.charting.charts.LineChart
import com.github.mikephil.charting.charts.PieChart
import com.github.mikephil.charting.components.Legend
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.data.*
import com.github.mikephil.charting.formatter.IndexAxisValueFormatter
import com.github.mikephil.charting.formatter.PercentFormatter

data class Holding(
    val id: String,
    val symbol: String,
    val name: String,
    val quantity: Double,
    val currentPrice: Double,
    val profitLossPercentage: Double
)

data class PerformancePoint(val label: String, val value: Float)
data class AllocationSlice(val label: String, val percentage: Float)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InvestmentPortfolioScreen(
    totalBalance: Double? = null,
    totalProfit: Double? = null,
    totalProfitPercentage: Double? = null,
    holdings: List<Holding> = emptyList(),
    performanceHistory: List<PerformancePoint> = emptyList(),
    allocationSlices: List<AllocationSlice> = emptyList(),
    onAddInvestment: () -> Unit = {}
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Investment Portfolio", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.9f)
                ),
                modifier = Modifier.glassmorphism(cornerRadius = 0.dp)
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = onAddInvestment,
                containerColor = MaterialTheme.colorScheme.primary
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Investment")
            }
        }
    ) { paddingValues ->
        if (totalBalance == null && holdings.isEmpty()) {
            // Empty state
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Default.ShowChart,
                        contentDescription = null,
                        modifier = Modifier.size(72.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "No investments yet",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Tap + to add your first investment",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                contentPadding = PaddingValues(vertical = 16.dp)
            ) {
                // Portfolio header
                if (totalBalance != null) {
                    item {
                        PortfolioHeaderCard(
                            balance = totalBalance,
                            profit = totalProfit ?: 0.0,
                            profitPercentage = totalProfitPercentage ?: 0.0
                        )
                    }
                }

                // Performance chart (only if data exists)
                if (performanceHistory.isNotEmpty()) {
                    item {
                        Text(
                            text = "Performance History",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                    item {
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(250.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
                            ),
                            elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
                        ) {
                            Box(modifier = Modifier.padding(16.dp)) {
                                PerformanceLineChart(data = performanceHistory)
                            }
                        }
                    }
                }

                // Allocation chart (only if data exists)
                if (allocationSlices.isNotEmpty()) {
                    item {
                        Text(
                            text = "Asset Allocation",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                    item {
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(300.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
                            ),
                            elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
                        ) {
                            Box(modifier = Modifier.padding(16.dp)) {
                                AllocationPieChart(data = allocationSlices)
                            }
                        }
                    }
                }

                // Holdings list
                if (holdings.isNotEmpty()) {
                    item {
                        Text(
                            text = "Current Holdings",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                    items(holdings, key = { it.id }) { holding ->
                        HoldingRowItem(holding)
                    }
                }
            }
        }
    }
}

@Composable
fun PortfolioHeaderCard(balance: Double, profit: Double, profitPercentage: Double) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Column(
            modifier = Modifier
                .padding(24.dp)
                .fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Total Portfolio Value",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "$${"%.2f".format(balance)}",
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            Spacer(modifier = Modifier.height(12.dp))

            val isPositive = profit >= 0
            val icon = if (isPositive) Icons.Default.TrendingUp else Icons.Default.TrendingDown
            val color = if (isPositive) Color(0xFF4CAF50) else Color(0xFFF44336)
            val sign = if (isPositive) "+" else "-"

            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(imageVector = icon, contentDescription = null, tint = color, modifier = Modifier.size(20.dp))
                Spacer(modifier = Modifier.width(4.dp))
                Text(
                    text = "$sign$${"%.2f".format(kotlin.math.abs(profit))} (${"%.2f".format(profitPercentage)}%)",
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium,
                    color = color
                )
            }
        }
    }
}

@Composable
fun HoldingRowItem(holding: Holding) {
    val isPositive = holding.profitLossPercentage >= 0
    val color = if (isPositive) Color(0xFF4CAF50) else Color(0xFFF44336)
    val sign = if (isPositive) "+" else ""

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(holding.symbol, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text(holding.name, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "$${"%.2f".format(holding.currentPrice * holding.quantity)}",
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    text = "$sign${"%.2f".format(holding.profitLossPercentage)}%",
                    style = MaterialTheme.typography.bodyMedium,
                    color = color,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

@Composable
fun PerformanceLineChart(data: List<PerformancePoint>) {
    val primaryColor = Color(0xFF4CAF50).toArgb()
    val onSurfaceColor = MaterialTheme.colorScheme.onSurface.toArgb()

    AndroidView(
        factory = { context ->
            LineChart(context).apply {
                description.isEnabled = false
                legend.isEnabled = false
                setTouchEnabled(true)
                setPinchZoom(false)
                xAxis.apply {
                    position = XAxis.XAxisPosition.BOTTOM
                    textColor = onSurfaceColor
                    setDrawGridLines(false)
                }
                axisLeft.apply {
                    textColor = onSurfaceColor
                    setDrawGridLines(true)
                }
                axisRight.isEnabled = false
            }
        },
        update = { chart ->
            val entries = data.mapIndexed { i, point -> Entry(i.toFloat(), point.value) }
            chart.xAxis.valueFormatter = IndexAxisValueFormatter(data.map { it.label })
            val dataSet = LineDataSet(entries, "Portfolio Value").apply {
                color = primaryColor
                setCircleColor(primaryColor)
                lineWidth = 2.5f
                circleRadius = 4f
                setDrawValues(false)
                mode = LineDataSet.Mode.CUBIC_BEZIER
                setDrawFilled(true)
                fillColor = primaryColor
                fillAlpha = 40
            }
            chart.data = LineData(dataSet)
            chart.invalidate()
        },
        modifier = Modifier.fillMaxSize()
    )
}

@Composable
fun AllocationPieChart(data: List<AllocationSlice>) {
    val chartColors = listOf(
        Color(0xFF2196F3).toArgb(),
        Color(0xFF9C27B0).toArgb(),
        Color(0xFFFF9800).toArgb(),
        Color(0xFF607D8B).toArgb(),
        Color(0xFF4CAF50).toArgb(),
        Color(0xFFF44336).toArgb()
    )
    val onSurfaceColor = MaterialTheme.colorScheme.onSurface.toArgb()

    AndroidView(
        factory = { context ->
            PieChart(context).apply {
                description.isEnabled = false
                isDrawHoleEnabled = true
                setHoleColor(AndroidColor.TRANSPARENT)
                setTransparentCircleColor(AndroidColor.TRANSPARENT)
                holeRadius = 55f
                transparentCircleRadius = 60f
                setDrawCenterText(true)
                centerText = "Allocation"
                setCenterTextColor(onSurfaceColor)
                setCenterTextSize(16f)
                setUsePercentValues(true)
                legend.apply {
                    textColor = onSurfaceColor
                    isWordWrapEnabled = true
                    verticalAlignment = Legend.LegendVerticalAlignment.BOTTOM
                    horizontalAlignment = Legend.LegendHorizontalAlignment.CENTER
                }
            }
        },
        update = { chart ->
            val entries = data.map { PieEntry(it.percentage, it.label) }
            val dataSet = PieDataSet(entries, "").apply {
                setColors(chartColors.take(entries.size))
                sliceSpace = 2f
                selectionShift = 5f
                valueTextColor = AndroidColor.WHITE
                valueTextSize = 12f
                valueFormatter = PercentFormatter(chart)
            }
            chart.data = PieData(dataSet)
            chart.invalidate()
        },
        modifier = Modifier.fillMaxSize()
    )
}
