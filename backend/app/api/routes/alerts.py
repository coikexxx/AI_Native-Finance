"""Alert routes: CRUD alerts + SSE notification stream."""
import asyncio
from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.db import get_db
from app.models.alert import Alert, AlertTrigger
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertTriggerResponse
from app.core.sse_manager import sse_manager

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("/stream")
async def notification_stream():
    """SSE stream for global alert notifications."""
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = sse_manager.create_notification_stream()
        yield sse_manager.format_sse({"event_type": "connected", "payload": {}})
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield sse_manager.format_sse(event)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            sse_manager.remove_notification_stream(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("", response_model=List[AlertResponse])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    stmt = select(Alert).order_by(desc(Alert.created_at))
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    return [
        AlertResponse(
            id=a.id, ticker=a.ticker, alert_type=a.alert_type,
            target_price=a.target_price, cron_expression=a.cron_expression,
            event_description=a.event_description, is_active=a.is_active,
            created_at=a.created_at, last_triggered_at=a.last_triggered_at,
            trigger_count=len(a.triggers),
        )
        for a in alerts
    ]


@router.post("", response_model=AlertResponse)
async def create_alert(
    payload: AlertCreate,
    db: AsyncSession = Depends(get_db),
):
    alert = Alert(
        ticker=payload.ticker,
        alert_type=payload.alert_type,
        target_price=payload.target_price,
        cron_expression=payload.cron_expression,
        event_description=payload.event_description,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    # Register scheduled re-analysis job if applicable
    if payload.alert_type == "re_analyze":
        try:
            from app.alerts.scheduler import alert_scheduler
            alert_scheduler.add_reanalysis_job(alert)
        except Exception:
            pass

    return AlertResponse(
        id=alert.id, ticker=alert.ticker, alert_type=alert.alert_type,
        target_price=alert.target_price, cron_expression=alert.cron_expression,
        event_description=alert.event_description, is_active=alert.is_active,
        created_at=alert.created_at, trigger_count=0,
    )


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    payload: AlertUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if payload.is_active is not None:
        alert.is_active = payload.is_active
    if payload.target_price is not None:
        alert.target_price = payload.target_price
    if payload.cron_expression is not None:
        alert.cron_expression = payload.cron_expression
    if payload.event_description is not None:
        alert.event_description = payload.event_description

    await db.commit()
    await db.refresh(alert)
    return AlertResponse(
        id=alert.id, ticker=alert.ticker, alert_type=alert.alert_type,
        target_price=alert.target_price, cron_expression=alert.cron_expression,
        event_description=alert.event_description, is_active=alert.is_active,
        created_at=alert.created_at, last_triggered_at=alert.last_triggered_at,
        trigger_count=len(alert.triggers),
    )


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    await db.commit()


@router.get("/{alert_id}/history", response_model=List[AlertTriggerResponse])
async def get_alert_history(alert_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AlertTrigger).where(AlertTrigger.alert_id == alert_id).order_by(
        desc(AlertTrigger.triggered_at)
    )
    result = await db.execute(stmt)
    triggers = result.scalars().all()
    return [
        AlertTriggerResponse(
            id=t.id, alert_id=t.alert_id,
            triggered_at=t.triggered_at,
            trigger_value=t.trigger_value,
            action_taken=t.action_taken,
        )
        for t in triggers
    ]
