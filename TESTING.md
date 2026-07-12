# 🧪 WealthFlow Phase 10: Enterprise Testing Strategy & JVM Quality Harness

This document outlines the testing specifications for the **WealthFlow** platform, covering automated unit tests, screenshot regression testing, local Robolectric JVM setups, and backend API contract validation.

---

## 1. Local JVM Functional Testing (Robolectric)

To bypass the slow start-up times of Android emulators, WealthFlow uses **Robolectric** to execute local JVM-based functional tests. These test critical repository and view model interactions instantly.

```kotlin
// src/test/java/com/example/ui/viewmodel/FinanceViewModelTest.kt
package com.example.ui.viewmodel

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.example.data.database.AppDatabase
import com.example.data.model.TransactionEntity
import com.example.data.repository.FinanceRepository
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.annotation.Config

@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(AndroidJUnit4::class)
@Config(sdk = [33])
class FinanceViewModelTest {

    private lateinit var db: AppDatabase
    private lateinit var repository: FinanceRepository
    private lateinit var viewModel: FinanceViewModel

    @Before
    fun setUp() {
        // Build an in-memory database configuration
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        db = AppDatabase.getDatabase(context)
        repository = FinanceRepository(
            db.transactionDao(),
            db.budgetDao(),
            db.goalDao(),
            db.debtDao(),
            db.billDao()
        )
        viewModel = FinanceViewModel(repository)
    }

    @After
    fun tearDown() {
        db.close()
    }

    @Test
    fun addTransaction_insertsToDatabaseAndFlowUpdates() = runTest {
        val testTx = TransactionEntity(
            id = 0,
            title = "Whole Foods Organic Market",
            amount = 120.50,
            category = "Groceries",
            type = "EXPENSE",
            timestamp = System.currentTimeMillis()
        )

        viewModel.addTransaction(testTx.title, testTx.amount, testTx.category, testTx.type, testTx.timestamp)

        // Wait for flow collection and assert the record is populated
        val allTx = db.transactionDao().getAllTransactions()
        allTx.collect { list ->
            assertEquals(1, list.size)
            assertEquals("Whole Foods Organic Market", list[0].title)
            assertEquals(120.50, list[0].amount, 0.01)
        }
    }
}
```

---

## 2. Jetpack Compose Screenshot Regression Testing (Roborazzi)

To ensure the Material Design 3 interface retains its pixel-perfect fidelity across different screen densities, **Roborazzi** is configured to capture and compare Compose tree layouts.

```kotlin
// src/test/java/com/example/ui/screens/MainAppScreenScreenshotTest.kt
package com.example.ui.screens

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onRoot
import com.github.takahirom.roborazzi.captureRoboImage
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class MainAppScreenScreenshotTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun captureDashboardTabScreen() {
        composeTestRule.setContent {
            // Render the screen with dummy theme variables
            MainAppScreenContentWithEmptyDataState()
        }

        // Output screenshot to build path to perform automated image difference testing
        composeTestRule.onRoot().captureRoboImage("screenshots/dashboard_empty_state.png")
    }
}
```

---

## 3. DRF Django Endpoint Contract Testing

We run contract tests using Python's pytest framework to confirm the security and validation structures of our REST API.

```python
# tests/test_transactions_endpoint.py
import pytest
from rest_framework import status
from django.urls import reverse
from models import Transaction

@pytest.mark.django_db
def test_create_transaction_unauthorized_fails(client):
    url = reverse('transaction-list')
    payload = {
        "title": "Aesthetic Workspace",
        "amount": 25.00,
        "category": "Office Supplies",
        "type": "EXPENSE"
    }
    
    # Missing Bearer token header
    response = client.post(url, payload, content_type='application/json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_create_transaction_authorized_succeeds(authenticated_client):
    client, user = authenticated_client
    url = reverse('transaction-list')
    payload = {
        "title": "Stripe Subscriptions API",
        "amount": 10.00,
        "category": "Technology",
        "type": "EXPENSE"
    }
    
    response = client.post(url, payload, content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    assert Transaction.objects.filter(user=user, title="Stripe Subscriptions API").exists()
```

---

## 4. Automation Testing commands

Developers utilize simple commands to trigger local test runners during high-velocity feature deployments:

```bash
# Run local JVM functional tests
gradle :app:testDebugUnitTest

# Validate UI layouts with Roborazzi
gradle :app:verifyRoborazziDebug

# Update Roborazzi visual baselines
gradle :app:recordRoborazziDebug
```
