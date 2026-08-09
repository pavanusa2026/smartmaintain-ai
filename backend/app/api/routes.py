from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from typing import Optional
import uuid

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.rate_limit import check_rate_limit, reset_rate_limit
from app.core.security import create_access_token, get_current_user, require_roles, verify_password
from app.core.validators import strip_and_validate_text, validate_image_content
from app.repositories.factory import (
    get_alert_repository,
    get_dashboard_stats,
    get_feedback_repository,
    get_inspection_repository,
    get_machine_repository,
    get_user_repository,
    get_work_order_repository,
)
from app.schemas.domain import (
    Alert,
    AlertUpdate,
    AssistantQuery,
    AssistantResponse,
    AuditEvent,
    DashboardStats,
    FailurePrediction,
    Feedback,
    FeedbackCreate,
    Inspection,
    InspectionReview,
    LoginRequest,
    Machine,
    MachineCreate,
    MachineUpdate,
    SensorReading,
    SensorReadingCreate,
    TokenResponse,
    WorkOrder,
    WorkOrderCreate,
    WorkOrderUpdate,
)
from app.services.audit_service import AuditService
from app.services.bedrock_service import BedrockService, InspectionService
from app.services.monitoring_service import process_sensor_reading
from app.services.prediction_service import get_prediction_service

router = APIRouter()
audit = AuditService()


# --- Auth ---

@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    settings = get_settings()
    check_rate_limit(
        request,
        max_attempts=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
        scope="login",
    )
    user_repo = get_user_repository()
    user = user_repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    reset_rate_limit(request, "login")
    token = create_access_token(
        {"sub": user["userId"], "email": user["email"], "role": user["role"], "name": user["name"]}
    )
    return TokenResponse(
        access_token=token,
        role=user["role"],
        name=user["name"],
        email=user["email"],
    )


# --- Dashboard ---

@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(user: dict = Depends(get_current_user)):
    return get_dashboard_stats()


# --- Machines ---

@router.get("/machines", response_model=list[Machine])
async def list_machines(
    status: Optional[str] = Query(None, pattern="^(healthy|warning|critical|offline)$"),
    search: Optional[str] = Query(None, max_length=100),
    user: dict = Depends(get_current_user),
):
    return get_machine_repository().list_machines(status=status, search=search)


@router.post("/machines", response_model=Machine)
async def create_machine(
    body: MachineCreate,
    user: dict = Depends(require_roles("admin", "supervisor")),
):
    repo = get_machine_repository()
    if body.machineId and repo.get_machine(body.machineId):
        raise HTTPException(status_code=409, detail="Machine ID already exists")
    data = body.model_dump()
    machine = repo.create_machine(data)
    audit.log(user["userId"], "create", "machine", machine["machineId"], {"name": machine.get("name")})
    return machine


@router.get("/machines/{machine_id}", response_model=Machine)
async def get_machine(machine_id: str, user: dict = Depends(get_current_user)):
    machine = get_machine_repository().get_machine(machine_id)
    if not machine:
        raise NotFoundError("Machine not found")
    return machine


@router.patch("/machines/{machine_id}", response_model=Machine)
async def update_machine(
    machine_id: str,
    body: MachineUpdate,
    user: dict = Depends(require_roles("admin", "supervisor")),
):
    machine = get_machine_repository().update_machine(machine_id, body.model_dump(exclude_unset=True))
    if not machine:
        raise NotFoundError("Machine not found")
    audit.log(user["userId"], "update", "machine", machine_id)
    return machine


