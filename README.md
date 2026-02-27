# AI Native Finance

AI Native Finance 是一个专注于 **A股 / 港股 / BTC** 的 AI 投研平台：
- **Backend**：FastAPI + 多 Agent 编排 + SSE 实时进度。
- **Frontend**：React + Vite + Zustand，看板化展示分析过程和结果。

---

## 1. 功能概览

### 核心分析
- 输入短代码（如 `600519`、`0700`、`BTC`）自动识别市场并分析
- A股：行业研究、财务分析、估值（DCF / 相对估值）、风险矩阵、投资论文
- 港股：与 A股 相同的分析流程，采用港元计价，港股监管框架
- BTC：加密货币专用框架（S2F 模型、NVT 比率、MVRV、减半周期分析，跳过 DCF）
- SSE 实时流：阶段进度、Agent 进度、任务完成/失败

### 股票代码自动解析
| 用户输入 | 解析结果 | 市场 |
|---------|---------|------|
| `600519` | `600519.SS` | A股 上交所 |
| `000858` | `000858.SZ` | A股 深交所 |
| `0700` | `0700.HK` | 港股 |
| `9988` | `9988.HK` | 港股 |
| `BTC` / `bitcoin` | `BTC-USD` | 加密货币 |

### 行情监控板块
- 自选股价格异动监控（阈值 ±2%，每 5 分钟）
- 成交量异常放大监控（≥ 2× 三个月均值）
- 重要新闻/舆情扫描（每 30 分钟），支持中英文关键词
- A股/港股 亚洲市场时段覆盖（北京时间 9:30–16:00）+ BTC 24/7
- 通过 SSE 实时推送价格异动和新闻预警

### 预警与自选股
- 价格突破预警（高于/低于目标价）
- 定期重新分析（日/周/月）
- 自选股管理，一键触发分析

---

## 2. 目录结构

```text
AI_Native-Finance/
├── backend/
│   └── app/
│       ├── api/routes/          # analysis / alerts / watchlist / monitor 路由
│       ├── core/                # 编排器、SSE 管理
│       ├── agents/              # 9个研究 Agent（行业/财务/估值/风险/论文等）
│       ├── alerts/              # 预警调度器、自选股监控
│       ├── ingestion/           # 行情/新闻/宏观/财报数据获取
│       │   ├── ticker_resolver.py   # 股票代码自动解析（核心）
│       │   ├── news.py              # 新浪财经中文新闻 + Yahoo RSS
│       │   ├── macro.py             # 宏观数据（A股含 USD/CNY，BTC 含 VIX）
│       │   └── earnings_calls.py    # 财报披露（CNINFO/HKEX，非 EDGAR）
│       ├── llm/prompts/
│       │   ├── market_context.py    # A股/港股/加密货币市场背景提示词
│       │   └── valuation.py         # 含 BTC 专用估值提示词
│       ├── governance/          # 提示词合规与 ticker 校验
│       └── main.py
└── frontend/
    └── src/
        ├── pages/
        │   ├── MonitorPage.tsx      # 行情监控看板
        │   └── WatchlistPage.tsx    # 自选股管理
        └── components/
            └── research/TickerInput.tsx
```

---

## 3. 运行环境要求

- Python **3.10+**（建议 3.11）
- Node.js **18+**（建议 20）
- npm **9+**

---

## 4. 后端启动

### 4.1 安装依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.2 配置环境变量

`backend/app/config.py` 使用 `.env` 读取配置，最小可用示例：

```bash
cd backend
cat > .env <<'EOF'
anthropic_api_key=YOUR_ANTHROPIC_API_KEY
llm_model=claude-sonnet-4-6
app_host=0.0.0.0
app_port=8000
frontend_url=http://localhost:5173
EOF
```

> 若不配置 `anthropic_api_key`，与 LLM 相关分析能力会受限。

### 4.3 启动服务

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后可访问：
- 健康检查：`http://localhost:8000/health`
- OpenAPI 文档：`http://localhost:8000/docs`

---

## 5. 前端启动

### 5.1 安装依赖

```bash
cd frontend
npm install
```

### 5.2 启动开发服务器

```bash
cd frontend
npm run dev
```

默认地址：`http://localhost:5173`

Vite 已配置 `/api` 代理到 `http://localhost:8000`，本地联调无需额外跨域配置。

---

## 6. 常用操作（开发）

### 6.1 启动一个分析任务

