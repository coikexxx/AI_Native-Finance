# AI Native Finance

AI Native Finance 是一个「前后端分离」的 AI 股票研究平台：
- **Backend**：FastAPI + 多 Agent 编排 + SSE 实时进度。
- **Frontend**：React + Vite + Zustand，看板化展示分析过程和结果。

---

## 1. 功能概览

- 股票分析任务创建与历史查询。
- SSE 实时流：阶段进度、Agent 进度、任务完成/失败。
- 投资备忘录、评分卡、证据包展示。
- 预警（Alerts）与预警通知流。
- 自选股（Watchlist）管理。

---

## 2. 目录结构

```text
AI_Native-Finance/
├── backend/                 # FastAPI 服务
│   ├── app/
│   │   ├── api/routes/      # analysis / alerts / watchlist 路由
│   │   ├── core/            # 编排器、SSE 管理
│   │   ├── agents/          # 9个研究 Agent
│   │   ├── storage/         # object/vector/feature store
│   │   └── main.py          # 应用入口
│   └── requirements.txt
└── frontend/                # React + Vite 前端
    ├── src/
    └── package.json
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
curl -X POST http://localhost:8000/api/v1/analysis \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"AAPL"}'
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

### 6.4 查询分析历史

```bash
curl 'http://localhost:8000/api/v1/analysis/history?limit=20'
```

---

## 7. 预警与自选股接口（简表）

### Alerts
- `GET /api/v1/alerts`
- `POST /api/v1/alerts`
- `PUT /api/v1/alerts/{alert_id}`
- `DELETE /api/v1/alerts/{alert_id}`
- `GET /api/v1/alerts/{alert_id}/history`
- `GET /api/v1/alerts/stream`（SSE）

### Watchlist
- `GET /api/v1/watchlist`
- `POST /api/v1/watchlist`
- `DELETE /api/v1/watchlist/{ticker}`

---

## 8. 常见问题排查

### 8.1 前端无法请求后端
1. 确认后端在 `:8000` 正常启动。
2. 确认前端是通过 `npm run dev` 启动（带代理）。
3. 检查浏览器控制台与后端日志。

### 8.2 无法生成分析结果
1. 检查 `anthropic_api_key` 是否正确。
2. 检查外网访问能力（行情/新闻/LLM）。
3. 查看后端日志中对应 job_id 的报错。

### 8.3 SSE 中断
1. 确认请求没有被反向代理缓冲（Nginx 需关闭 buffering）。
2. 长连接场景可关注心跳包是否正常返回。

---

## 9. Git 推送与 PR（你本机）

```bash
git remote -v
git branch --show-current
git push -u origin <your-branch>
```

GitHub 上创建 PR：

```text
https://github.com/<owner>/<repo>/compare/main...<your-branch>
```

---

## 10. 生产部署建议（简版）

- 后端使用 `uvicorn/gunicorn` + 进程管理（systemd/supervisor）。
- 前端静态资源由 Nginx 托管。
- 为 SQLite 数据目录做持久化备份；并考虑未来迁移到 Postgres。
- 对外 API 增加鉴权、限流、日志与告警。