@router.get("/machines/{machine_id}/readings", response_model=list[SensorReading])
async def get_readings(
    machine_id: str,
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    repo = get_machine_repository()
    if not repo.get_machine(machine_id):
        raise NotFoundError("Machine not found")
    return repo.get_readings(machine_id, limit=limit)


@router.get("/machines/{machine_id}/prediction", response_model=FailurePrediction)
async def get_prediction(machine_id: str, user: dict = Depends(get_current_user)):
    repo = get_machine_repository()
    machine = repo.get_machine(machine_id)
    if not machine:
        raise NotFoundError("Machine not found")
    readings = repo.get_readings(machine_id, limit=20)
    return get_prediction_service().predict(
        machine_id,
        readings,
        machine_type=machine.get("type", "motor"),
        operating_hours=machine.get("operatingHours", 0),
    )


# --- Readings ---

@router.post("/readings")
async def submit_reading(body: SensorReadingCreate, user: dict = Depends(get_current_user)):
    repo = get_machine_repository()
    if not repo.get_machine(body.machineId):
        raise NotFoundError(f"Machine {body.machineId} not found")
    try:
        return await process_sensor_reading(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# --- Predictions ---

@router.post("/predictions/run", response_model=FailurePrediction)
async def run_prediction(
    machineId: str = Query(..., min_length=3, max_length=32),
    user: dict = Depends(get_current_user),
):
    repo = get_machine_repository()
    machine = repo.get_machine(machineId)
    if not machine:
        raise NotFoundError("Machine not found")
    readings = repo.get_readings(machineId, limit=20)
    return get_prediction_service().predict(
        machineId,
        readings,
        machine_type=machine.get("type", "motor"),
        operating_hours=machine.get("operatingHours", 0),
    )


# --- Alerts ---

@router.get("/alerts", response_model=list[Alert])
async def list_alerts(
    status: Optional[str] = Query(None, pattern="^(new|acknowledged|investigating|closed)$"),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    machineId: Optional[str] = Query(None, min_length=3, max_length=32),
    user: dict = Depends(get_current_user),
):
    return get_alert_repository().list_alerts(status=status, severity=severity, machine_id=machineId)


@router.patch("/alerts/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: str,
    body: AlertUpdate,
    user: dict = Depends(require_roles("admin", "supervisor", "technician")),
):
    alert = get_alert_repository().update_alert(alert_id, body.model_dump(exclude_unset=True))
    if not alert:
        raise NotFoundError("Alert not found")
    audit.log(user["userId"], "update", "alert", alert_id, {"status": body.status})
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(
    alert_id: str,
    user: dict = Depends(require_roles("admin", "supervisor", "technician")),
):
    alert = get_alert_repository().update_alert(
        alert_id,
        {"status": "acknowledged", "acknowledgedBy": user.get("name", user.get("email"))},
    )
    if not alert:
        raise NotFoundError("Alert not found")
    audit.log(user["userId"], "acknowledge", "alert", alert_id)
    return alert


# --- Work Orders ---

@router.get("/work-orders", response_model=list[WorkOrder])
async def list_work_orders(
    status: Optional[str] = Query(None, pattern="^(open|in_progress|completed|canceled)$"),
    machineId: Optional[str] = Query(None, min_length=3, max_length=32),
    user: dict = Depends(get_current_user),
):
    return get_work_order_repository().list_work_orders(status=status, machine_id=machineId)


@router.post("/work-orders", response_model=WorkOrder)
async def create_work_order(
    body: WorkOrderCreate,
    user: dict = Depends(require_roles("admin", "supervisor")),
):
    repo = get_machine_repository()
    if not repo.get_machine(body.machineId):
        raise NotFoundError("Machine not found")
    wo = get_work_order_repository().create_work_order(body.model_dump())
    audit.log(user["userId"], "create", "work_order", wo["workOrderId"], {"machineId": body.machineId})
    return wo


@router.patch("/work-orders/{work_order_id}", response_model=WorkOrder)
async def update_work_order(
    work_order_id: str,
    body: WorkOrderUpdate,
    user: dict = Depends(require_roles("admin", "supervisor", "technician")),
):
    wo = get_work_order_repository().update_work_order(work_order_id, body.model_dump(exclude_unset=True))
    if not wo:
        raise NotFoundError("Work order not found")
    audit.log(user["userId"], "update", "work_order", work_order_id, {"status": body.status})
    return wo


# --- Inspections ---

@router.post("/inspections", response_model=Inspection)
async def create_inspection(
    file: UploadFile = File(...),
    productId: str = Form(""),
    user: dict = Depends(require_roles("admin", "supervisor", "inspector")),
):
    contents = await file.read()
    try:
        ext = validate_image_content(contents, file.content_type, get_settings().max_upload_size_mb)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    safe_name = f"{uuid.uuid4().hex}{ext}"
    safe_product_id = strip_and_validate_text(productId.strip(), "productId", min_len=0, max_len=64) if productId.strip() else f"PROD-{safe_name}"

    analysis = InspectionService().analyze_image(contents, safe_name)
    inspection = get_inspection_repository().create_inspection(
        {
            "productId": safe_product_id,
            "imageUrl": f"/api/inspections/images/{safe_name}",
            "imageKey": safe_name,
            "predictedResult": analysis["predictedResult"],
            "defectType": analysis["defectType"],
            "confidence": analysis["confidence"],
        }
    )
    audit.log(user["userId"], "create", "inspection", inspection["inspectionId"])
    return inspection


@router.get("/inspections", response_model=list[Inspection])
async def list_inspections(user: dict = Depends(get_current_user)):
    return get_inspection_repository().list_inspections()


@router.get("/inspections/{inspection_id}", response_model=Inspection)
async def get_inspection(inspection_id: str, user: dict = Depends(get_current_user)):
    inspection = get_inspection_repository().get_inspection(inspection_id)
    if not inspection:
        raise NotFoundError("Inspection not found")
    return inspection


@router.patch("/inspections/{inspection_id}/review", response_model=Inspection)
async def review_inspection(
    inspection_id: str,
    body: InspectionReview,
    user: dict = Depends(require_roles("inspector", "supervisor")),
):
    updates = body.model_dump(exclude_unset=True)
    inspection = get_inspection_repository().update_inspection(inspection_id, updates)
    if not inspection:
        raise NotFoundError("Inspection not found")
    audit.log(user["userId"], "review", "inspection", inspection_id, {"result": body.reviewedResult})
    return inspection


# --- Assistant ---

@router.post("/assistant/query", response_model=AssistantResponse)
async def assistant_query(body: AssistantQuery, user: dict = Depends(get_current_user)):
    return BedrockService().query_assistant(body.question, body.machineId)


# --- Feedback ---

@router.post("/feedback", response_model=Feedback)
async def submit_feedback(body: FeedbackCreate, user: dict = Depends(require_roles("admin", "supervisor", "technician"))):
    data = body.model_dump()
    data["userId"] = user.get("userId", "")
    return get_feedback_repository().create_feedback(data)


# --- Audit ---

@router.get("/audit", response_model=list[AuditEvent])
async def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(require_roles("admin")),
):
    return audit.list_events(limit=limit)


# --- Reports ---

@router.get("/reports/summary")
async def reports_summary(user: dict = Depends(require_roles("admin", "supervisor", "manager"))):
    alert_repo = get_alert_repository()
    wo_repo = get_work_order_repository()
    insp_repo = get_inspection_repository()
    machine_repo = get_machine_repository()

    alerts = alert_repo.list_alerts()
    work_orders = wo_repo.list_work_orders()
    inspections = insp_repo.list_inspections(limit=200)
    machines = machine_repo.list_machines()

    closed_alerts = [a for a in alerts if a.get("status") == "closed"]
    completed_wo = [w for w in work_orders if w.get("status") == "completed"]
    failed_inspections = [i for i in inspections if i.get("predictedResult") == "fail"]

    avg_failure_risk = (
        sum(m.get("failureProbability", 0) for m in machines) / len(machines) if machines else 0
    )

    return {
        "totalAlerts": len(alerts),
        "closedAlerts": len(closed_alerts),
        "alertResponseRate": round(len(closed_alerts) / max(len(alerts), 1) * 100, 1),
        "totalWorkOrders": len(work_orders),
        "completedWorkOrders": len(completed_wo),
        "maintenanceCompletionRate": round(len(completed_wo) / max(len(work_orders), 1) * 100, 1),
        "totalInspections": len(inspections),
        "defectRate": round(len(failed_inspections) / max(len(inspections), 1) * 100, 1),
        "averageFailureRisk": round(avg_failure_risk * 100, 1),
        "machineAvailability": round(
            sum(1 for m in machines if m.get("status") == "healthy") / max(len(machines), 1) * 100, 1
        ),
    }
