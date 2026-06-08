# 模拟面试助手执行计划

> 目标路径：`/Users/abner/projects/study/agent-project`
>
> 项目策略：App 本机跑，依赖 Docker 跑。
>
> 执行建议：拆成多个 agent 并行实现，主控 agent 负责接口契约、架构边界和集成验收。

## 1. 方案判断

这个项目不是一个简单聊天机器人，而是一个有明确业务闭环的 AI 应用：

1. 用户上传简历、JD、题库等资料。
2. 后端解析资料并构建 RAG 知识库。
3. 面试编排器根据阶段、难度、岗位和资料召回上下文。
4. LangChain 负责 Prompt、Retriever、Chain、结构化输出编排。
5. DeepSeek 负责生成问题、追问、评价和报告。
6. React 前端以对话式 UI 承载体验。

关键设计原则：

- 业务状态由后端控制，不交给 LLM 自由发挥。
- RAG 负责事实依据，LLM 负责表达和推理。
- LangChain 是应用编排层，不是业务状态层。
- DeepSeek API 远程调用，不需要本地部署模型。
- 开发期不要把前后端也塞进 Docker，避免热更新慢和调试复杂。

## 2. 开发环境方案

### 本机运行

- React 18.3.1
- Vite 6.x
- TypeScript 5.7+
- Python 3.11.x
- FastAPI 0.115.x
- LangChain 0.3.x
- Uvicorn 0.34.x

### Docker 运行依赖

- PostgreSQL 16
- Redis 7
- Qdrant 1.13.x
- MinIO latest，可选

### 本机已知状态

当前机器：

- macOS 26.5
- arm64
- Node v22.22.0
- npm 10.9.4
- Python 3.9.6，建议安装 Python 3.11
- Docker 当前不可用，需要安装 Docker Desktop

建议补装：

```bash
brew install python@3.11
brew install --cask docker
```

## 3. 推荐仓库结构

```text
agent-project/
  frontend/
    package.json
    src/
      pages/
      components/
      api/
      stores/
      types/

  backend/
    pyproject.toml
    .env.example
    app/
      main.py
      api/
        documents.py
        interviews.py
        reports.py
      core/
        config.py
        logging.py
      db/
        session.py
        migrations/
      models/
        document.py
        interview.py
        message.py
        report.py
      services/
        document_service.py
        rag_service.py
        interview_orchestrator.py
        evaluation_service.py
        deepseek_service.py
      chains/
        question_chain.py
        answer_review_chain.py
        followup_chain.py
        report_chain.py
      prompts/
        interviewer.py
        reviewer.py
        report.py

  docker/
    docker-compose.yml

  docs/
    architecture.md
    api.md
    acceptance.md

  interview-assistant-technical-proposal.html
  interview-assistant-execution-plan.md
```

## 4. 多 Agent 拆分策略

根据 `dispatching-parallel-agents` 的原则，只有边界独立、文件冲突少、可以并行推进的任务才拆 agent。这个项目适合拆成以下角色。

### 主控 Agent：架构与集成

职责：

- 定义目录结构。
- 定义 API 契约。
- 定义数据模型字段。
- 合并各 agent 输出。
- 运行最终验证。
- 控制不要过度设计。

产出：

- `docs/architecture.md`
- `docs/api.md`
- 集成后的可运行项目

### Agent A：前端对话体验

职责：

- 初始化 React + Vite + TypeScript。
- 实现面试配置页。
- 实现资料上传页。
- 实现聊天面试页。
- 实现 SSE 流式输出渲染。
- 实现报告页。

主要文件：

- `frontend/src/pages/*`
- `frontend/src/components/*`
- `frontend/src/api/*`
- `frontend/src/stores/*`

验收：

- `npm run dev` 可启动。
- 可以创建面试。
- 可以发送回答并展示 AI 流式内容。
- 可以查看报告。

### Agent B：后端 API 与数据模型

职责：

- 初始化 FastAPI。
- 配置 SQLAlchemy / Alembic。
- 建立 documents、interviews、messages、reports 表。
- 实现文档上传接口。
- 实现面试创建接口。
- 实现消息发送接口。
- 实现报告查询接口。

主要文件：

- `backend/app/main.py`
- `backend/app/api/*.py`
- `backend/app/models/*.py`
- `backend/app/db/*.py`

验收：

- `uvicorn app.main:app --reload --port 8000` 可启动。
- `/docs` 可以打开。
- 核心 API 可通过 curl 调通。

### Agent C：RAG 知识库

职责：

- 文档解析。
- 文本清洗。
- chunk 切分。
- metadata 设计。
- embedding 接入。
- Qdrant 写入和检索。
- Retriever 封装。

主要文件：

- `backend/app/services/document_service.py`
- `backend/app/services/rag_service.py`

验收：

- 上传文档后可写入 Qdrant。
- 输入查询后能召回相关 chunk。
- 支持按 `document_type`、`user_id`、`interview_id` 过滤。

