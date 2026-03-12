# "Jinni 会议精灵" Web 化架构设计

**版本**: 1.0
**日期**: 2026-03-11
**作者**: 架构组
**状态**: 设计草案

---

## 一、系统概述

### 1.1 现状分析

当前 "Jinni 会议精灵" 已实现 CLI 闭环：

```
音视频输入 → Whisper ASR → LLM 增强 → 模板总结 → 文件输出
```

| 能力 | 状态 | 说明 |
|------|------|------|
| ASR 转录 | ✅ | Whisper 本地/云端，支持多种模型 |
| LLM 增强 | ✅ | OpenAI/Anthropic/GLM/DeepSeek |
| 模板总结 | ✅ | 多角色视角 + 自定义模板 |
| CLI 接口 | ✅ | 完整命令行工具 |
| **Web 界面** | ❌ | **待开发** |
| **任务持久化** | ❌ | **待开发** |
| **异步处理** | ❌ | **待开发** |

### 1.2 演进目标

**核心目标**：从单机 CLI 工具演进为 **SaaS 化会议智能处理平台**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Web 化演进路线图                              │
├─────────────────────────────────────────────────────────────────────┤
│  Phase 1 (MVP)         │  Phase 2 (增强)        │  Phase 3 (企业)   │
├────────────────────────┼───────────────────────┼───────────────────┤
│  • FastAPI 后端        │  • WebSocket 推送     │  • 多租户支持     │
│  • Streamlit 前端      │  • 用户认证系统       │  • 权限管理       │
│  • SQLite 持久化       │  • 会议分享链接       │  • API 限流       │
│  • Celery 异步任务     │  • 历史记录搜索      │  • 对象存储       │
│  • Redis 状态缓存      │  • 导出 PDF/Word      │  • 部署容器化     │
└────────────────────────┴───────────────────────┴───────────────────┘
```

### 1.3 架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           前端层 (Frontend)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Streamlit UI    │  │  未来: Vue.js    │  │  未来: Mobile    │          │
│  │  • 文件上传      │  │  • React SPA     │  │  • 小程序        │          │
│  │  • 进度展示      │  │  • 实时推送      │  │  • 响应式        │          │
│  │  • 结果预览      │  │  • 状态管理      │  │                  │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
└───────────┼────────────────────┼─────────────────────┼──────────────────────┘
            │                    │                     │
            ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API 网关层 (FastAPI)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  /upload    │ │  /status    │ │  /meetings  │ │  /templates │          │
│  │  POST       │ │  GET        │ │  GET        │ │  CRUD       │          │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘          │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        业务逻辑层 (Service Layer)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ MeetingService   │  │ TaskService      │  │ TemplateService  │          │
│  │ • 创建会议       │  │ • 任务状态查询   │  │ • 模板管理       │          │
│  │ • 获取结果       │  │ • 任务取消       │  │ • 自定义模板     │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                      │
│  ┌────────▼─────────┐  ┌────────▼─────────┐  ┌────────▼─────────┐          │
│  │ ProcessService   │  │ StorageService   │  │ LLMService       │          │
│  │ • 音视频处理     │  │ • 文件存储       │  │ • Provider 路由  │          │
│  │ • ASR 调用       │  │ • 结果存取       │  │ • 重试/回退      │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Celery Workers  │   │  Storage Layer   │   │  External APIs   │
├──────────────────┤   ├──────────────────┤   ├──────────────────┤
│ • Worker 1-N     │   │ • SQLite/Postgre │   │ • OpenAI API     │
│ • ASR Task       │   │ • Local File/S3  │   │ • Anthropic API  │
│ • LLM Enhance    │   │ • Redis Cache    │   │ • GLM API        │
│ • Summary Task   │   │                  │   │ • DeepSeek API   │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 二、技术栈选型

### 2.1 后端技术栈

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| **Web 框架** | FastAPI | • 异步高性能<br>• 自动 API 文档<br>• 类型安全 (Pydantic)<br>• 与现有 Python 代码无缝集成 |
| **异步任务** | Celery + Redis | • 成熟的分布式任务队列<br>• 支持任务优先级、重试、定时<br>• 实时进度追踪<br>• 与 FastAPI 完美配合 |
| **数据库** | SQLite (MVP) → PostgreSQL (生产) | • MVP: SQLite 零配置<br>• 生产: PostgreSQL 支持并发、JSON、全文搜索 |
| **缓存** | Redis | • 任务状态存储<br>• 会话管理<br>• 速率限制 |
| **文件存储** | 本地文件系统 (MVP) → MinIO/S3 (生产) | • MVP: 本地存储简单<br>• 生产: 对象存储支持大文件、CDN |

### 2.2 前端技术栈

| 方案 | 适用场景 | 技术栈 | 理由 |
|------|----------|--------|------|
| **Phase 1 (MVP)** | 快速原型 | Streamlit | • 纯 Python 开发<br>• 内置文件上传、进度条<br>• 零前端代码<br>• 适合内部工具 |
| **Phase 2** | 正式产品 | Vue.js 3 + TypeScript + Vite | • 组件化开发<br>• 响应式设计<br>• 丰富的 UI 库 (Element Plus)<br>• 与 FastAPI 类型共享 |
| **Phase 3** | 移动端 | Flutter / UniApp | • 跨平台<br>• 原生性能 |

### 2.3 部署技术栈

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| **容器化** | Docker | • 环境一致性<br>• 简化部署 |
| **反向代理** | Nginx | • 静态文件服务<br>• 负载均衡<br>• SSL 终止 |
| **进程管理** | Supervisor / systemd | • 进程守护<br>• 自动重启 |
| **监控** | Prometheus + Grafana | • 指标收集<br>• 可视化监控 |

### 2.4 依赖包清单

```txt
# requirements-web.txt

