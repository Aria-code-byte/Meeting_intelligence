# Proposal: Web Architecture Implementation

**Change ID**: 2026-03-11-web-architecture
**Status**: Proposal
**Created**: 2026-03-11
**Author**: Architecture Team

---

## Overview

将 "Jinni 会议精灵" 从 CLI 工具演进为 Web 应用，实现：
- 可视化界面：文件上传与结果展示
- 任务持久化：会议、转录、总结的结构化存储
- 异步处理：长视频不阻塞前端

---

## Motivation

当前项目仅支持 CLI 模式，存在以下限制：

1. **用户体验**: 非技术用户难以使用命令行
2. **持久化缺失**: 处理结果仅保存在本地文件
3. **状态追踪**: 长视频处理无法实时查看进度
4. **多终端访问**: 无法在多设备间同步数据

Web 化后可解决上述问题，并为企业版奠定基础。

---

## Proposed Solution

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Streamlit (Phase 1) → Vue.js (Phase 2) |
| 后端 | FastAPI |
| 异步任务 | Celery + Redis |
| 数据库 | SQLite (MVP) → PostgreSQL |
| 存储 | 本地文件系统 → MinIO/S3 |

### 核心模块

```
api/           - FastAPI 路由与依赖
tasks/         - Celery 异步任务
services/      - 业务逻辑层
models/        - SQLAlchemy 数据模型
core/          - 配置与安全
frontend/      - Streamlit UI
storage/       - 文件存储目录
```

### 数据库表

- `users` - 用户表 (Phase 2)
- `meetings` - 会议主表
- `tasks` - 任务状态表
- `transcripts` - 转录结果表
- `summaries` - 总结结果表
- `templates` - 模板表

### API 端点

```
POST   /api/v1/meetings              - 创建会议 (上传文件)
GET    /api/v1/meetings              - 获取会议列表
GET    /api/v1/meetings/{id}         - 获取会议详情
GET    /api/v1/tasks/{id}/progress   - 任务进度 (SSE)
GET    /api/v1/meetings/{id}/transcript - 获取转录
GET    /api/v1/meetings/{id}/summary - 获取总结
GET    /api/v1/templates             - 获取模板列表
```

---

## Implementation Plan

### Phase 1: MVP (6 weeks)

| Week | Tasks |
|------|-------|
| 1 | 项目结构搭建、数据库设计、FastAPI 框架 |
| 2 | 文件上传 API、Meeting CRUD |
| 3 | Celery 集成、ASR 异步任务 |
| 4 | LLM 增强/总结异步任务 |
| 5 | Streamlit 前端 UI |
| 6 | 测试、文档、部署 |

### Phase 2: Enhancement (4-6 weeks)

- 用户认证 (JWT)
- WebSocket 实时推送
- 历史记录搜索
- PDF/Word 导出
- Docker 部署

### Phase 3: Enterprise (on demand)

- 多租户支持
- RBAC 权限管理
- API 限流
- 对象存储集成

---

## Alternatives Considered

### 方案 A: Streamlit Only
- **优点**: 开发最快，纯 Python
- **缺点**: UI 定制受限，不适合生产环境
- **结论**: 适用于 MVP/内部工具

### 方案 B: Vue.js SPA + FastAPI
- **优点**: 完整的前后端分离，UI 灵活
- **缺点**: 开发周期长，需要前端技能
- **结论**: 适用于正式产品

### 方案 C: Gradio
- **优点**: 快速构建 ML 原型
- **缺点**: 定制性差，商业化不友好
- **结论**: 不采用

**最终选择**: Phase 1 用 Streamlit 快速验证，Phase 2 迁移到 Vue.js

---

## Risks and Mitigations

| 风险 | 缓解措施 |
|------|----------|
| 长视频处理超时 | Celery 异步 + 断点续传 |
| LLM API 限流 | 指数退避重试 + 多 Key 轮询 |
| 存储空间不足 | 分片存储 + 定期清理 + 对象存储 |
| 并发性能瓶颈 | Redis 缓存 + 数据库索引优化 |

---

## Open Questions

1. **认证时机**: Phase 1 是否需要用户登录？建议 MVP 跳过，Phase 2 添加
2. **部署方式**: Docker 部署是否必要？建议 Phase 1 手动部署，Phase 2 容器化
3. **LLM 成本**: 是否需要添加用量统计？建议记录 token 使用量

---

## Related Documents

- [详细架构设计](/docs/architecture/web-architecture.md)
- [LLM 调用流程](/docs/architecture/llm-call-flow.md)
- [现有 CLI 文档](/docs/cli-flow.md)
