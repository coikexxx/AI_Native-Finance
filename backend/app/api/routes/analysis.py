"""Analysis routes: POST /analyze, GET /analysis/{id}, SSE stream."""
import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.db import get_db
from app.models.analysis import AnalysisJob, AnalysisResult
from app.models.evidence import EvidenceItem
from app.schemas.analysis import AnalysisRequest
from app.schemas.output import AnalysisJobResponse, AnalysisResultResponse, EvidenceReference
from app.core.orchestrator import orchestrator
from app.core.sse_manager import sse_manager
from app.governance.prompt_guardrails import validate_ticker

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisJobResponse)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a new analysis job for a ticker. Returns job_id immediately."""
    ticker = request.ticker

    is_valid, err = validate_ticker(ticker)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    job = AnalysisJob(
        id=str(uuid.uuid4()),
        ticker=ticker,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Start analysis in background (uses a NEW db session)
    async def run_in_background(job_id: str, ticker: str):
        from app.models.db import AsyncSessionLocal
        async with AsyncSessionLocal() as bg_session:
            await orchestrator.run_analysis(job_id, ticker, bg_session)

    background_tasks.add_task(run_in_background, job.id, ticker)

    return AnalysisJobResponse(
        job_id=job.id,
        ticker=job.ticker,
        status=job.status,
        created_at=job.created_at,
    )


@router.get("/history")
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get history of analysis jobs."""
    stmt = select(AnalysisJob).order_by(desc(AnalysisJob.created_at)).limit(limit).offset(offset)
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [
        AnalysisJobResponse(
            job_id=j.id,
            ticker=j.ticker,
            status=j.status,
            created_at=j.created_at,
            completed_at=j.completed_at,
            error_message=j.error_message,
        )
        for j in jobs
    ]


@router.get("/{job_id}/stream")
async def stream_analysis(job_id: str, db: AsyncSession = Depends(get_db)):
    """SSE stream of analysis progress events."""
    # Verify job exists
    stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        # If already complete, send the result immediately
        if job.status == "complete" and job.result:
            res = job.result
            yield sse_manager.format_sse({
                "event_type": "complete",
                "agent_name": None,
                "payload": {
                    "decision": res.decision,
                    "scorecard": res.scorecard,
                    "decision_rationale": res.decision_rationale,
                },
            })
            return

        if job.status == "failed":
            yield sse_manager.format_sse({
                "event_type": "error",
                "payload": {"message": job.error_message or "Analysis failed"},
            })
            return

        # Register SSE queue and yield events
        queue = sse_manager.create_analysis_stream(job_id)
        try:
            # Send initial connected event
            yield sse_manager.format_sse({"event_type": "connected", "payload": {"job_id": job_id}})

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield sse_manager.format_sse(event)
                    if event.get("event_type") in ("complete", "error"):
                        break
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield ": heartbeat\n\n"
        finally:
            sse_manager.remove_analysis_stream(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{job_id}", response_model=AnalysisResultResponse)
async def get_analysis(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get the full analysis result for a completed job."""
    stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status == "pending" or job.status == "running":
        return AnalysisResultResponse(
            job_id=job.id,
            ticker=job.ticker,
            status=job.status,
            created_at=job.created_at,
        )

    # Load evidence items
    ev_stmt = select(EvidenceItem).where(EvidenceItem.job_id == job_id)
    ev_result = await db.execute(ev_stmt)
    evidence_items = ev_result.scalars().all()

    evidence_refs = [
        EvidenceReference(
            citation_key=e.citation_key,
            agent_name=e.agent_name,
            source_label=e.source_label,
            source_type=e.source_type,
            excerpt=e.excerpt,
            source_url=e.source_url,
        )
        for e in evidence_items
    ]

    res = job.result
    if not res:
        return AnalysisResultResponse(
            job_id=job.id,
            ticker=job.ticker,
            status=job.status,
            created_at=job.created_at,
            error_message=job.error_message,
        )

    return AnalysisResultResponse(
        job_id=job.id,
        ticker=job.ticker,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        scorecard=res.scorecard,
        decision=res.decision,
        decision_rationale=res.decision_rationale,
        investment_memo_md=res.investment_memo_md,
        evidence_items=evidence_refs,
    )