# Web 框架
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6  # 文件上传

# 异步任务
celery[redis]>=5.3.0
redis>=5.0.0

# 数据库
sqlalchemy>=2.0.0
alembic>=1.12.0          # 数据库迁移
asyncpg>=0.29.0          # PostgreSQL 异步驱动

# 前端 (Phase 1)
streamlit>=1.28.0

# 认证 (Phase 2)
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# 工具
pydantic>=2.4.0
pydantic-settings>=2.1.0

# 现有依赖
openai-whisper>=20230314
openai>=1.0.0
anthropic>=0.18.0
zhipuai>=2.0.0
```

---

## 三、数据库建模

### 3.1 ER 图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据库关系图                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │   users      │         │  meetings    │         │   tasks      │
    ├──────────────┤         ├──────────────┤         ├──────────────┤
    │ id (PK)      │───┐     │ id (PK)      │───┐     │ id (PK)      │
    │ username     │   │     │ user_id (FK) │   │     │ meeting_id   │───┐
    │ email        │   │     │ title        │   │     │ status       │   │
    │ password_hash│   │     │ original_file│   │     │ task_type    │   │
    │ created_at   │   │     │ duration     │   │     │ progress     │   │
    │ updated_at   │   │     │ created_at   │   │     │ result_json  │   │
    └──────────────┘   │     │ updated_at   │   │     │ error_msg    │   │
                       │     └──────────────┘   │     │ started_at   │   │
                       │           │            │     │ completed_at │   │
                       │           │            │     └──────────────┘   │
                       │           │            │                        │
                       │           ▼            ▼                        │
                       │    ┌──────────────┐  ┌──────────────┐          │
                       │    │  transcripts │  │  summaries   │          │
                       │    ├──────────────┤  ├──────────────┤          │
                       │    │ id (PK)      │  │ id (PK)      │          │
                       └────│ meeting_id   │  │ meeting_id   │          │
                            │ raw_text     │  │ template_id  │          │
                            │ enhanced_text│  │ content_json │          │
                            │ language     │  │ llm_provider │          │
                            │ word_count   │  │ llm_model    │          │
                            └──────────────┘  └──────────────┘          │
                                                                  │
                       ┌─────────────────────────────────────────┘
                       │
                       ▼
            ┌──────────────┐
            │  templates   │
            ├──────────────┤
            │ id (PK)      │
            │ user_id (FK) │
            │ name         │
            │ role         │
            │ angle        │
            │ focus (JSON) │
            │ sections(JSON)│
            │ is_public    │
            │ created_at   │
            └──────────────┘
```

### 3.2 表结构定义

#### 3.2.1 users (用户表)

```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    is_admin        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

#### 3.2.2 meetings (会议表)

```sql
CREATE TABLE meetings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    original_file   VARCHAR(500),           -- 原始文件路径
    file_size       BIGINT,                 -- 文件大小 (bytes)
    duration        FLOAT,                  -- 音频时长 (秒)
    language        VARCHAR(10) DEFAULT 'zh',
    status          VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_meetings_user_id ON meetings(user_id);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_created_at ON meetings(created_at DESC);
