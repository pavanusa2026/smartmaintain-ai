# SmartMaintain AI - API Specification

Base URL: `/api`

Authentication: Bearer JWT token from `POST /api/auth/login`

## Authentication

### POST /api/auth/login
```json
{ "email": "supervisor@smartmaintain.ai", "password": "demo123" }
```
Response: `{ "access_token", "token_type", "role", "name", "email" }`

## Machines

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /machines | List all machines (filter: status, search) |
| POST | /machines | Register new machine |
| GET | /machines/{id} | Get machine details |
| PATCH | /machines/{id} | Update machine |
| GET | /machines/{id}/readings | Get sensor history |
| GET | /machines/{id}/prediction | Get failure prediction |

## Sensor Data

### POST /api/readings
```json
{
  "machineId": "MOTOR-204",
  "temperature": 71.2,
  "vibration": 2.4,
  "pressure": 41.8,
  "powerConsumption": 13.5,
  "rotationalSpeed": 1795,
  "operatingLoad": 72
}
```
Returns reading, prediction, optional alert, and updated machine status.

## Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /alerts | List alerts (filter: status, severity, machineId) |
| PATCH | /alerts/{id} | Update alert |
| POST | /alerts/{id}/acknowledge | Acknowledge alert |

## Work Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /work-orders | List work orders |
| POST | /work-orders | Create work order |
| PATCH | /work-orders/{id} | Update work order |

## Inspections

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /inspections | Upload image (multipart/form-data) |
| GET | /inspections | List inspections |
| GET | /inspections/{id} | Get inspection result |
| PATCH | /inspections/{id}/review | Confirm/override result |

## Assistant

### POST /api/assistant/query
```json
{ "question": "What should I inspect when motor vibration increases?", "machineId": "MOTOR-204" }
```

## Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | App health check |
| GET | /ready | Dependency readiness |
