package com.example.ui.screens

import android.graphics.Color as AndroidColor
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BarChart
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

data class SpendingTrendPoint(val label: String, val amount: Float)
data class CategoryBreakdown(val category: String, val total: Float)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnalyticsDashboardScreen(
    spendingTrends: List<SpendingTrendPoint> = emptyList(),
    categoryHeatmap: List<CategoryBreakdown> = emptyList()
) {
    val scrollState = rememberScrollState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Advanced Analytics", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.9f)
                ),
                modifier = Modifier.glassmorphism(cornerRadius = 0.dp)
            )
        }
    ) { paddingValues ->
        if (spendingTrends.isEmpty() && categoryHeatmap.isEmpty()) {
            // Empty state
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Default.BarChart,
                        contentDescription = null,
                        modifier = Modifier.size(72.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "No analytics data yet",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Add transactions to see your spending trends",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                    )
                }
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(scrollState)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                if (spendingTrends.isNotEmpty()) {
                    Text(
                        text = "Spending Trends",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary
                    )
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
                            SpendingLineChart(data = spendingTrends)
                        }
                    }
                }

                if (categoryHeatmap.isNotEmpty()) {
                    Text(
                        text = "Category Breakdown",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(350.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
                        ),
                        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
                    ) {
                        Box(modifier = Modifier.padding(16.dp)) {
                            CategoryPieChart(data = categoryHeatmap)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}

@Composable
fun SpendingLineChart(data: List<SpendingTrendPoint>) {
    val primaryColor = MaterialTheme.colorScheme.primary.toArgb()
    val onSurfaceColor = MaterialTheme.colorScheme.onSurface.toArgb()

    AndroidView(
        factory = { context ->
            LineChart(context).apply {
                description.isEnabled = false
                legend.textColor = onSurfaceColor
                setTouchEnabled(true)
                setPinchZoom(false)
                xAxis.apply {
                    position = XAxis.XAxisPosition.BOTTOM
                    textColor = onSurfaceColor
                    setDrawGridLines(false)
                    granularity = 1f
                }
                axisLeft.apply {
                    textColor = onSurfaceColor
                    setDrawGridLines(true)
                }
                axisRight.isEnabled = false
            }
        },
        update = { chart ->
            val entries = data.mapIndexed { i, pt -> Entry(i.toFloat(), pt.amount) }
            chart.xAxis.valueFormatter = IndexAxisValueFormatter(data.map { it.label })
            val dataSet = LineDataSet(entries, "Monthly Spending").apply {
                color = primaryColor
                setCircleColor(primaryColor)
                lineWidth = 3f
                circleRadius = 5f
                setDrawValues(false)
                mode = LineDataSet.Mode.CUBIC_BEZIER
                setDrawFilled(true)
                fillColor = primaryColor
                fillAlpha = 50
            }
            chart.data = LineData(dataSet)
            chart.invalidate()
        },
        modifier = Modifier.fillMaxSize()
    )
}

@Composable
fun CategoryPieChart(data: List<CategoryBreakdown>) {
    val chartColors = listOf(
        Color(0xFF6750A4).toArgb(),
        Color(0xFF2E7D32).toArgb(),
        Color(0xFFD84315).toArgb(),
        Color(0xFF0277BD).toArgb(),
        Color(0xFFF9A825).toArgb(),
        Color(0xFF6A1B9A).toArgb()
    )
    val onSurfaceColor = MaterialTheme.colorScheme.onSurface.toArgb()

    AndroidView(
        factory = { context ->
            PieChart(context).apply {
                description.isEnabled = false
                isDrawHoleEnabled = true
                setHoleColor(AndroidColor.TRANSPARENT)
                setTransparentCircleColor(AndroidColor.TRANSPARENT)
                holeRadius = 58f
                transparentCircleRadius = 61f
                setDrawCenterText(true)
                centerText = "Expenses"
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
            val entries = data.map { PieEntry(it.total, it.category) }
            val dataSet = PieDataSet(entries, "").apply {
                setColors(chartColors.take(entries.size))
                sliceSpace = 3f
                selectionShift = 5f
                valueTextColor = AndroidColor.WHITE
                valueTextSize = 14f
                valueFormatter = PercentFormatter(chart)
            }
            chart.data = PieData(dataSet)
            chart.invalidate()
        },
        modifier = Modifier.fillMaxSize()
    )
}