```

#### 3.2.3 tasks (任务表)

```sql
CREATE TABLE tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id      INTEGER NOT NULL,
    task_type       VARCHAR(50) NOT NULL,   -- asr, enhance, summary
    status          VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    progress        INTEGER DEFAULT 0,       -- 0-100
    result_json     TEXT,                   -- JSON 结果
    error_message   TEXT,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE INDEX idx_tasks_meeting_id ON tasks(meeting_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_task_type ON tasks(task_type);
```

#### 3.2.4 transcripts (转录表)

```sql
CREATE TABLE transcripts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id      INTEGER NOT NULL UNIQUE,
    raw_text        TEXT NOT NULL,
    enhanced_text   TEXT,
    language        VARCHAR(10),
    word_count      INTEGER,
    utterance_count INTEGER,
    metadata_json   TEXT,                   -- 额外元数据
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE INDEX idx_transcripts_meeting_id ON transcripts(meeting_id);
```

#### 3.2.5 summaries (总结表)

```sql
CREATE TABLE summaries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id      INTEGER NOT NULL,
    template_id     INTEGER,
    content_json    TEXT NOT NULL,          -- JSON 结构化内容
    llm_provider    VARCHAR(50),
    llm_model       VARCHAR(100),
    tokens_used     INTEGER,
    processing_time FLOAT,                  -- 处理耗时 (秒)
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES templates(id)
);

CREATE INDEX idx_summaries_meeting_id ON summaries(meeting_id);
CREATE INDEX idx_summaries_template_id ON summaries(template_id);
```

#### 3.2.6 templates (模板表)

```sql
CREATE TABLE templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,                 -- NULL 表示系统模板
    name            VARCHAR(100) NOT NULL,
    role            VARCHAR(50) NOT NULL,
    angle           VARCHAR(50),
    focus           TEXT NOT NULL,           -- JSON 数组
    sections        TEXT NOT NULL,           -- JSON 数组
    is_public       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_templates_user_id ON templates(user_id);
CREATE INDEX idx_templates_is_public ON templates(is_public);
```

### 3.3 SQLAlchemy 模型定义

```python
# models/database.py

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meetings = relationship("Meeting", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    original_file = Column(String(500))
    file_size = Column(Integer)
    duration = Column(Float)
    language = Column(String(10), default="zh")
    status = Column(String(20), default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="meetings")
    tasks = relationship("Task", back_populates="meeting", cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="meeting", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)  # asr, enhance, summary
    status = Column(String(20), default="pending", index=True)
    progress = Column(Integer, default=0)
    result_json = Column(Text)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="tasks")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, unique=True, index=True)
    raw_text = Column(Text, nullable=False)
    enhanced_text = Column(Text)
    language = Column(String(10))
    word_count = Column(Integer)
    utterance_count = Column(Integer)
    metadata_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="transcript")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), index=True)
    content_json = Column(Text, nullable=False)
    llm_provider = Column(String(50))
    llm_model = Column(String(100))
    tokens_used = Column(Integer)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    meeting = relationship("Meeting", back_populates="summaries")
    template = relationship("Template", back_populates="summaries")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    angle = Column(String(50))
    focus = Column(Text, nullable=False)  # JSON
    sections = Column(Text, nullable=False)  # JSON
    is_public = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="templates")
    summaries = relationship("Summary", back_populates="template")
