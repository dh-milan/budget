package com.example.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.airbnb.lottie.compose.*
import com.example.ui.theme.glassmorphism
import com.example.ui.theme.shimmerEffect

@Composable
fun AnimatedGlassCard(
    title: String,
    modifier: Modifier = Modifier,
    lottieResId: Int? = null,
    isLoading: Boolean = false
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .glassmorphism(
                cornerRadius = 24.dp,
                blurRadius = 20.dp,
                backgroundColor = Color.Black.copy(alpha = 0.4f),
                borderColor = Color.White.copy(alpha = 0.2f)
            )
            .padding(24.dp)
    ) {
        if (isLoading) {
            // Skeleton loading state
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.6f)
                    .height(24.dp)
                    .shimmerEffect(androidx.compose.foundation.shape.RoundedCornerShape(4.dp))
            )
        } else {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = title,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )

                // Optional Lottie Animation
                if (lottieResId != null) {
                    val composition by rememberLottieComposition(LottieCompositionSpec.RawRes(lottieResId))
                    val progress by animateLottieCompositionAsState(
                        composition,
                        iterations = LottieConstants.IterateForever
                    )
                    
                    LottieAnimation(
                        composition = composition,
                        progress = { progress },
                        modifier = Modifier.size(48.dp)
                    )
                }
            }
        }
    }
}
