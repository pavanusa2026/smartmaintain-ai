# SmartMaintain AI

**AI Predictive Maintenance and Quality Monitoring System** for manufacturing environments.

SmartMaintain AI collects machine sensor readings, analyzes equipment behavior, predicts potential failures, detects product-quality defects, and helps maintenance teams make better decisions.

## Features

- **Real-time Equipment Dashboard** — Machine health scores, status overview, and production-line monitoring
- **Anomaly Detection** — Isolation Forest model identifies abnormal sensor patterns
- **Failure-Risk Prediction** — Random Forest model predicts 7-day failure probability
- **AI Alert Explanations** — Plain-language explanations of ML predictions (Bedrock-ready)
- **Alert Management** — Create, acknowledge, investigate, and close alerts
- **Work Order Management** — Full maintenance workflow from alert to completion
- **Quality Inspection** — Computer vision defect detection on uploaded product images
- **Maintenance Assistant** — RAG-based Q&A using approved maintenance documentation
- **Reports & Analytics** — Operational metrics and AI performance indicators
- **Role-Based Access** — Admin, supervisor, technician, operator, and inspector roles
- **Sensor Simulator** — Generates realistic sensor data with failure scenarios

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Material UI, Recharts, React Query, React Router |
| Backend | Python, FastAPI, Pydantic, JWT Auth |
| ML | scikit-learn (Isolation Forest, Random Forest) |
| Storage | In-memory (local), DynamoDB-ready |
| AI Services | Local models + Bedrock/SageMaker adapters |
| Deployment | Docker, AWS App Runner / ECS ready |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- npm

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 3. Sensor Simulator (optional)

```bash
cd simulator
pip install -r requirements.txt
python machine_simulator.py --scenario bearing_failure --machine MOTOR-204
```

### Demo Login

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@smartmaintain.ai | demo123 |
| Supervisor | supervisor@smartmaintain.ai | demo123 |
| Technician | tech@smartmaintain.ai | demo123 |
| Operator | operator@smartmaintain.ai | demo123 |
| Inspector | inspector@smartmaintain.ai | demo123 |

## Docker

```bash
docker compose up --build
```

Access the app at http://localhost:8080

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/auth/login` | Authenticate |
| GET | `/api/dashboard/stats` | Dashboard metrics |
| GET | `/api/machines` | List machines |
| GET | `/api/machines/{id}` | Machine details |
| GET | `/api/machines/{id}/readings` | Sensor history |
| GET | `/api/machines/{id}/prediction` | Failure prediction |
| POST | `/api/readings` | Submit sensor data |
| GET | `/api/alerts` | List alerts |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge alert |
| GET | `/api/work-orders` | List work orders |
| POST | `/api/work-orders` | Create work order |
| POST | `/api/inspections` | Upload inspection image |
| POST | `/api/assistant/query` | Maintenance assistant |
| GET | `/api/reports/summary` | Reports summary |

Full API docs at http://localhost:8080/docs

## Demo Scenario

1. Log in as supervisor
2. View dashboard with 5 machines operating normally
3. Start bearing failure simulation:
   ```bash
   python simulator/machine_simulator.py --scenario bearing_failure --machine MOTOR-204
   ```
4. Watch vibration and temperature increase on Motor 204 detail page
5. See health score decline and failure risk increase
6. Review auto-generated alert with AI explanation
7. Create work order from alert
8. Ask maintenance assistant about bearing inspection
9. Upload product image for quality inspection
10. Complete work order and verify machine recovery

## Project Structure

```
SmartMaintainAI/
├── frontend/          # React + TypeScript + Vite
├── backend/           # FastAPI application
├── simulator/         # Sensor data simulator
├── ml/                # Model training and artifacts
├── infrastructure/    # CloudFormation and deployment scripts
├── docs/              # Documentation
├── Dockerfile         # Multi-stage production build
└── docker-compose.yml # Local development stack
```

## AWS Deployment

The application supports AWS deployment with:

- **DynamoDB** for machine metadata, alerts, work orders
- **S3** for sensor files, images, documents
- **SageMaker** for ML model hosting
- **Bedrock** for AI explanations
- **Cognito** for authentication
- **SNS** for alert notifications
- **App Runner / ECS** for container hosting

Set environment variables to switch from local to AWS services:

```bash
USE_LOCAL_MODEL=false
SAGEMAKER_ENDPOINT=smartmaintain-predictions
STORAGE_BACKEND=dynamodb
```

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## License

MIT