```

---

## 四、核心流程时序图

### 4.1 会议处理主流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           会议处理完整流程                                   │
└─────────────────────────────────────────────────────────────────────────────┘

 用户              前端              API            Celery              外部API
  │                 │                 │               │                  │
  │  上传视频       │                 │               │                  │
  │───────────────>│                 │               │                  │
  │                 │                 │               │                  │
  │                 │  POST /upload   │               │                  │
  │                 │────────────────>│               │                  │
  │                 │                 │               │                  │
  │                 │                 │  创建 Meeting │                  │
  │                 │                 │──────────────>│                  │
  │                 │                 │               │                  │
  │                 │                 │  返回 task_id │                  │
  │                 │<────────────────│               │                  │
  │                 │                 │               │                  │
  │  返回任务ID     │                 │               │                  │
  │<───────────────│                 │               │                  │
  │                 │                 │               │                  │
  │  ─────────────────────────────────────────────────────────────────    │
  │                 │                 │               │                  │
  │  轮询状态       │  GET /status/{id}                │                  │
  │<───────────────│────────────────>│               │                  │
  │                 │<────────────────│               │                  │
  │                 │                 │               │                  │
  │                 │                 │  ASR Task    │                  │
  │                 │                 │<──────────────│                  │
  │                 │                 │               │                  │
  │                 │                 │               │  Whisper API     │
  │                 │                 │               │─────────────────>│
  │                 │                 │               │<─────────────────│
  │                 │                 │               │                  │
  │                 │                 │  更新进度     │                  │
  │                 │                 │──────────────>│                  │
  │                 │                 │               │                  │
  │  更新进度条     │                 │               │                  │
  │<───────────────│                 │               │                  │
  │                 │                 │               │                  │
  │                 │                 │  Enhance Task│                  │
  │                 │                 │<──────────────│                  │
  │                 │                 │               │                  │
  │                 │                 │               │  DeepSeek API    │
  │                 │                 │               │─────────────────>│
  │                 │                 │               │<─────────────────│
  │                 │                 │               │                  │
  │                 │                 │  更新进度     │                  │
  │                 │                 │──────────────>│                  │
  │                 │                 │               │                  │
  │  更新进度条     │                 │               │                  │
  │<───────────────│                 │               │                  │
  │                 │                 │               │                  │
  │                 │                 │  Summary Task│                  │
  │                 │                 │<──────────────│                  │
  │                 │                 │               │                  │
  │                 │                 │               │  DeepSeek API    │
  │                 │                 │               │─────────────────>│
  │                 │                 │               │<─────────────────│
  │                 │                 │               │                  │
  │                 │                 │  更新进度     │                  │
  │                 │                 │──────────────>│                  │
  │                 │                 │               │                  │
  │  处理完成       │                 │               │                  │
  │<───────────────│                 │               │                  │
  │                 │                 │               │                  │
  │  查看结果       │  GET /meetings/{id}              │                  │
  │───────────────>│────────────────>│               │                  │
  │                 │<────────────────│               │                  │
  │                 │                 │               │                  │
  │  显示结果       │                 │               │                  │
  │<───────────────│                 │               │                  │
```

### 4.2 状态转换图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              任务状态流转                                    │
└─────────────────────────────────────────────────────────────────────────────┘

         ┌─────────────┐
         │   pending   │  任务已创建，等待执行
         └──────┬──────┘
                │
                ▼
         ┌─────────────┐
         │  processing │  任务执行中
         └──────┬──────┘
                │
        ┌───────┴───────┐
        ▼               ▼
 ┌─────────────┐  ┌─────────────┐
 │  completed  │  │   failed    │
 │ (成功)      │  │ (失败)      │
 └─────────────┘  └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │  retrying   │  重试中 (可选)
                 └──────┬──────┘
                        │
                        ▼
                 (回到 processing)

会议状态 (Meeting.status):
  • pending:      待处理
  • processing:   处理中
  • completed:    处理完成
  • failed:       处理失败
```

### 4.3 Celery 任务链设计

```python
# tasks/celery_tasks.py

from celery import chain, group, shared_task
from celery.result import AsyncResult

@shared_task(bind=True, max_retries=3)
def asr_task(self, meeting_id: int, file_path: str):
    """ASR 转录任务"""
    from services.asr_service import ASRService
    from models.database import SessionLocal, Meeting

    db = SessionLocal()
    try:
        # 更新状态
        meeting = db.query(Meeting).get(meeting_id)
        meeting.status = "processing"
        db.commit()

        # 调用 Whisper ASR
        asr_service = ASRService()
        result = asr_service.transcribe(file_path)

        # 保存转录结果
        # ...

        return {"meeting_id": meeting_id, "transcript_id": result.id}
    except Exception as e:
        self.retry(exc=e, countdown=60)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def enhance_task(self, meeting_id: int, transcript_id: int):
    """LLM 增强任务"""
    from services.enhance_service import EnhanceService
    from models.database import SessionLocal

    db = SessionLocal()
    try:
        # 调用 LLM 增强
        enhance_service = EnhanceService()
        result = enhance_service.enhance(transcript_id)

        return {"meeting_id": meeting_id, "enhanced_text": result.text}
    except Exception as e:
        self.retry(exc=e, countdown=60)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def summary_task(self, meeting_id: int, template_id: int):
    """会议总结任务"""
    from services.summary_service import SummaryService
    from models.database import SessionLocal, Meeting

    db = SessionLocal()
    try:
        # 调用 LLM 总结
        summary_service = SummaryService()
        result = summary_service.generate(meeting_id, template_id)

        # 更新会议状态
        meeting = db.query(Meeting).get(meeting_id)
        meeting.status = "completed"
        db.commit()

        return {"meeting_id": meeting_id, "summary_id": result.id}
    except Exception as e:
        # 标记会议失败
        meeting = db.query(Meeting).get(meeting_id)
        meeting.status = "failed"
        db.commit()
        self.retry(exc=e, countdown=60)
    finally:
        db.close()


