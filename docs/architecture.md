# SmartMaintain AI - Architecture

## Overview

SmartMaintain AI is a full-stack predictive maintenance platform for manufacturing. It follows a modular architecture with clear separation between frontend, backend API, ML services, and AWS integrations.

## Component Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   React UI  │────▶│  FastAPI API │────▶│  Repositories   │
│  (Vite/MUI) │     │  (Python)    │     │  (Memory/DDB)   │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │ ML Models│ │ Bedrock  │ │ SNS Notify   │
        │ (Local/  │ │ (RAG/    │ │              │
        │ SageMaker│ │ Explain) │ │              │
        └──────────┘ └──────────┘ └──────────────┘
```

## Backend Layers

| Layer | Purpose |
|-------|---------|
| `api/routes.py` | HTTP endpoints, request validation |
| `schemas/domain.py` | Pydantic models for all entities |
| `repositories/` | Data access (in-memory or DynamoDB) |
| `services/` | Business logic, ML, AI, notifications |
| `core/` | Config, security, JWT auth |

## ML Pipeline

1. Sensor readings ingested via POST `/api/readings`
2. Feature extraction (9-dimensional vector with rolling stats)
3. Isolation Forest → anomaly score
4. Random Forest → failure probability
5. Health score computed from combined metrics
6. Alerts auto-created when thresholds exceeded
7. Bedrock/local service generates human-readable explanation

## AWS Integration Points

All AWS services use adapter pattern with local fallbacks:

- `LocalModelPredictionService` / `SageMakerPredictionService`
- `BedrockService` with local RAG fallback
- `NotificationService` with SNS or console logging
- Repository layer supports `memory` and `dynamodb` backends

## Deployment

Multi-stage Docker build:
1. Build React frontend with Node.js
2. Copy static files into Python container
3. FastAPI serves both API and SPA

Health check at `/health` (no external dependencies).
