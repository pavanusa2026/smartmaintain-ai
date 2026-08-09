from datetime import datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.validators import (
    strip_and_validate_text,
    validate_due_date,
    validate_email,
    validate_machine_id,
    validate_probability,
    validate_sensor_value,
)


class MachineStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class MachineType(str, Enum):
    MOTOR = "motor"
    PUMP = "pump"
    CONVEYOR = "conveyor"
    CNC = "cnc"
    COMPRESSOR = "compressor"
    OVEN = "oven"
    PACKAGING = "packaging"
    OTHER = "other"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    CLOSED = "closed"


class AlertType(str, Enum):
    TEMPERATURE = "temperature"
    VIBRATION = "vibration"
    FAILURE_RISK = "failure_risk"
    QUALITY = "quality"
    ANOMALY = "anomaly"


class WorkOrderPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EMERGENCY = "emergency"


class WorkOrderStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class DefectType(str, Enum):
    SCRATCH = "scratch"
    CRACK = "crack"
    MISALIGNMENT = "misalignment"
    CONTAMINATION = "contamination"
    MISSING_COMPONENT = "missing_component"
    PACKAGING_DAMAGE = "packaging_damage"
    OTHER = "other"
    NONE = "none"


class FeedbackType(str, Enum):
    CORRECT = "correct"
    FALSE_POSITIVE = "false_positive"
    INCORRECT_TYPE = "incorrect_type"
    CONFIRMED = "confirmed"
    HEALTHY = "healthy"
    DIFFERENT_REPAIR = "different_repair"


# --- Machine ---

class MachineBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100)]
    type: MachineType
    location: Annotated[str, Field(min_length=2, max_length=200)]
    manufacturer: Annotated[str, Field(max_length=100)] = ""
    modelNumber: Annotated[str, Field(max_length=50)] = ""
    installationDate: str = ""
    productionLine: Annotated[str, Field(max_length=100)] = ""

    @field_validator("name", "location", "manufacturer", "modelNumber", "productionLine")
    @classmethod
    def validate_text_fields(cls, v: str, info) -> str:
        if not v:
            return v
        return strip_and_validate_text(v, info.field_name, min_len=1 if info.field_name != "manufacturer" else 0)


class MachineCreate(MachineBase):
    machineId: Optional[str] = None

    @field_validator("machineId")
    @classmethod
    def validate_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_machine_id(v)


class Machine(MachineBase):
    machineId: str
    status: MachineStatus = MachineStatus.HEALTHY
    lastReadingAt: Optional[datetime] = None
    healthScore: float = Field(default=100.0, ge=0, le=100)
    failureProbability: float = Field(default=0.0, ge=0, le=1)
    lastMaintenanceDate: Optional[str] = None
    operatingHours: float = Field(default=0.0, ge=0)
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class MachineUpdate(BaseModel):
    name: Optional[Annotated[str, Field(min_length=2, max_length=100)]] = None
    location: Optional[Annotated[str, Field(min_length=2, max_length=200)]] = None
    status: Optional[MachineStatus] = None
    healthScore: Optional[float] = Field(default=None, ge=0, le=100)
    failureProbability: Optional[float] = Field(default=None, ge=0, le=1)

    @field_validator("name", "location")
    @classmethod
    def validate_text_fields(cls, v: Optional[str], info) -> Optional[str]:
        if v is None or not v:
            return v
        return strip_and_validate_text(v, info.field_name)


# --- Sensor Reading ---

