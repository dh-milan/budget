# 🚀 WealthFlow Cloud Infrastructure & Deployment Guide

This document defines the production cloud deployment specifications for the **WealthFlow** enterprise backend and mobile application pipeline.

---

## 1. High-Performance Containerization (`docker-compose.prod.yml`)

The production infrastructure is completely containerized. Below is the multi-container configuration hosting the core API gateway, PostgreSQL database clustering, in-memory Redis message queues, and background task scheduling (Celery).

```yaml
version: '3.8'

services:
  # 1. Django REST Framework API Gateway
  web:
    image: wealthflow/backend:latest
    build:
      context: .
      dockerfile: ./Dockerfile.prod
    command: gunicorn wealthflow.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/mediafiles
    expose:
      - "8000"
    environment:
      - DEBUG=0
      - DATABASE_URL=postgres://flow_admin:SecureAdminPassword@db:5432/wealthflow_prod
      - REDIS_URL=redis://redis:6379/1
      - CELERY_BROKER_URL=redis://redis:6379/0
      - STRIPE_SECRET_KEY=sk_prod_51Nz...
    depends_on:
      - db
      - redis

  # 2. Redis Cache & Broker Broker
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # 3. PostgreSQL Main Cluster Database
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=wealthflow_prod
      - POSTGRES_USER=flow_admin
      - POSTGRES_PASSWORD=SecureAdminPassword
    ports:
      - "5432:5432"

  # 4. Celery Worker (Background predicted transaction logic)
  celery_worker:
    image: wealthflow/backend:latest
    command: celery -A wealthflow worker -l info --concurrency=4
    environment:
      - DATABASE_URL=postgres://flow_admin:SecureAdminPassword@db:5432/wealthflow_prod
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  # 5. Reverse Proxy & SSL Nginx Router
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/prod.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles
      - media_volume:/app/mediafiles
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - web
      - redis

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

---

## 2. Cloud Infrastructure Map (AWS & ECS Fargate)

WealthFlow targets a resilient, auto-scaled environment on **Amazon Web Services (AWS)** using Serverless orchestration.

```
                  ┌───────────────────────────────┐
                  │          Route 53             │ (High-Availability DNS)
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │    AWS CloudFront CDN         │ (Static Asset Edge Caching)
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │   Application Load Balancer   │ (ALB with SSL Certificate Termination)
                  └──────────────┬────────────────┘
                                 │
                                 ▼
            ┌────────────────────┴────────────────────┐
            ▼                                         ▼
   ┌──────────────────┐                      ┌──────────────────┐
   │    ECS Fargate   │                      │    ECS Fargate   │
   │ API Task Instance│ (Availability Zone A)│ API Task Instance│ (Availability Zone B)
   └────────┬─────────┘                      └────────┬─────────┘
            │                                         │
            └────────────────────┬────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
   │  AWS ElastiCache │ │   Aurora Postgres│ │ S3 Storage Bucket│
   │  (Redis Cluster) │ │ (Serverless DB)  │ │ (Receipt Uploads)│
   └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 3. GitHub Actions Continuous Integration / CD Pipeline

The following YAML workflow verifies Android source compilation on every single push and builds production docker containers for serverless deployment:

```yaml
name: WealthFlow CI/CD Engine

on:
  push:
    branches: [ main, release/* ]
  pull_request:
    branches: [ main ]

jobs:
  # Pipeline Job 1: Build & Verify Android Client App
  android-build:
    name: Compiling Android Artifacts
    runs-on: ubuntu-latest
    steps:
      - name: Code Checkout
        uses: actions/checkout@v4

      - name: Setup Java Development Kit (JDK 17)
        uses: actions/setup-java@v3
        with:
          distribution: 'zulu'
          java-version: '17'
          cache: 'gradle'

      - name: Grant Execute Permission to Gradle Wrapper
        run: chmod +x gradlew

      - name: Execute Android Code Linter and Formatter Check
        run: ./gradlew lint

      - name: Run Roborazzi Visual Regression Verification
        run: ./gradlew testDebugUnitTest

      - name: Generate Unsigned Debug APK
        run: ./gradlew assembleDebug

  # Pipeline Job 2: Build & Deploy Backend Containers (AWS)
  backend-deploy:
    name: Build & Push DRF Containers to AWS ECR
    needs: android-build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Code Checkout
        uses: actions/checkout@v4

      - name: Setup AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Authenticate with Amazon Elastic Container Registry (ECR)
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build, Tag, and Push Production Backend Container
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: wealthflow-backend
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -t $ECR_REGISTRY/$ECR_REPOSITORY:latest -f Dockerfile.prod .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Force ECS Fargate Cluster Redeployment
        run: |
          aws ecs update-service --cluster wealthflow-production-cluster --service wealthflow-api-gateway --force-new-deployment
```
