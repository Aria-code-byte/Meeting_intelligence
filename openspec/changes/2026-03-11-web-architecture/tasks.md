# Tasks: Web Architecture Implementation

**Change ID**: 2026-03-11-web-architecture
**Status**: Proposal

---

## Phase 1: MVP (Week 1-6)

### Week 1: 基础架构

- [ ] **T1.1** 创建项目结构
  - [ ] `api/` - FastAPI 应用
  - [ ] `tasks/` - Celery 任务
  - [ ] `services/` - 业务逻辑层
  - [ ] `models/` - 数据模型
  - [ ] `core/` - 配置模块
  - [ ] `storage/` - 文件存储目录

- [ ] **T1.2** 数据库设计与实现
  - [ ] 定义 SQLAlchemy 模型
  - [ ] 创建数据库迁移脚本 (Alembic)
  - [ ] 编写初始化脚本 `scripts/init_db.py`

- [ ] **T1.3** FastAPI 基础框架
  - [ ] 创建 `api/main.py` 应用入口
  - [ ] 配置 CORS、中间件
  - [ ] 添加健康检查端点 `/health`
  - [ ] 集成自动文档 (Swagger/ReDoc)

- [ ] **T1.4** 配置管理
  - [ ] `core/config.py` - Pydantic Settings
  - [ ] `.env` 更新 (添加数据库、Redis 配置)
  - [ ] `core/database.py` - 数据库连接池

### Week 2: API 与文件上传

- [ ] **T2.1** 会议管理 API
  - [ ] `api/routers/meetings.py`
  - [ ] POST `/api/v1/meetings` - 创建会议
  - [ ] GET `/api/v1/meetings` - 会议列表 (分页)
  - [ ] GET `/api/v1/meetings/{id}` - 会议详情
  - [ ] DELETE `/api/v1/meetings/{id}` - 删除会议

- [ ] **T2.2** 文件上传功能
  - [ ] 支持格式: mp4, mp3, wav, m4a, m4v
  - [ ] 文件大小限制 (默认 500MB)
  - [ ] 文件重命名 (UUID)
  - [ ] 上传进度显示

- [ ] **T2.3** Pydantic Schema 定义
  - [ ] `api/schemas/meeting.py`
  - [ ] `api/schemas/task.py`
  - [ ] 请求/响应验证

- [ ] **T2.4** 单元测试
  - [ ] `tests/test_api/test_meetings.py`
  - [ ] 文件上传测试
  - [ ] API 验证测试

### Week 3: Celery 集成与 ASR 任务

- [ ] **T3.1** Celery 配置
  - [ ] `tasks/celery_app.py` - Celery 应用配置
  - [ ] Redis broker 连接
  - [ ] 任务结果后端配置
  - [ ] Worker 启动脚本

- [ ] **T3.2** ASR 任务实现
  - [ ] `tasks/asr_task.py` - 封装现有 Whisper 调用
  - [ ] 进度回调机制
  - [ ] 错误处理与重试

- [ ] **T3.3** 任务状态 API
  - [ ] `api/routers/tasks.py`
  - [ ] GET `/api/v1/tasks/{id}` - 获取任务状态
  - [ ] GET `/api/v1/tasks/{id}/progress` - SSE 进度推送
  - [ ] POST `/api/v1/tasks/{id}/cancel` - 取消任务

- [ ] **T3.4** ASR 服务层
  - [ ] `services/asr_service.py` - 封装现有 `asr/` 模块
  - [ ] 音频预处理 (FFmpeg)
  - [ ] Whisper 调用
  - [ ] 结果入库

### Week 4: LLM 增强与总结任务

- [ ] **T4.1** 增强任务实现
  - [ ] `tasks/enhance_task.py` - 封装现有增强逻辑
  - [ ] `services/enhance_service.py`
  - [ ] 调用 `transcript/llm/enhancer.py`

- [ ] **T4.2** 总结任务实现
  - [ ] `tasks/summary_task.py` - 封装现有总结逻辑
  - [ ] `services/summary_service.py`
  - [ ] 调用 `summarizer/generate.py`

