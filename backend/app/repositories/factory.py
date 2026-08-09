"""Repository factory - selects memory or DynamoDB backend."""

from functools import lru_cache

from app.core.config import get_settings


@lru_cache
def get_storage_backend() -> str:
    return get_settings().storage_backend


def get_machine_repository():
    if get_storage_backend() == "dynamodb":
        from app.repositories.dynamodb import DynamoDBMachineRepository
        return DynamoDBMachineRepository()
    from app.repositories.base import MachineRepository
    return MachineRepository()


def get_alert_repository():
    if get_storage_backend() == "dynamodb":
        from app.repositories.dynamodb import DynamoDBAlertRepository
        return DynamoDBAlertRepository()
    from app.repositories.base import AlertRepository
    return AlertRepository()


def get_work_order_repository():
    if get_storage_backend() == "dynamodb":
        from app.repositories.dynamodb import DynamoDBWorkOrderRepository
        return DynamoDBWorkOrderRepository()
    from app.repositories.base import WorkOrderRepository
    return WorkOrderRepository()


def get_inspection_repository():
    if get_storage_backend() == "dynamodb":
        from app.repositories.dynamodb import DynamoDBInspectionRepository
        return DynamoDBInspectionRepository()
    from app.repositories.base import InspectionRepository
    return InspectionRepository()


def get_feedback_repository():
    from app.repositories.base import FeedbackRepository
    return FeedbackRepository()


def get_user_repository():
    from app.repositories.base import UserRepository
    return UserRepository()


def get_dashboard_stats():
    from app.repositories.base import get_dashboard_stats as _stats
    return _stats()
