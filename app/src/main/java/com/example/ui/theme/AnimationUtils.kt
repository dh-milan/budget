package com.example.ui.theme

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.gestures.animateScrollBy
import androidx.compose.ui.unit.dp

object AnimationUtils {
    // Animation durations - optimized for 60fps (16.67ms per frame)
    const val FAST_DURATION = 150
    const val NORMAL_DURATION = 300
    const val SLOW_DURATION = 500
    const val SPLASH_DURATION = 2000
    const val STAGGER_DELAY = 50 // Delay between list items

    // Animation specs - using optimized easing functions
    val FastEaseOut = FastOutSlowInEasing
    val NormalEaseOut = LinearOutSlowInEasing
    val SlowEaseOut = LinearOutSlowInEasing
    val SpringSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessLow)
    
    // Optimized spring for UI elements
    val OptimizedSpring = spring(
        dampingRatio = Spring.DampingRatioNoBouncy,
        stiffness = Spring.StiffnessMedium
    )

    // Standard animations with optimized specs
    val FadeIn = fadeIn(
        animationSpec = tween(NORMAL_DURATION, easing = LinearOutSlowInEasing)
    )
    val FadeOut = fadeOut(
        animationSpec = tween(NORMAL_DURATION, easing = LinearOutSlowInEasing)
    )
    val SlideInFromBottom = slideInVertically(
        animationSpec = tween(NORMAL_DURATION, easing = FastEaseOut),
        initialOffsetY = { it / 4 }
    )
    val SlideOutToBottom = slideOutVertically(
        animationSpec = tween(NORMAL_DURATION, easing = FastEaseOut),
        targetOffsetY = { it / 4 }
    )
    val SlideInFromRight = slideInHorizontally(
        animationSpec = tween(NORMAL_DURATION, easing = FastEaseOut),
        initialOffsetX = { it / 3 }
    )
    val SlideOutToLeft = slideOutHorizontally(
        animationSpec = tween(NORMAL_DURATION, easing = FastEaseOut),
        targetOffsetX = { -it / 3 }
    )
    val ScaleIn = scaleIn(
        animationSpec = tween(NORMAL_DURATION, easing = FastEaseOut),
        initialScale = 0.8f
    )
    val ScaleOut = scaleOut(
        animationSpec = tween(NORMAL_DURATION, easing = FastEaseOut),
        targetScale = 0.8f
    )
    
    // Quick scale for buttons and interactive elements
    val QuickScaleIn = scaleIn(
        animationSpec = tween(FAST_DURATION, easing = FastEaseOut),
        initialScale = 0.95f
    )
    val QuickScaleOut = scaleOut(
        animationSpec = tween(FAST_DURATION, easing = FastEaseOut),
        targetScale = 0.95f
    )

    // Stagger animation for lists - returns animation spec with delay
    fun staggeredEnter(delay: Int = STAGGER_DELAY, index: Int = 0): EnterTransition {
        val totalDelay = index * delay
        return fadeIn(
            animationSpec = tween(NORMAL_DURATION, delayMillis = totalDelay, easing = LinearOutSlowInEasing)
        ) + slideInVertically(
            animationSpec = tween(NORMAL_DURATION, delayMillis = totalDelay, easing = FastEaseOut),
            initialOffsetY = { it / 4 }
        )
    }

    // Pulse animation for FAB - optimized
    val PulseAnimation = infiniteRepeatable(
        animation = tween(1000, easing = LinearEasing),
        repeatMode = RepeatMode.Reverse
    )

    // Shimmer animation for loading states
    val ShimmerAnimation = infiniteRepeatable(
        animation = tween(2000, easing = LinearEasing),
        repeatMode = RepeatMode.Restart
    )
    
    // Smooth color transition
    fun smoothColorTransition() = animateColorAsState(
        targetValue = it,
        animationSpec = tween(NORMAL_DURATION, easing = LinearOutSlowInEasing),
        label = "colorTransition"
    )
}