### Agent D：LangChain + DeepSeek 应用层

职责：

- DeepSeek OpenAI-compatible client 封装。
- QuestionChain。
- FollowupChain。
- AnswerReviewChain。
- ReportChain。
- JSON 结构化输出校验。

主要文件：

- `backend/app/services/deepseek_service.py`
- `backend/app/chains/*.py`
- `backend/app/prompts/*.py`

验收：

- 可以生成单个面试问题。
- 可以评价用户回答。
- 可以根据不足生成追问。
- 可以生成结构化报告 JSON。

### Agent E：DevOps 与本地依赖

职责：

- 编写 Docker Compose。
- 编写 `.env.example`。
- 编写启动脚本。
- 编写 README 本地开发步骤。

主要文件：

- `docker/docker-compose.yml`
- `backend/.env.example`
- `frontend/.env.example`
- `README.md`

验收：

- `docker compose up -d` 可启动依赖。
- PostgreSQL、Redis、Qdrant 端口可访问。
- README 可以让新人按步骤启动项目。

### Agent F：测试与验收

职责：

- 后端 API 测试。
- RAG 检索测试。
- Chain 输出结构测试。
- 前端手工验收清单。
- MVP 端到端验收脚本。

主要文件：

- `backend/tests/*`
- `docs/acceptance.md`

验收：

- 后端测试可跑通。
- 明确 MVP 验收路径：上传资料 → 创建面试 → 回答问题 → 生成报告。

## 5. 推荐并行执行顺序

### Wave 1：基础骨架

并行：

- Agent A：初始化前端。
- Agent B：初始化后端和基础 API。
- Agent E：初始化 Docker Compose 和环境变量。

主控 Agent 同时定义：

- API 字段。
- 数据模型。
- 项目目录。

### Wave 2：AI 能力

并行：

- Agent C：实现 RAG。
- Agent D：实现 LangChain + DeepSeek。
- Agent A：根据 API mock 完成页面交互。

主控 Agent 负责对齐：

- RAG 返回格式。
- Chain 输入输出格式。
- 前后端消息协议。

### Wave 3：业务闭环

并行：

- Agent B：实现面试状态机。
- Agent D：接入提问、追问、评价、报告链。
- Agent F：补测试和验收清单。

主控 Agent 负责集成：

- 完整跑通一场面试。
- 修接口不一致。
- 补 README。

## 6. MVP 验收标准

第一版只要满足下面闭环即可：

1. 用户能上传一份简历和一份 JD。
2. 后端能解析并写入 Qdrant。
3. 用户能创建一场模拟面试。
4. AI 能基于简历/JD 提一个问题。
5. 用户回答后，AI 能给出评分和追问。
6. 用户结束面试后，系统能生成报告。
7. 前端能完整展示整个流程。

## 7. 风险点与规避

### 风险 1：LLM 输出不稳定

规避：

- 所有评价类输出要求 JSON。
- 使用 Pydantic 校验。
- 校验失败时自动 retry。

### 风险 2：RAG 召回不准

规避：

- chunk metadata 必须包含 document_type、section、tags。
- 面试阶段限制检索 scope。
- 后续接 reranker。

### 风险 3：业务流程被模型带偏

规避：

- 后端维护面试状态机。
- LLM 只生成当前阶段内容。
- 每轮只允许输出一个问题或一个评价对象。

### 风险 4：开发环境复杂

规避：

- 前后端本机跑。
- Docker 只跑基础依赖。
- MVP 可先不启 Redis / MinIO。

## 8. 第一批具体任务

1. 创建 `frontend/` React 项目。
2. 创建 `backend/` FastAPI 项目。
3. 创建 `docker/docker-compose.yml`。
4. 定义 `.env.example`。
5. 定义数据库模型。
6. 实现基础聊天接口。
7. 接 DeepSeek。
8. 实现文档上传和 Qdrant 写入。
9. 实现面试状态机。
10. 实现报告生成。

## 9. 主控 Agent 给子 Agent 的提示模板

```text
你是本项目的子 Agent，负责【模块名】。

项目目标：构建一个 React + FastAPI + LangChain + RAG + DeepSeek 的模拟面试助手。
开发模式：React/FastAPI 本机跑，PostgreSQL/Redis/Qdrant/MinIO 通过 Docker Compose 跑。

你的边界：只修改以下目录/文件：
- xxx

你需要交付：
- xxx

必须遵守：
- 不要改其他 Agent 的文件。
- 不要引入超出 MVP 的复杂功能。
- 所有配置走环境变量。
- 输出完成后说明修改文件、运行命令、验收方式。
```

## 10. 结论

建议先按多 agent 并行方式推进 MVP：

- 主控 agent 负责架构和集成。
- 前端、后端、RAG、LangChain、DevOps、测试分别拆 agent。
- 每个 agent 只处理边界清晰的模块。
- 第一阶段不做语音、视频、多面试官和企业后台。

优先跑通主链路，再做体验增强。
