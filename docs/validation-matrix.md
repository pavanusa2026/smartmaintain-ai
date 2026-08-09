# Validation Matrix

| Form / Endpoint | Field | Rules | Error Message |
|-----------------|-------|-------|---------------|
| Login | email | Required, valid email format | "Invalid email address" |
| Login | password | Required, min 6 chars | "Password must be at least 6 characters" |
| Machine Create | name | 2–100 chars, no script injection | "Name must be at least 2 characters" |
| Machine Create | location | 2–200 chars, required | "Location is required" |
| Machine Create | machineId | Optional, alphanumeric + hyphens, 3–32 chars | "Invalid machine ID format" |
| Machine Create | type | Enum: motor, pump, conveyor, etc. | Pydantic enum error |
| Sensor Reading | machineId | Valid machine ID format | "Invalid machine ID format" |
| Sensor Reading | temperature | -50 to 500, not NaN | "Temperature must be between -50 and 500" |
| Sensor Reading | vibration | 0 to 100 | "Vibration must be between 0 and 100" |
| Sensor Reading | pressure | 0 to 500 | "Pressure must be between 0 and 500" |
| Sensor Reading | powerConsumption | 0 to 1000 | "Power must be between 0 and 1000" |
| Sensor Reading | rotationalSpeed | 0 to 50000 | "Speed must be between 0 and 50000" |
| Sensor Reading | operatingLoad | 0 to 100 | "Load must be between 0 and 100" |
| Work Order | title | 3–200 chars, required | "Title must be at least 3 characters" |
| Work Order | machineId | Valid format, must exist | "Machine not found" |
| Work Order | dueDate | YYYY-MM-DD, not in past | "Due date cannot be in the past" |
| Work Order | priority | Enum: low, normal, high, emergency | Pydantic enum error |
| Inspection Upload | file | JPEG/PNG/WebP, max 10MB | "File must be JPEG, PNG, or WebP" |
| Inspection Review | reviewedResult | "pass" or "fail" | "Reviewed result must be pass or fail" |
| Assistant Query | question | 5–1000 chars, no script tags | "Question must be at least 5 characters" |
| Assistant Query | machineId | Optional, valid ID format | "Invalid machine ID format" |
| Feedback | feedbackType | Enum: correct, false_positive, etc. | Pydantic enum error |
| Feedback | comment | Max 1000 chars | "Comment must not exceed 1000 characters" |
| Alert Update | status | Enum: new, acknowledged, investigating, closed | Pydantic enum error |
| Probability fields | confidence, failureProbability | 0.0 to 1.0 | "Must be between 0 and 1" |

## Client + Server Validation

All forms validate on the client first (instant feedback) and are re-validated server-side via Pydantic. Server responses use consistent JSON:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation failed",
    "details": { "fields": [{ "field": "temperature", "message": "..." }] }
  }
}
```