def create_meeting_pipeline(meeting_id: int, file_path: str, template_id: int):
    """创建会议处理任务链"""
    return chain(
        asr_task.s(meeting_id, file_path),
        enhance_task.s(meeting_id),
        summary_task.s(meeting_id, template_id)
    )()
```

---

## 五、API 接口定义

### 5.1 RESTful API 列表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| **会议管理** |||
| POST | `/api/v1/meetings` | 创建会议 (上传文件) | ✅ |
| GET | `/api/v1/meetings` | 获取会议列表 | ✅ |
| GET | `/api/v1/meetings/{id}` | 获取会议详情 | ✅ |
| DELETE | `/api/v1/meetings/{id}` | 删除会议 | ✅ |
| **任务状态** |||
| GET | `/api/v1/tasks/{id}` | 获取任务状态 | ✅ |
| GET | `/api/v1/tasks/{id}/progress` | 获取任务进度 (SSE) | ✅ |
| POST | `/api/v1/tasks/{id}/cancel` | 取消任务 | ✅ |
| **转录与总结** |||
| GET | `/api/v1/meetings/{id}/transcript` | 获取转录文本 | ✅ |
| GET | `/api/v1/meetings/{id}/summary` | 获取总结结果 | ✅ |
| POST | `/api/v1/meetings/{id}/summarize` | 生成新总结 | ✅ |
| **模板管理** |||
| GET | `/api/v1/templates` | 获取模板列表 | ✅ |
| GET | `/api/v1/templates/{id}` | 获取模板详情 | ✅ |
| POST | `/api/v1/templates` | 创建自定义模板 | ✅ |
| PUT | `/api/v1/templates/{id}` | 更新模板 | ✅ |
| DELETE | `/api/v1/templates/{id}` | 删除模板 | ✅ |
| **用户认证** (Phase 2) |||
| POST | `/api/v1/auth/register` | 用户注册 | ❌ |
| POST | `/api/v1/auth/login` | 用户登录 | ❌ |
| POST | `/api/v1/auth/logout` | 用户登出 | ✅ |
| GET | `/api/v1/auth/me` | 获取当前用户 | ✅ |

### 5.2 核心 API 详解

#### 5.2.1 创建会议 (上传文件)

```python
# POST /api/v1/meetings

@app.post("/api/v1/meetings")
async def create_meeting(
    file: UploadFile,
    title: str = Form(...),
    template_id: int = Form(1),
    language: str = Form("zh"),
    current_user: User = Depends(get_current_user)
):
    """
    上传音视频文件并创建会议处理任务

    Request:
        - file: 音视频文件 (mp4, mp3, wav, m4a)
        - title: 会议标题
        - template_id: 使用的模板 ID
        - language: 语言代码 (zh, en)

    Response:
        {
            "id": 1,
            "title": "产品周会",
            "status": "pending",
            "task_id": "celery-task-uuid",
            "created_at": "2026-03-11T10:00:00Z"
        }
    """
```

#### 5.2.2 获取任务进度 (SSE)

```python
# GET /api/v1/tasks/{id}/progress

