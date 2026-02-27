"""
Agent OS: 4-phase analysis pipeline coordinator.

Phase 1: Parallel data ingestion
Phase 2: Index & feature extraction
Phase 3: Wave-based agent execution
Phase 4: Synthesis → Investment Memo
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Optional
import logging

from app.config import settings
from app.core.sse_manager import sse_manager
from app.governance.citations import CitationMapper
from app.ingestion.market_data import MarketDataFetcher
from app.ingestion.financials import FinancialsFetcher
from app.ingestion.company_info import CompanyInfoFetcher
from app.ingestion.news import NewsFetcher
from app.ingestion.earnings_calls import EarningsCallFetcher
from app.ingestion.macro import MacroFetcher
from app.storage.object_store import ObjectStore
from app.storage.vector_store import VectorStore
from app.storage.feature_store import FeatureStore
from app.storage.knowledge_graph import KnowledgeGraph
from app.tools.document_parser import chunk_text, generate_chunk_ids, generate_chunk_metadatas
from app.tools.time_series import TimeSeriesAnalyzer
from app.agents.industry_agent import IndustryAgent
from app.agents.financial_quality_agent import FinancialQualityAgent
from app.agents.business_model_agent import BusinessModelAgent
from app.agents.moat_agent import MoatAgent
from app.agents.management_agent import ManagementAgent
from app.agents.valuation_agent import ValuationAgent
from app.agents.risk_agent import RiskAgent
from app.agents.thesis_agent import ThesisAgent
from app.agents.monitoring_agent import MonitoringAgent

logger = logging.getLogger(__name__)

AGENT_DISPLAY_NAMES = {
    "IndustryAgent": "行业结构分析 Industry Analysis",
    "FinancialQualityAgent": "财务质量分析 Financial Quality",
    "ManagementAgent": "管理层评估 Management Assessment",
    "BusinessModelAgent": "商业模式分析 Business Model",
    "MoatAgent": "护城河量化 Economic Moat",
    "ValuationAgent": "估值分析 Valuation",
    "RiskAgent": "风险评估 Risk Assessment",
    "ThesisAgent": "投资论点综合 Investment Thesis",
    "MonitoringAgent": "监控框架 Monitoring Setup",
}


class AgentOrchestrator:
    def __init__(self):
        self.market_data = MarketDataFetcher()
        self.financials = FinancialsFetcher()
        self.company_info = CompanyInfoFetcher()
        self.news = NewsFetcher()
        self.earnings = EarningsCallFetcher()
        self.macro = MacroFetcher()
        self.object_store = ObjectStore()
        self.vector_store = VectorStore()
        self.feature_store = FeatureStore()
        self.kg = KnowledgeGraph()
        self.ts_analyzer = TimeSeriesAnalyzer()

    async def _emit(self, job_id: str, event_type: str, agent_name: Optional[str] = None, payload: dict = None):
        await sse_manager.push_analysis_event(job_id, {
            "event_type": event_type,
            "agent_name": agent_name,
            "payload": payload or {},
        })

    async def _make_progress_callback(self, job_id: str):
        async def callback(agent_name: str, pct: int, message: str):
            await self._emit(job_id, "agent_progress", agent_name, {
                "progress_pct": pct,
                "message": message,
            })
        return callback

    async def run_analysis(self, job_id: str, ticker: str, db_session) -> None:
        """Main entry point. Called as a FastAPI background task."""
        from app.models.analysis import AnalysisJob, AnalysisResult
        from app.models.evidence import EvidenceItem
        from app.ingestion.ticker_resolver import resolve_ticker
        from sqlalchemy import select

        # ── Resolve ticker to yfinance format and detect market ───────────────
        try:
            ticker_info = resolve_ticker(ticker)
        except ValueError:
            ticker_info = {
                "yf_ticker": ticker, "display": ticker, "market": "unknown",
                "currency": "$", "currency_code": "USD",
                "exchange": "Unknown", "trading_hours": "Unknown",
                "market_name_cn": "未知市场",
            }
        yf_ticker = ticker_info["yf_ticker"]
        market = ticker_info["market"]

        citations = CitationMapper()
        progress_cb = await self._make_progress_callback(job_id)

        try:
            # Update job status to running
            await self._update_job_status(db_session, job_id, "running")
            await self._emit(job_id, "phase_start", payload={
                "phase": "ingestion",
                "message": f"开始采集数据 [{ticker_info['market_name_cn']}] {yf_ticker}...",
            })

            # ── Phase 1: Parallel Data Ingestion ──────────────────────────────
            logger.info(f"[{yf_ticker}] Phase 1: Data Ingestion (market={market})")
            context = await self._phase1_ingest(yf_ticker, job_id, market=market)
            # Embed market metadata into context for all downstream agents
            context.update({
                "yf_ticker": yf_ticker,
                "display_ticker": ticker_info["display"],
                "market": market,
                "currency": ticker_info["currency"],
                "currency_code": ticker_info["currency_code"],
                "market_name_cn": ticker_info["market_name_cn"],
                "exchange": ticker_info["exchange"],
            })

            # ── Phase 2: Index & Feature Extraction ───────────────────────────
            logger.info(f"[{yf_ticker}] Phase 2: Index & Feature Extraction")
            await self._emit(job_id, "phase_start", payload={"phase": "indexing", "message": "索引数据..."})
            context = await self._phase2_index(yf_ticker, context)

            # ── Phase 3: Agent Waves ───────────────────────────────────────────
            logger.info(f"[{ticker}] Phase 3: Agent Waves")
            await self._emit(job_id, "phase_start", payload={"phase": "analysis", "message": "Running specialist agents..."})
            agent_outputs = await self._phase3_run_agents(ticker, job_id, context, citations, progress_cb)
            context.update(agent_outputs)

            # ── Phase 4: Synthesis ─────────────────────────────────────────────
            logger.info(f"[{ticker}] Phase 4: Synthesis")
            await self._emit(job_id, "phase_start", payload={"phase": "synthesis", "message": "Writing investment memo..."})
            thesis = agent_outputs.get("thesis", {})
            scorecard = thesis.get("scorecard", {})
            decision = thesis.get("decision", "Watch")
            memo_md = thesis.get("investment_memo_md", "")

            # Add evidence pack appendix to memo
            evidence_appendix = citations.to_markdown()
            full_memo = memo_md + "\n\n" + evidence_appendix

            # Persist result
            result = AnalysisResult(
                job_id=job_id,
                industry_analysis=agent_outputs.get("industry_analysis"),
                business_model=agent_outputs.get("business_model"),
                moat_score=agent_outputs.get("moat_score"),
                financial_quality=agent_outputs.get("financial_quality"),
                management_assessment=agent_outputs.get("management_assessment"),
                valuation=agent_outputs.get("valuation"),
                risk_assessment=agent_outputs.get("risk_assessment"),
                thesis=thesis,
                monitoring_setup=agent_outputs.get("monitoring_setup"),
                scorecard=scorecard,
                decision=decision,
                decision_rationale=thesis.get("decision_rationale", ""),
                investment_memo_md=full_memo,
                dcf_assumptions=agent_outputs.get("valuation", {}).get("scenario_outputs"),
                scenario_outputs=agent_outputs.get("valuation", {}).get("scenario_outputs"),
            )
            db_session.add(result)

            # Persist evidence items
            for entry in citations.get_all():
                ev = EvidenceItem(
                    job_id=job_id,
                    agent_name=entry.agent_name,
                    source_type=entry.source_type,
                    source_label=entry.source_label,
                    excerpt=entry.excerpt,
                    source_url=entry.source_url,
                    citation_key=entry.key,
                    data_snapshot=entry.data_snapshot if entry.data_snapshot else None,
                )
                db_session.add(ev)

            await self._update_job_status(db_session, job_id, "complete")
            await db_session.commit()

            await self._emit(job_id, "complete", payload={
                "decision": decision,
                "scorecard": scorecard,
                "decision_rationale": thesis.get("decision_rationale", ""),
                "memo_length": len(full_memo),
            })
            logger.info(f"[{ticker}] Analysis complete. Decision: {decision}")

        except Exception as e:
            logger.error(f"[{ticker}] Analysis failed: {e}", exc_info=True)
            await self._update_job_status(db_session, job_id, "failed", str(e))
            try:
                await db_session.commit()
            except Exception:
                pass
            await self._emit(job_id, "error", payload={"message": str(e)})

    async def _phase1_ingest(self, ticker: str, job_id: str, market: str = "unknown") -> dict:
        """Parallel data ingestion from all sources."""
        context = {"ticker": ticker}

        async def fetch_market():
            try:
                df = await asyncio.to_thread(self.market_data.fetch_ohlcv, ticker)
                self.object_store.save(ticker, "market_data", df.to_dict() if not df.empty else {})
                return df
            except Exception as e:
                logger.warning(f"market_data failed: {e}")
                return None

        async def fetch_company():
            try:
                info = await asyncio.to_thread(self.company_info.fetch_company_profile, ticker)
                text = await asyncio.to_thread(self.company_info.to_text_summary, ticker)
                self.object_store.save(ticker, "company_info", {"info": info, "text": text})
                return info, text
            except Exception as e:
                logger.warning(f"company_info failed: {e}")
                return {}, ""

        async def fetch_fin():
            timeout = settings.ingestion_fetch_timeout_seconds

            async def timed_fetch(label: str, fn):
                start = time.perf_counter()
                try:
                    result = await asyncio.wait_for(asyncio.to_thread(fn, ticker), timeout=timeout)
                    logger.info("[%s] financials.%s fetched in %.2fs", ticker, label, time.perf_counter() - start)
                    return result
                except asyncio.TimeoutError:
                    logger.warning("[%s] financials.%s timed out after %ss", ticker, label, timeout)
                    return None
                except Exception as e:
                    logger.warning("[%s] financials.%s failed: %s", ticker, label, e)
                    return None

            income, balance, cashflow = await asyncio.gather(
                timed_fetch("income", self.financials.fetch_income_statement),
                timed_fetch("balance", self.financials.fetch_balance_sheet),
                timed_fetch("cashflow", self.financials.fetch_cash_flow),
            )

            try:
                text = await asyncio.wait_for(
                    asyncio.to_thread(self.financials.to_text_summary, ticker),
                    timeout=timeout,
                )
                self.object_store.save(ticker, "financials_text", text)
            except Exception as e:
                logger.warning("[%s] financials.text failed: %s", ticker, e)
                text = ""

            return income, balance, cashflow, text

        async def fetch_news():
            try:
                text = await asyncio.to_thread(self.news.to_text_summary, ticker, 15, market)
                self.object_store.save(ticker, "news", text)
                return text
            except Exception as e:
                logger.warning(f"news failed: {e}")
                return ""

        async def fetch_earnings():
            try:
                text = await asyncio.to_thread(self.earnings.to_text_summary, ticker, market)
                self.object_store.save(ticker, "earnings", text)
                return text
            except Exception as e:
                logger.warning(f"earnings failed: {e}")
                return ""

        async def fetch_macro():
            try:
                text = await asyncio.to_thread(self.macro.to_text_summary, market)
                return text
            except Exception as e:
                logger.warning(f"macro failed: {e}")
                return ""

        # Run all ingestion in parallel
        results = await asyncio.gather(
            fetch_market(),
            fetch_company(),
            fetch_fin(),
            fetch_news(),
            fetch_earnings(),
            fetch_macro(),
            return_exceptions=True,
        )

        ohlcv_df = results[0] if not isinstance(results[0], Exception) else None
        company_result = results[1] if not isinstance(results[1], Exception) else ({}, "")
        fin_result = results[2] if not isinstance(results[2], Exception) else (None, None, None, "")
        news_text = results[3] if not isinstance(results[3], Exception) else ""
        earnings_text = results[4] if not isinstance(results[4], Exception) else ""
        macro_text = results[5] if not isinstance(results[5], Exception) else ""

        company_info, company_text = company_result if isinstance(company_result, tuple) else ({}, "")
        income_df, balance_df, cashflow_df, financials_text = fin_result if isinstance(fin_result, tuple) else (None, None, None, "")

        context.update({
            "ohlcv_df": ohlcv_df,
            "company_info": company_info,
            "company_text": company_text,
            "company_name": company_info.get("longName") or company_info.get("shortName") or ticker,
            "income_df": income_df,
            "balance_df": balance_df,
            "cashflow_df": cashflow_df,
            "financials_text": financials_text,
            "news_text": news_text,
            "earnings_text": earnings_text,
            "macro_text": macro_text,
        })
        return context

    async def _phase2_index(self, ticker: str, context: dict) -> dict:
        """Index text data into ChromaDB and compute features."""
        col = f"{ticker.lower()}_general"

        # Chunk and index text documents
        texts_to_index = [
            (context.get("company_text", ""), "company_info", f"{ticker} Company Profile"),
            (context.get("financials_text", ""), "filing", f"{ticker} Financial Statements"),
            (context.get("news_text", ""), "news", f"{ticker} News"),
            (context.get("earnings_text", ""), "earnings_call", f"{ticker} SEC Filings"),
        ]

        all_docs, all_metas, all_ids = [], [], []
        for text, source_type, label in texts_to_index:
            if text and len(text) > 100:
                chunks = chunk_text(text, chunk_size=800, overlap=100)
                ids = generate_chunk_ids(ticker, source_type, chunks)
                metas = generate_chunk_metadatas(ticker, source_type, label, chunks_count=len(chunks))
                all_docs.extend(chunks)
                all_metas.extend(metas)
                all_ids.extend(ids)

        if all_docs:
            await asyncio.to_thread(
                self.vector_store.upsert_documents,
                col, all_docs, all_metas, all_ids
            )

        # Build knowledge graph from company info
        info = context.get("company_info", {})
        if info.get("shortName"):
            self.kg.add_company(
                ticker=ticker,
                name=info.get("longName") or ticker,
                sector=info.get("sector") or "",
                industry=info.get("industry") or "",
            )
        context["kg_text"] = self.kg.to_text_summary(ticker)

        # Compute financial features
        income_df = context.get("income_df")
        balance_df = context.get("balance_df")
        cashflow_df = context.get("cashflow_df")
        features = {}
        if income_df is not None:
            features = await asyncio.to_thread(
                self.feature_store.compute_and_save,
                ticker, income_df, balance_df, cashflow_df
            )
        context["features"] = features

        # Compute price features
        ohlcv_df = context.get("ohlcv_df")
        price_features = {}
        if ohlcv_df is not None and not ohlcv_df.empty:
            price_features = self.ts_analyzer.compute_price_features(ticker, ohlcv_df)
        context["price_features"] = price_features
        context["current_price"] = price_features.get("current_price", 0)

        return context

    async def _phase3_run_agents(
        self, ticker: str, job_id: str, context: dict,
        citations: CitationMapper, progress_cb
    ) -> dict:
        """Execute agents in dependency waves."""
        outputs = {}

        def make_agent(AgentClass):
            return AgentClass(
                job_id=job_id,
                ticker=ticker,
                citation_mapper=citations,
                vector_store=self.vector_store,
                progress_callback=progress_cb,
            )

        # Wave 1: Independent agents (parallel)
        wave1_agents = [
            ("industry_analysis", make_agent(IndustryAgent)),
            ("financial_quality", make_agent(FinancialQualityAgent)),
            ("management_assessment", make_agent(ManagementAgent)),
        ]

        for name, agent in wave1_agents:
            await self._emit(job_id, "agent_start", agent.agent_name, {
                "display_name": AGENT_DISPLAY_NAMES.get(agent.agent_name, agent.agent_name)
            })

        wave1_results = await asyncio.gather(
            *[agent.safe_run(context) for _, agent in wave1_agents],
            return_exceptions=True,
        )

        for (name, agent), result in zip(wave1_agents, wave1_results):
            if isinstance(result, Exception):
                result = {"error": str(result)}
            outputs[name] = result
            context[name] = result
            await self._emit(job_id, "agent_complete", agent.agent_name, {
                "result_summary": str(result)[:200],
            })

        # Wave 2: Depends on Wave 1 (parallel)
        wave2_ctx = {**context, **outputs}
        wave2_agents = [
            ("business_model", make_agent(BusinessModelAgent)),
            ("moat_score", make_agent(MoatAgent)),
        ]

        for name, agent in wave2_agents:
            await self._emit(job_id, "agent_start", agent.agent_name, {
                "display_name": AGENT_DISPLAY_NAMES.get(agent.agent_name, agent.agent_name)
            })

        wave2_results = await asyncio.gather(
            *[agent.safe_run(wave2_ctx) for _, agent in wave2_agents],
            return_exceptions=True,
        )

        for (name, agent), result in zip(wave2_agents, wave2_results):
            if isinstance(result, Exception):
                result = {"error": str(result)}
            outputs[name] = result
            wave2_ctx[name] = result
            await self._emit(job_id, "agent_complete", agent.agent_name, {"result_summary": str(result)[:200]})

        # Wave 3: Depends on Wave 2 (parallel)
        wave3_ctx = {**wave2_ctx}
        wave3_agents = [
            ("valuation", make_agent(ValuationAgent)),
            ("risk_assessment", make_agent(RiskAgent)),
        ]

        for name, agent in wave3_agents:
            await self._emit(job_id, "agent_start", agent.agent_name, {
                "display_name": AGENT_DISPLAY_NAMES.get(agent.agent_name, agent.agent_name)
            })

        wave3_results = await asyncio.gather(
            *[agent.safe_run(wave3_ctx) for _, agent in wave3_agents],
            return_exceptions=True,
        )

        for (name, agent), result in zip(wave3_agents, wave3_results):
            if isinstance(result, Exception):
                result = {"error": str(result)}
            outputs[name] = result
            wave3_ctx[name] = result
            await self._emit(job_id, "agent_complete", agent.agent_name, {"result_summary": str(result)[:200]})

        # Wave 4: Synthesis (sequential)
        wave4_ctx = {**wave3_ctx}
        thesis_agent = make_agent(ThesisAgent)
        monitoring_agent = make_agent(MonitoringAgent)

        await self._emit(job_id, "agent_start", "ThesisAgent", {
            "display_name": AGENT_DISPLAY_NAMES["ThesisAgent"]
        })
        thesis = await thesis_agent.safe_run(wave4_ctx)
        if isinstance(thesis, Exception):
            thesis = {"error": str(thesis)}
        outputs["thesis"] = thesis
        wave4_ctx["thesis"] = thesis
        await self._emit(job_id, "agent_complete", "ThesisAgent", {"decision": thesis.get("decision", "Watch")})

        await self._emit(job_id, "agent_start", "MonitoringAgent", {
            "display_name": AGENT_DISPLAY_NAMES["MonitoringAgent"]
        })
        monitoring = await monitoring_agent.safe_run(wave4_ctx)
        if isinstance(monitoring, Exception):
            monitoring = {"error": str(monitoring)}
        outputs["monitoring_setup"] = monitoring
        await self._emit(job_id, "agent_complete", "MonitoringAgent", {})

        return outputs

    async def _update_job_status(
        self, db_session, job_id: str, status: str, error: str = None
    ) -> None:
        from app.models.analysis import AnalysisJob
        from sqlalchemy import select
        stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
        result = await db_session.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            job.status = status
            if status == "complete":
                job.completed_at = datetime.utcnow()
            if error:
                job.error_message = error
            await db_session.flush()


orchestrator = AgentOrchestrator()