class SensorReadingBase(BaseModel):
    machineId: str
    temperature: float
    vibration: float
    pressure: float
    powerConsumption: float
    rotationalSpeed: float
    operatingLoad: float

    @field_validator("machineId")
    @classmethod
    def validate_mid(cls, v: str) -> str:
        return validate_machine_id(v)

    @field_validator("temperature")
    @classmethod
    def validate_temp(cls, v: float) -> float:
        return validate_sensor_value(v, "temperature", -50, 500)

    @field_validator("vibration")
    @classmethod
    def validate_vib(cls, v: float) -> float:
        return validate_sensor_value(v, "vibration", 0, 100)

    @field_validator("pressure")
    @classmethod
    def validate_pressure(cls, v: float) -> float:
        return validate_sensor_value(v, "pressure", 0, 500)

    @field_validator("powerConsumption")
    @classmethod
    def validate_power(cls, v: float) -> float:
        return validate_sensor_value(v, "powerConsumption", 0, 1000)

    @field_validator("rotationalSpeed")
    @classmethod
    def validate_speed(cls, v: float) -> float:
        return validate_sensor_value(v, "rotationalSpeed", 0, 50000)

    @field_validator("operatingLoad")
    @classmethod
    def validate_load(cls, v: float) -> float:
        return validate_sensor_value(v, "operatingLoad", 0, 100)


class SensorReadingCreate(SensorReadingBase):
    timestamp: Optional[datetime] = None


class SensorReading(SensorReadingBase):
    readingId: str
    timestamp: datetime
    anomalyScore: float = Field(default=0.0, ge=0, le=1)


# --- Alert ---

class AlertBase(BaseModel):
    machineId: str
    severity: AlertSeverity
    alertType: AlertType
    title: Annotated[str, Field(min_length=3, max_length=200)]
    explanation: Annotated[str, Field(max_length=2000)] = ""
    recommendedAction: Annotated[str, Field(max_length=500)] = ""
    confidence: float = Field(default=0.0, ge=0, le=1)

    @field_validator("machineId")
    @classmethod
    def validate_mid(cls, v: str) -> str:
        return validate_machine_id(v)

    @field_validator("title", "explanation", "recommendedAction")
    @classmethod
    def validate_text(cls, v: str, info) -> str:
        if not v:
            return v
        return strip_and_validate_text(v, info.field_name, min_len=1 if info.field_name == "title" else 0)


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    acknowledgedBy: Optional[Annotated[str, Field(max_length=100)]] = None
    investigationNotes: Optional[Annotated[str, Field(max_length=2000)]] = None
    assignedTo: Optional[Annotated[str, Field(max_length=100)]] = None

    @field_validator("acknowledgedBy", "investigationNotes", "assignedTo")
    @classmethod
    def validate_text_fields(cls, v: Optional[str], info) -> Optional[str]:
        if v is None or not v:
            return v
        return strip_and_validate_text(v, info.field_name, min_len=1 if info.field_name == "acknowledgedBy" else 0)


class Alert(AlertBase):
    alertId: str
    status: AlertStatus = AlertStatus.NEW
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    acknowledgedBy: Optional[str] = None
    investigationNotes: Optional[str] = None
    assignedTo: Optional[str] = None
    modelVersion: Optional[str] = None


# --- Work Order ---