@app.get("/api/v1/tasks/{task_id}/progress")
async def task_progress(task_id: str):
    """
    Server-Sent Events 实时推送任务进度

    Response Stream:
        data: {"stage": "asr", "progress": 45, "message": "正在转录..."}

        data: {"stage": "enhance", "progress": 20, "message": "LLM 增强中..."}

        data: {"stage": "summary", "progress": 80, "message": "生成总结..."}

        data: {"stage": "completed", "progress": 100, "meeting_id": 1}
    """
    async def event_generator():
        while True:
            task = AsyncResult(task_id)
            if task.state == 'PENDING':
                yield f"data: {{'stage': 'pending', 'progress': 0}}\n\n"
            elif task.state == 'PROGRESS':
                yield f"data: {task.info}\n\n"
            elif task.state == 'SUCCESS':
                yield f"data: {{'stage': 'completed', 'progress': 100}}\n\n"
                break
            elif task.state == 'FAILURE':
                yield f"data: {{'stage': 'failed', 'error': '{str(task.info)}'}}\n\n"
                break
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
```

#### 5.2.3 获取会议详情

```python
# GET /api/v1/meetings/{id}

@app.get("/api/v1/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取会议完整信息，包括转录和总结

    Response:
        {
            "id": 1,
            "title": "产品周会",
            "status": "completed",
            "duration": 1800,
            "language": "zh",
            "created_at": "2026-03-11T10:00:00Z",
            "transcript": {
                "raw_text": "...",
                "enhanced_text": "...",
                "word_count": 5000
            },
            "summaries": [
                {
                    "id": 1,
                    "template": "产品经理",
                    "content": {...},
                    "llm_provider": "deepseek",
                    "llm_model": "deepseek-chat"
                }
            ]
        }
    """
```

### 5.3 Pydantic 模型

```python
# schemas/api.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: int = Field(default=1, ge=1)
    language: str = Field(default="zh", pattern="^(zh|en|ja|ko)$")


class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    duration: Optional[float]
    language: str
    task_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    id: int
    raw_text: str
    enhanced_text: Optional[str]
    word_count: Optional[int]
    utterance_count: Optional[int]
    language: Optional[str]

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    id: int
    template_id: int
    content: dict
    llm_provider: Optional[str]
    llm_model: Optional[str]
    tokens_used: Optional[int]
    processing_time: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class MeetingDetailResponse(MeetingResponse):
    transcript: Optional[TranscriptResponse]
    summaries: List[SummaryResponse]


class TaskProgress(BaseModel):
    stage: str  # pending, asr, enhance, summary, completed, failed
    progress: int = Field(ge=0, le=100)
    message: Optional[str] = None
    error: Optional[str] = None
```

---

## 六、项目结构

### 6.1 目录结构

```
meeting_intelligence/
├── api/                          # Web API 层 (新增)
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口
│   ├── dependencies.py           # 依赖注入
│   ├── routers/                  # API 路由
│   │   ├── __init__.py
│   │   ├── meetings.py           # 会议管理
│   │   ├── tasks.py              # 任务状态
│   │   ├── transcripts.py        # 转录相关
│   │   ├── summaries.py          # 总结相关
│   │   ├── templates.py          # 模板管理
│   │   └── auth.py               # 认证 (Phase 2)
│   ├── schemas/                  # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── meeting.py
│   │   ├── task.py
│   │   └── user.py
│   └── middleware/               # 中间件
│       ├── __init__.py
│       ├── auth.py
│       └── error_handler.py
│
├── tasks/                        # Celery 任务 (新增)
│   ├── __init__.py
│   ├── celery_app.py             # Celery 配置
│   ├── asr_task.py
│   ├── enhance_task.py
│   └── summary_task.py
│
├── services/                     # 业务逻辑层 (新增)
│   ├── __init__.py
│   ├── meeting_service.py
│   ├── task_service.py
│   ├── asr_service.py            # 封装现有 ASR 模块
│   ├── enhance_service.py        # 封装现有增强模块
│   ├── summary_service.py        # 封装现有总结模块
│   ├── storage_service.py        # 文件存储
│   └── template_service.py       # 模板管理
│
├── models/                       # 数据模型 (新增)
│   ├── __init__.py
│   └── database.py               # SQLAlchemy 模型
│
├── core/                         # 核心配置 (新增)
│   ├── __init__.py
│   ├── config.py                 # 配置管理
│   ├── security.py               # 安全相关
│   └── database.py               # 数据库连接
│
├── frontend/                     # 前端代码 (新增 - Phase 1)
│   ├── streamlit_app.py          # Streamlit 应用
│   └── components/               # UI 组件
│
├── asr/                          # 现有 ASR 模块
├── transcript/                   # 现有转录模块
├── summarizer/                   # 现有总结模块
├── template/                     # 现有模板模块
│
├── storage/                      # 文件存储 (新增)
│   ├── uploads/                  # 上传文件
│   ├── transcripts/              # 转录结果
│   ├── summaries/                # 总结结果
│   └── cache/                    # 缓存文件
│
├── tests/                        # 测试
│   ├── test_api/                 # API 测试
│   ├── test_tasks/               # 任务测试
│   └── test_services/            # 服务测试
│
├── docker/                       # Docker 配置 (新增)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── scripts/                      # 脚本
│   ├── init_db.py                # 初始化数据库
│   └── seed_data.py              # 填充测试数据
│
├── .env.example
├── .env
├── requirements.txt
├── requirements-web.txt          # Web 相关依赖 (新增)
├── pyproject.toml
└── README.md
```

---

## 七、潜在挑战与解决方案

### 7.1 长视频处理挑战

| 挑战 | 解决方案 |
|------|----------|
| **内存溢出** | • 分段加载音频<br>• 使用生成器处理流式数据<br>• Celery 任务超时控制 |
| **处理时间长** | • 实时进度推送 (SSE/WebSocket)<br>• 支持后台处理，用户可关闭页面<br>• 任务断点续传 |
| **并发限制** | • Celery worker 限流<br>• 任务队列优先级<br>• Redis 状态缓存 |

### 7.2 LLM API 限制

| 挑战 | 解决方案 |
|------|----------|
| **速率限制** | • 指数退避重试<br>• 多 API Key 轮询<br>• 请求队列化 |
| **成本控制** | • Token 预估<br>• 使用更便宜的模型 (DeepSeek)<br>• 缓存相同请求结果 |
| **超时问题** | • 增加超时时间<br>• 异步长轮询<br>• Fallback 到备用 Provider |

### 7.3 文件存储挑战

| 挑战 | 解决方案 |
|------|----------|
| **大文件上传** | • 分片上传<br>• 上传进度显示<br>• 断点续传 |
| **存储空间** | • 定期清理旧文件<br>• 压缩归档<br>• 迁移到对象存储 (S3) |
| **文件安全** | • 随机文件名<br>• 访问权限控制<br>• 定期扫描 |

### 7.4 扩展性挑战

| 挑战 | 解决方案 |
|------|----------|
| **数据库性能** | • 读写分离<br>• 索引优化<br>• 迁移到 PostgreSQL |
| **水平扩展** | • 无状态 API 服务<br>• Redis 共享缓存<br>• 负载均衡 |
| **监控告警** | • Prometheus 指标<br>• Celery 任务监控<br>• 错误日志聚合 |

---

## 八、实施路线图

### Phase 1: MVP (4-6 周)

| 周 | 任务 | 交付物 |
|----|------|--------|
| 1 | 项目结构搭建、数据库设计 | `models/`, `core/` |
| 2 | FastAPI 基础框架、文件上传 | `/api/v1/meetings` |
| 3 | Celery 任务集成、ASR 任务 | `tasks/`, `services/` |
| 4 | LLM 增强/总结任务 | 完整处理流程 |
| 5 | Streamlit 前端界面 | 可用 Web UI |
| 6 | 测试、文档、部署 | MVP 发布 |

### Phase 2: 增强版 (4-6 周)

| 功能 | 描述 |
|------|------|
| 用户认证 | JWT + 用户权限 |
| WebSocket | 实时进度推送 |
| 历史记录 | 搜索、分页、过滤 |
| 导出功能 | PDF/Word 导出 |
| 部署优化 | Docker + Nginx |

### Phase 3: 企业版 (按需)

| 功能 | 描述 |
|------|------|
| 多租户 | 企业隔离 |
| 权限管理 | RBAC |
| API 限流 | 防止滥用 |
| 对象存储 | S3/MinIO 集成 |
| 监控告警 | 完整可观测性 |

---

## 九、总结

本架构设计旨在将 "Jinni 会议精灵" 从 CLI 工具平滑演进为 SaaS 平台：

1. **最小化改动**: 复用现有 `asr/`, `transcript/`, `summarizer/` 模块
2. **分层架构**: API → Service → Domain，职责清晰
3. **异步优先**: Celery 处理长任务，不阻塞用户
4. **可扩展性**: 模块化设计，便于后续功能添加
5. **成本优化**: 支持 DeepSeek 等低成本 LLM

**下一步**: 创建 OpenSpec 变更提案，开始 Phase 1 开发。

---

*文档版本: 1.0*
*创建日期: 2026-03-11*
*作者: 架构组*
