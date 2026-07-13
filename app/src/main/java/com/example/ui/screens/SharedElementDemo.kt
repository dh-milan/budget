package com.example.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.ExperimentalSharedTransitionApi
import androidx.compose.animation.SharedTransitionLayout
import androidx.compose.animation.core.spring
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.data.model.TransactionEntity
import com.example.ui.components.AnimatedGlassCard
import com.example.ui.theme.glassmorphism

@OptIn(ExperimentalSharedTransitionApi::class)
@Composable
fun TransactionHeroAnimationDemo(transaction: TransactionEntity) {
    var showDetails by remember { mutableStateOf(false) }

    // SharedTransitionLayout enables hero animations (shared element transitions)
    // between two composable states or navigation destinations.
    SharedTransitionLayout {
        // 1. The standard list item view
        AnimatedVisibility(
            visible = !showDetails,
            enter = fadeIn(),
            exit = fadeOut()
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
                    .sharedBounds(
                        rememberSharedContentState(key = "transaction_card_${transaction.id}"),
                        animatedVisibilityScope = this@AnimatedVisibility,
                        boundsTransform = { _, _ -> spring(dampingRatio = 0.8f, stiffness = 300f) }
                    )
                    .clickable { showDetails = true }
            ) {
                AnimatedGlassCard(
                    title = "${transaction.title} - $${transaction.amount}",
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }

        // 2. The expanded hero detail view
        AnimatedVisibility(
            visible = showDetails,
            enter = fadeIn(),
            exit = fadeOut()
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp)
                    .sharedBounds(
                        rememberSharedContentState(key = "transaction_card_${transaction.id}"),
                        animatedVisibilityScope = this@AnimatedVisibility,
                        boundsTransform = { _, _ -> spring(dampingRatio = 0.8f, stiffness = 300f) }
                    )
                    .glassmorphism(cornerRadius = 32.dp, blurRadius = 40.dp)
                    .clickable { showDetails = false }
            ) {
                Column(modifier = Modifier.padding(32.dp)) {
                    Text(
                        text = transaction.title,
                        style = MaterialTheme.typography.headlineLarge,
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier.sharedElement(
                            rememberSharedContentState(key = "transaction_title_${transaction.id}"),
                            animatedVisibilityScope = this@AnimatedVisibility
                        )
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Amount: $${transaction.amount}",
                        style = MaterialTheme.typography.headlineMedium,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Category: ${transaction.category}",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(32.dp))
                    Text(
                        text = "This is a hero transition! Tap anywhere to shrink back into the list view.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                    )
                }
            }
        }
    }
}
