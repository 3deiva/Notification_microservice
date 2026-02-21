from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.events import HealthResponse, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    return {"status": "UP", "service": "notification-service"}


@router.get(
    "/notifications/{employee_id}",
    response_model=list[NotificationResponse],
    tags=["notifications"],
)
async def get_notifications(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    notifications = await service.get_notifications_by_employee(employee_id)
    if not notifications:
        raise HTTPException(status_code=404, detail=f"No notifications found for employee {employee_id}")

    return [
        NotificationResponse(
            event_type=n.event_type,
            channel=n.channel_type,
            status=n.status,
            timestamp=n.created_at,
        )
        for n in notifications
    ]