class WorkOrderBase(BaseModel):
    machineId: str
    alertId: Optional[str] = None
    title: Annotated[str, Field(min_length=3, max_length=200)]
    description: Annotated[str, Field(max_length=2000)] = ""
    priority: WorkOrderPriority = WorkOrderPriority.NORMAL
    assignedTo: Optional[Annotated[str, Field(max_length=100)]] = None
    dueDate: Optional[str] = None

    @field_validator("machineId")
    @classmethod
    def validate_mid(cls, v: str) -> str:
        return validate_machine_id(v)

    @field_validator("title", "description")
    @classmethod
    def validate_text(cls, v: str, info) -> str:
        if not v:
            return v
        return strip_and_validate_text(v, info.field_name, min_len=1 if info.field_name == "title" else 0)

    @field_validator("dueDate")
    @classmethod
    def validate_due(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return v
        return validate_due_date(v)


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    status: Optional[WorkOrderStatus] = None
    assignedTo: Optional[Annotated[str, Field(max_length=100)]] = None
    resolutionNotes: Optional[Annotated[str, Field(max_length=2000)]] = None
    actualFailureFound: Optional[bool] = None
    priority: Optional[WorkOrderPriority] = None


class WorkOrder(WorkOrderBase):
    workOrderId: str
    status: WorkOrderStatus = WorkOrderStatus.OPEN
    resolutionNotes: Optional[str] = None
    actualFailureFound: Optional[bool] = None
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None


# --- Inspection ---

class InspectionCreate(BaseModel):
    productId: Annotated[str, Field(max_length=100)] = ""

    @field_validator("productId")
    @classmethod
    def validate_pid(cls, v: str) -> str:
        if not v:
            return v
        return strip_and_validate_text(v, "productId", min_len=1, max_len=100)


class InspectionReview(BaseModel):
    reviewedResult: str
    reviewedBy: Annotated[str, Field(min_length=1, max_length=100)]
    defectType: Optional[DefectType] = None

    @field_validator("reviewedResult")
    @classmethod
    def validate_result(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ("pass", "fail"):
            raise ValueError("Reviewed result must be 'pass' or 'fail'")
        return cleaned

    @field_validator("reviewedBy")
    @classmethod
    def validate_reviewer(cls, v: str) -> str:
        return strip_and_validate_text(v, "reviewedBy")


class Inspection(BaseModel):
    inspectionId: str
    productId: str
    batchId: Optional[str] = None
    imageUrl: str
    imageKey: Optional[str] = None
    predictedResult: str
    defectType: DefectType = DefectType.NONE
    confidence: float = Field(ge=0, le=1)
    reviewedResult: Optional[str] = None
    reviewedBy: Optional[str] = None
    createdAt: datetime


# --- Prediction ---

class FailurePrediction(BaseModel):
    machineId: str
    failureProbability: float = Field(ge=0, le=1)
    predictionWindowDays: int = 7
    likelyFailureType: str = "unknown"
    confidence: float = Field(ge=0, le=1)
    healthScore: float = Field(ge=0, le=100)
    anomalyScore: float = Field(ge=0, le=1)
    remainingUsefulLifeHours: float = 0.0
    modelVersion: str
    primaryConcern: str = ""
    recommendedAction: str = ""
    predictionTimestamp: Optional[datetime] = None


# --- Assistant ---

class AssistantQuery(BaseModel):
    question: Annotated[str, Field(min_length=5, max_length=1000)]
    machineId: Optional[str] = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        return strip_and_validate_text(v, "question", min_len=5, max_len=1000)

    @field_validator("machineId")
    @classmethod
    def validate_mid(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return v
        return validate_machine_id(v)


class DocumentSource(BaseModel):
    title: str
    section: str
    revisionDate: str


class AssistantResponse(BaseModel):
    answer: str
    sources: list[DocumentSource]
    safetyNotice: str
    humanReviewReminder: str
    urgencyLevel: str = "medium"


# --- Feedback ---

class FeedbackCreate(BaseModel):
    entityType: str
    entityId: str
    feedbackType: FeedbackType
    comment: Annotated[str, Field(max_length=1000)] = ""
    userId: str = ""
    machineId: Optional[str] = None
    correctedFailureType: Optional[str] = None

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str) -> str:
        if not v:
            return v
        return strip_and_validate_text(v, "comment", min_len=0, max_len=1000)


class Feedback(FeedbackCreate):
    feedbackId: str
    createdAt: datetime


# --- Audit ---

class AuditEvent(BaseModel):
    eventId: str
    userId: str
    action: str
    resourceType: str
    resourceId: str
    timestamp: datetime
    metadata: dict = {}


# --- Auth ---

class LoginRequest(BaseModel):
    email: str
    password: Annotated[str, Field(min_length=6, max_length=128)]

    @field_validator("email")
    @classmethod
    def validate_login_email(cls, v: str) -> str:
        return validate_email(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    email: str


# --- Dashboard ---

class DashboardStats(BaseModel):
    totalMachines: int
    healthyMachines: int
    warningMachines: int
    criticalMachines: int
    offlineMachines: int
    openWorkOrders: int
    defectsDetectedToday: int
    activeAlerts: int
    estimatedDowntimeAvoidedHours: float


# --- Pagination ---

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    pageSize: int
    hasMore: bool
