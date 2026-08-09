# Database Design - DynamoDB

## Tables

| Table | Partition Key | Sort Key | GSIs |
|-------|--------------|----------|------|
| smartmaintain-machines | machineId | — | status-index, productionLine-index |
| smartmaintain-alerts | alertId | — | status-index |
| smartmaintain-work-orders | workOrderId | — | status-index |
| smartmaintain-inspections | inspectionId | — | — |

## Access Patterns

| Pattern | Table | Key / Index |
|---------|-------|-------------|
| Get machine by ID | machines | PK: machineId |
| List machines by status | machines | GSI: status-index |
| List machines by production line | machines | GSI: productionLine-index |
| Get alert by ID | alerts | PK: alertId |
| List alerts by status | alerts | GSI: status-index |
| Get work order by ID | work_orders | PK: workOrderId |
| List work orders by status | work_orders | GSI: status-index |
| Get inspection by ID | inspections | PK: inspectionId |

## Deploy

```bash
aws cloudformation deploy \
  --template-file infrastructure/dynamodb.yaml \
  --stack-name smartmaintain-db \
  --parameter-overrides Environment=dev
```

Set `STORAGE_BACKEND=dynamodb` and table name env vars to switch from in-memory storage.