```bash
# A股（茅台）
curl -X POST http://localhost:8000/api/v1/analysis \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"600519"}'

# 港股（腾讯）
curl -X POST http://localhost:8000/api/v1/analysis \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"0700"}'

# 比特币
curl -X POST http://localhost:8000/api/v1/analysis \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"BTC"}'
```

### 6.2 监听分析 SSE 流

将 `{job_id}` 替换为上一步返回值：

```bash
curl -N http://localhost:8000/api/v1/analysis/{job_id}/stream
```

### 6.3 查询分析结果

```bash
curl http://localhost:8000/api/v1/analysis/{job_id}
```

### 6.4 自选股管理

```bash
# 添加（支持短代码，自动解析为完整格式）
curl -X POST http://localhost:8000/api/v1/watchlist \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"600519"}'

# 查询
curl http://localhost:8000/api/v1/watchlist

# 删除
curl -X DELETE http://localhost:8000/api/v1/watchlist/600519.SS
```

---

## 7. API 接口汇总

### 分析
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/analysis` | 创建分析任务 |
| GET | `/api/v1/analysis/{job_id}` | 查询任务状态/结果 |
| GET | `/api/v1/analysis/{job_id}/stream` | SSE 实时进度流 |
| GET | `/api/v1/analysis/history` | 历史任务列表 |

### 预警
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/alerts` | 预警列表 |
| POST | `/api/v1/alerts` | 创建预警 |
| PUT | `/api/v1/alerts/{alert_id}` | 更新预警 |
| DELETE | `/api/v1/alerts/{alert_id}` | 删除预警 |
| GET | `/api/v1/alerts/{alert_id}/history` | 触发历史 |
| GET | `/api/v1/alerts/stream` | SSE 预警推送流 |

### 自选股
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/watchlist` | 自选股列表（含实时价格）|
| POST | `/api/v1/watchlist` | 添加（自动解析短代码）|
| DELETE | `/api/v1/watchlist/{ticker}` | 移除 |

### 行情监控
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/monitor/prices` | 自选股实时行情快照 |
| GET | `/api/v1/monitor/news` | 自选股新闻/舆情聚合 |
| POST | `/api/v1/monitor/check-now` | 手动触发一次异动检测 |

---

## 8. 监控调度说明

行情监控通过 APScheduler 定时运行，覆盖三个市场：

| 作业 | 时间窗口（ET）| 说明 |
|------|-------------|------|
| 价格异动（美股时段）| 周一–五 09:00–16:00 每5分钟 | 保留以兼容 |
| 价格异动（亚洲时段）| 周一–五 21:30–03:00 每5分钟 | A股 9:30–15:00 CST / 港股 9:30–16:00 HKT |
| 价格异动（BTC 补充）| 每天 04:00–08:00 每5分钟 | BTC 24/7 全覆盖 |
| 新闻/舆情扫描 | 每30分钟（全天）| 含中英文关键词 |

触发的异动通过 SSE 实时推送到前端（事件类型：`watchlist_price_anomaly` / `watchlist_news_alert`）。

---

## 9. 常见问题排查

### 9.1 前端无法请求后端
1. 确认后端在 `:8000` 正常启动。
2. 确认前端是通过 `npm run dev` 启动（带代理）。
3. 检查浏览器控制台与后端日志。

### 9.2 无法生成分析结果
1. 检查 `anthropic_api_key` 是否正确配置。
2. 检查外网访问能力（yfinance 行情 / 新浪财经 / LLM API）。
3. 查看后端日志中对应 job_id 的报错。

### 9.3 输入股票代码报错 400
目前仅支持 **A股（沪深）、港股、BTC**，输入其他市场代码（如 `AAPL`）会返回 400。
支持的短代码格式：
- A股沪市：`600519`、`601318`（6 位，6 开头）
- A股深市：`000858`、`300750`（6 位，0/2/3 开头）
- 港股：`0700`、`9988`（2–5 位，自动补零）
- BTC：`BTC`、`btc`、`bitcoin`

### 9.4 SSE 中断
1. 确认请求没有被反向代理缓冲（Nginx 需关闭 buffering）。
2. 长连接场景可关注心跳包是否正常返回。

---

## 10. 生产部署建议

- 后端使用 `uvicorn/gunicorn` + 进程管理（systemd/supervisor）。
- 前端静态资源由 Nginx 托管，注意关闭 SSE 的响应缓冲（`proxy_buffering off`）。
- 为 SQLite 数据目录做持久化备份；并考虑未来迁移到 Postgres。
- 对外 API 增加鉴权、限流、日志与告警。
- 新浪财经新闻抓取建议控制频率，避免 IP 被封禁。
