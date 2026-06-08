# Agent Project - 模拟面试助手

基于 React + FastAPI + LangChain + RAG + DeepSeek 的模拟面试助手。

## 开发模式

- 本机运行：React 前端、FastAPI 后端。
- Docker 运行：PostgreSQL、Redis、Qdrant、MinIO。
- DeepSeek API Key / Base URL：通过前端“模型配置”页面输入，不写死在代码里。

## 目录

```text
.
├── backend/                # FastAPI 服务
├── frontend/               # React + Vite 前端
├── docker/docker-compose.yml # 本地依赖服务
├── docker/.env.example     # Docker Compose 环境变量模板
├── backend/.env.example    # 后端环境变量模板
└── frontend/.env.example   # 前端环境变量模板
```

## 前置依赖

- Docker Desktop 或兼容 Docker Compose 的运行环境
- Python 3.11
- Node.js 20+

## 快速启动

### 1. 准备环境变量

```bash
cp docker/.env.example docker/.env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

默认配置可直接用于本机开发。如需改端口或账号密码，优先改 `docker/.env` 与 `backend/.env`，并保持两边连接信息一致。

### 2. 启动 Docker 依赖

```bash
cd docker
docker compose up -d
```

依赖服务默认地址：

| 服务 | 地址 | 说明 |
| --- | --- | --- |
| PostgreSQL | `localhost:5432` | DB：`interview_assistant`，用户：`interview` |
| Redis | `localhost:6379` | 默认 DB：`0` |
| Qdrant | `http://localhost:6333` | 向量数据库 HTTP API |
| MinIO API | `http://localhost:9000` | S3 兼容 API |
| MinIO Console | `http://localhost:9001` | 用户/密码默认 `minioadmin` / `minioadmin` |

查看状态：

```bash
cd docker
docker compose ps
```

停止依赖：

```bash
cd docker
docker compose down
```

如需删除本地数据卷：

```bash
cd docker
docker compose down -v
```

### 3. 启动后端

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

后端地址：`http://localhost:8000`。

### 4. 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

前端地址：`http://localhost:5173`。

## RAG 与向量库

后端默认启用生产化 RAG 路径：

- 文档解析：`.txt` / `.md` 直接解析，`.pdf` 使用 `pypdf`，`.docx` 使用 `python-docx`。
- 向量模型：默认使用 `fastembed` 的 `intfloat/multilingual-e5-small`，更适合中英文简历、JD 和项目材料检索。
- 向量存储：默认使用 Qdrant 本地持久化路径 `backend/runtime/qdrant`，数据不会因为后端进程重启丢失。
- 外部 Qdrant：如需连接 Docker Qdrant 服务，设置 `QDRANT_PATH=` 为空，并配置 `QDRANT_URL=http://localhost:6333`。

首次启动会下载 embedding 模型，耗时取决于网络。若模型或 Qdrant 初始化失败，开发模式会自动降级到 hashing embedding / 内存向量库；生产环境可把 `RAG_ALLOW_HASHING_FALLBACK=false`、`RAG_ALLOW_MEMORY_FALLBACK=false` 改为失败即报错。

## 模型配置

进入前端页面的“模型配置”区域，输入：

- DeepSeek API Key
- DeepSeek Base URL，例如 `https://api.deepseek.com`
- Chat Model，例如 `deepseek-chat`
- Reasoner Model，例如 `deepseek-reasoner`

后端会把配置保存到本地 `backend/runtime/model_config.json`。该目录已加入 `.gitignore`。

## 常见问题

- `docker compose up -d` 端口冲突：检查 `docker/.env` 中的 `POSTGRES_PORT`、`REDIS_PORT`、`QDRANT_HTTP_PORT`、`MINIO_API_PORT`、`MINIO_CONSOLE_PORT` 是否被本机其他服务占用。
- 后端连不上数据库：确认 `docker compose ps` 中 PostgreSQL 为 healthy，并检查 `backend/.env` 的 `DATABASE_URL` 是否匹配 `docker/.env` 中的账号、密码和端口。
- 前端请求后端失败：确认 `frontend/.env` 的 `VITE_API_BASE_URL` 指向 `http://localhost:8000`，并重启 Vite 开发服务。
