"""APScheduler-based alert scheduler."""
import asyncio
import logging
from datetime import datetime, date
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class AlertScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="America/New_York")
        self._started = False

    def start(self) -> None:
        if self._started:
            return

        # Price alert check: every 5 minutes on weekdays during market hours
        self.scheduler.add_job(
            self._check_price_alerts,
            trigger=CronTrigger(
                day_of_week="mon-fri",
                hour="9-16",
                minute="*/5",
                timezone="America/New_York",
            ),
            id="price_alert_checker",
            replace_existing=True,
        )

        # Earnings date check: daily at 8am ET
        self.scheduler.add_job(
            self._check_earnings_alerts,
            trigger=CronTrigger(hour=8, minute=0, timezone="America/New_York"),
            id="earnings_alert_checker",
            replace_existing=True,
        )

        self.scheduler.start()
        self._started = True
        logger.info("Alert scheduler started")

    def stop(self) -> None:
        if self._started and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self._started = False

    def add_reanalysis_job(self, alert) -> None:
        """Add a scheduled re-analysis job for an alert."""
        if not alert.cron_expression:
            return
        try:
            # Parse simple frequency to cron
            cron = alert.cron_expression
            if cron in ("daily", "0 8 * * *"):
                trigger = CronTrigger(hour=8, minute=0)
            elif cron in ("weekly", "0 8 * * 1"):
                trigger = CronTrigger(day_of_week="mon", hour=8, minute=0)
            elif cron in ("monthly", "0 8 1 * *"):
                trigger = CronTrigger(day=1, hour=8, minute=0)
            else:
                # Try to parse as cron expression
                parts = cron.split()
                if len(parts) == 5:
                    trigger = CronTrigger(
                        minute=parts[0], hour=parts[1], day=parts[2],
                        month=parts[3], day_of_week=parts[4],
                    )
                else:
                    trigger = CronTrigger(day_of_week="mon", hour=8, minute=0)

            job_id = f"reanalyze_{alert.id}"
            self.scheduler.add_job(
                self._run_reanalysis,
                trigger=trigger,
                id=job_id,
                args=[alert.ticker, alert.id],
                replace_existing=True,
            )
            logger.info(f"Scheduled re-analysis for {alert.ticker} with ID {job_id}")
        except Exception as e:
            logger.error(f"Error adding reanalysis job for alert {alert.id}: {e}")

    async def _check_price_alerts(self) -> None:
        """Batch check all active price alerts."""
        from app.models.db import AsyncSessionLocal
        from app.models.alert import Alert, AlertTrigger
        from app.ingestion.market_data import market_data_fetcher
        from app.core.sse_manager import sse_manager
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            stmt = select(Alert).where(
                Alert.is_active == True,
                Alert.alert_type.in_(["price_above", "price_below"]),
            )
            result = await db.execute(stmt)
            alerts = result.scalars().all()

            if not alerts:
                return

            # Batch fetch prices
            tickers = list(set(a.ticker for a in alerts))
            prices = {}
            for t in tickers:
                try:
                    price = await asyncio.to_thread(market_data_fetcher.fetch_fast_price, t)
                    if price:
                        prices[t] = price
                except Exception as e:
                    logger.warning(f"Failed to fetch price for {t}: {e}")

            # Check each alert
            for alert in alerts:
                price = prices.get(alert.ticker)
                if price is None or alert.target_price is None:
                    continue

                triggered = False
                if alert.alert_type == "price_above" and price >= alert.target_price:
                    triggered = True
                elif alert.alert_type == "price_below" and price <= alert.target_price:
                    triggered = True

                if triggered:
                    msg = f"{alert.ticker} price ${price:.2f} {'≥' if alert.alert_type == 'price_above' else '≤'} target ${alert.target_price:.2f}"
                    trigger = AlertTrigger(
                        alert_id=alert.id,
                        triggered_at=datetime.utcnow(),
                        trigger_value=msg,
                        action_taken="SSE notification sent",
                    )
                    db.add(trigger)
                    alert.last_triggered_at = datetime.utcnow()
                    alert.is_active = False  # One-shot alerts deactivate after trigger

                    await sse_manager.push_notification({
                        "event_type": "alert_triggered",
                        "payload": {
                            "alert_id": alert.id,
                            "ticker": alert.ticker,
                            "message": msg,
                            "alert_type": alert.alert_type,
                        },
                    })
                    logger.info(f"Alert triggered: {msg}")

            await db.commit()

    async def _check_earnings_alerts(self) -> None:
        """Check for upcoming earnings dates."""
        from app.models.db import AsyncSessionLocal
        from app.models.alert import Alert, AlertTrigger
        from app.ingestion.financials import financials_fetcher
        from app.core.sse_manager import sse_manager
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            stmt = select(Alert).where(
                Alert.is_active == True,
                Alert.alert_type == "earnings_date",
            )
            result = await db.execute(stmt)
            alerts = result.scalars().all()

            for alert in alerts:
                try:
                    cal = await asyncio.to_thread(financials_fetcher.fetch_earnings_calendar, alert.ticker)
                    if not cal:
                        continue

                    # Look for earnings date within next 7 days
                    import yfinance as yf
                    t = yf.Ticker(alert.ticker)
                    calendar = t.calendar
                    if calendar is None:
                        continue

                    earnings_date = None
                    if hasattr(calendar, 'get'):
                        earnings_date = calendar.get("Earnings Date")
                    elif hasattr(calendar, 'loc'):
                        try:
                            earnings_date = calendar.loc["Earnings Date"].iloc[0] if not calendar.empty else None
                        except Exception:
                            pass

                    if earnings_date:
                        if isinstance(earnings_date, (list, tuple)):
                            earnings_date = earnings_date[0]
                        # Normalize to plain date — handles both timezone-aware Timestamps and datetime
                        if hasattr(earnings_date, 'date'):
                            earnings_date = earnings_date.date()
                        if not isinstance(earnings_date, date):
                            earnings_date = None
                        if earnings_date:
                            days_until = (earnings_date - date.today()).days
                            if 0 <= days_until <= 7:
                                msg = f"{alert.ticker} earnings in {days_until} days ({earnings_date})"
                                trigger = AlertTrigger(
                                    alert_id=alert.id,
                                    triggered_at=datetime.utcnow(),
                                    trigger_value=msg,
                                    action_taken="SSE notification sent",
                                )
                                db.add(trigger)
                                alert.last_triggered_at = datetime.utcnow()
                                await sse_manager.push_notification({
                                    "event_type": "alert_triggered",
                                    "payload": {
                                        "alert_id": alert.id,
                                        "ticker": alert.ticker,
                                        "message": msg,
                                        "alert_type": "earnings_date",
                                    },
                                })
                except Exception as e:
                    logger.warning(f"Error checking earnings for {alert.ticker}: {e}")

            await db.commit()

    async def _run_reanalysis(self, ticker: str, alert_id: str) -> None:
        """Trigger a re-analysis for a scheduled alert."""
        from app.models.db import AsyncSessionLocal
        from app.models.analysis import AnalysisJob
        from app.models.alert import Alert, AlertTrigger
        from app.core.orchestrator import orchestrator
        from sqlalchemy import select
        import uuid

        async with AsyncSessionLocal() as db:
            # Create new analysis job
            job = AnalysisJob(
                id=str(uuid.uuid4()),
                ticker=ticker,
                status="pending",
                created_at=datetime.utcnow(),
            )
            db.add(job)
            await db.commit()

            # Log trigger
            stmt = select(Alert).where(Alert.id == alert_id)
            result = await db.execute(stmt)
            alert = result.scalar_one_or_none()
            if alert:
                trigger = AlertTrigger(
                    alert_id=alert_id,
                    triggered_at=datetime.utcnow(),
                    trigger_value=f"Scheduled re-analysis triggered for {ticker}",
                    action_taken=f"New analysis job {job.id} created",
                )
                db.add(trigger)
                alert.last_triggered_at = datetime.utcnow()
                await db.commit()

            # Run analysis
            async with AsyncSessionLocal() as analysis_db:
                await orchestrator.run_analysis(job.id, ticker, analysis_db)


alert_scheduler = AlertScheduler()
