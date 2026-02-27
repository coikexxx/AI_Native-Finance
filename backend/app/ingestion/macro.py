"""Macroeconomic data ingestion via FRED API — market-aware."""
import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Global / US macro indicators (background context for all markets)
_GLOBAL_SERIES = {
    "FEDFUNDS": "美联储基准利率 Federal Funds Rate (%)",
    "CPIAUCSL": "美国CPI通胀 US CPI",
    "T10Y2Y":   "美国国债收益率曲线 10Y-2Y Treasury Spread",
    "VIXCLS":   "VIX恐慌指数 CBOE Volatility Index",
    "DGS10":    "美国10年期国债收益率 10-Year Treasury Rate",
}

# A-share / HK extra indicators
_CHINA_SERIES = {
    "DEXCHUS": "美元兑人民币汇率 USD/CNY Exchange Rate",
    "GDP":     "美国GDP（全球背景参考）US GDP",
    "SP500":   "标普500指数（全球风险参考）S&P 500",
}

# BTC / crypto: use global indicators + note
_CRYPTO_NOTE = (
    "\n## 加密货币宏观背景\n"
    "BTC价格受全球宏观环境影响（美联储利率政策、美元强弱、风险偏好）。"
    "主要关注：美元指数（DXY）、美联储利率政策周期、机构资金流向（ETF净申购/赎回）。"
)


class MacroFetcher:
    def fetch_series(self, series_id: str, limit: int = 4) -> list:
        """Fetch recent observations for a FRED series."""
        if not settings.fred_api_key:
            return []
        try:
            params = {
                "series_id": series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": limit,
            }
            with httpx.Client(timeout=10) as client:
                resp = client.get(FRED_BASE, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("observations", [])
        except Exception as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}")
            return []

    def _format_series(self, series_dict: dict) -> list[str]:
        lines = []
        for series_id, label in series_dict.items():
            obs = self.fetch_series(series_id, limit=4)
            if obs:
                latest = [o for o in obs if o.get("value") != "."]
                if latest:
                    val = latest[0]["value"]
                    date = latest[0]["date"]
                    lines.append(f"- **{label}** ({series_id}): {val}（截至 {date}）")
        return lines

    def to_text_summary(self, market: str = "unknown") -> str:
        """Return market-aware macro context for LLM."""
        if not settings.fred_api_key:
            return "宏观数据不可用（未配置 FRED_API_KEY）"

        lines = []

        if market == "a_share":
            lines.append("# 宏观经济背景（A股视角）\n")
            lines.append("## 人民币汇率 & 中国宏观")
            lines.extend(self._format_series(_CHINA_SERIES))
            lines.append("\n## 全球宏观参考")
            lines.extend(self._format_series(_GLOBAL_SERIES))
            lines.append(
                "\n**A股特别关注**：央行（PBOC）货币政策方向、"
                "政府财政刺激政策、房地产行业风险传导、北向资金（沪深港通）净流入。"
            )

        elif market == "hk":
            lines.append("# 宏观经济背景（港股视角）\n")
            lines.append("## 汇率 & 联系汇率制度")
            lines.extend(self._format_series(_CHINA_SERIES))
            lines.append("\n## 全球宏观参考")
            lines.extend(self._format_series(_GLOBAL_SERIES))
            lines.append(
                "\n**港股特别关注**：港元联系汇率制度（7.75–7.85 HKD/USD）、"
                "美联储加息对港元流动性影响、南向资金（港股通）净流入、"
                "中国内地经济政策对港股的传导。"
            )

        elif market == "crypto":
            lines.append("# 宏观经济背景（加密货币视角）\n")
            lines.append("## 全球流动性 & 风险偏好")
            lines.extend(self._format_series(_GLOBAL_SERIES))
            lines.append(_CRYPTO_NOTE)

        else:
            lines.append("# 宏观经济背景（FRED数据）\n")
            all_series = {**_GLOBAL_SERIES, **_CHINA_SERIES}
            lines.extend(self._format_series(all_series))

        return "\n".join(lines)


macro_fetcher = MacroFetcher()