- [ ] **T4.3** 任务链编排
  - [ ] 定义处理流程: ASR → Enhance → Summary
  - [ ] 使用 Celery chain/group
  - [ ] 错误处理与回滚

- [ ] **T4.4** 转录与总结 API
  - [ ] GET `/api/v1/meetings/{id}/transcript`
  - [ ] GET `/api/v1/meetings/{id}/summary`
  - [ ] POST `/api/v1/meetings/{id}/summarize` - 重新生成

### Week 5: Streamlit 前端

- [ ] **T5.1** Streamlit 应用框架
  - [ ] `frontend/streamlit_app.py`
  - [ ] 页面布局配置
  - [ ] 会话状态管理

- [ ] **T5.2** 文件上传页面
  - [ ] `st.file_uploader` 组件
  - [ ] 表单输入 (标题、模板选择)
  - [ ] 上传进度显示

- [ ] **T5.3** 任务进度页面
  - [ ] 实时进度条
  - [ ] 当前阶段显示
  - [ ] 错误提示

- [ ] **T5.4** 结果展示页面
  - [ ] 转录文本展示
  - [ ] 总结结果渲染
  - [ ] 下载按钮

### Week 6: 测试与部署

- [ ] **T6.1** 集成测试
  - [ ] 端到端流程测试
  - [ ] 异常场景测试
  - [ ] 性能测试

- [ ] **T6.2** 文档完善
  - [ ] API 文档 (Swagger)
  - [ ] 部署文档
  - [ ] 用户使用手册

- [ ] **T6.3** 部署配置
  - [ ] 环境变量检查清单
  - [ ] 启动脚本
  - [ ] Nginx 配置 (可选)

- [ ] **T6.4** MVP 发布
  - [ ] 标记版本 v0.2.0
  - [ ] Release Notes

---

## Phase 2: Enhancement (Week 7-12)

### Week 7-8: 用户认证

- [ ] **T2.1** JWT 认证实现
  - [ ] `core/security.py` - JWT 生成/验证
  - [ ] 用户注册/登录 API
  - [ ] 认证中间件

- [ ] **T2.2** 用户管理
  - [ ] `api/routers/auth.py`
  - [ ] 用户 CRUD
  - [ ] 密码重置

### Week 9-10: WebSocket 与搜索

- [ ] **T2.3** WebSocket 推送
  - [ ] 实时进度推送
  - [ ] 连接管理

- [ ] **T2.4** 历史记录
  - [ ] 会议列表搜索
  - [ ] 全文搜索 (PostgreSQL FTS)
  - [ ] 过滤与排序

### Week 11-12: 导出与部署

- [ ] **T2.5** 导出功能
  - [ ] PDF 导出
  - [ ] Word 导出

- [ ] **T2.6** Docker 部署
  - [ ] Dockerfile
  - [ ] docker-compose.yml
  - [ ] 部署文档

---

## Dependencies

### 外部依赖

| 组件 | 版本要求 |
|------|----------|
| Python | 3.12+ |
| Redis | 7.0+ |
| SQLite | 3.35+ (MVP) |
| PostgreSQL | 15+ (Phase 2) |
| FFmpeg | 4.0+ |

### Python 包

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
celery[redis]>=5.3.0
redis>=5.0.0
sqlalchemy>=2.0.0
alembic>=1.12.0
streamlit>=1.28.0
python-multipart>=0.0.6
pydantic>=2.4.0
pydantic-settings>=2.1.0
```

---

## Definition of Done

每个任务完成标准：
- [ ] 代码实现完成
- [ ] 单元测试通过
- [ ] 代码审查通过
- [ ] 文档更新完成

---

## Notes

- 现有 `asr/`, `transcript/`, `summarizer/`, `template/` 模块保持不变
- 新增 `services/` 层封装现有模块，避免直接耦合
- MVP 阶段暂不实现用户认证，Phase 2 添加
