# LLM 总结功能使用指南

**更新日期**: 2026-05-13
**版本**: v1.0

---

## 📋 当前状态

### ✅ 已实现
1. 真实 LLM 总结功能已接入
2. 支持多种模板（8个内置模板）
3. 模板驱动的总结生成
4. 自动 fallback 到 mock 模式（未配置 API key 时）

### ⚠️ 配置要求
需要配置 OpenAI API Key 或兼容服务才能使用真实 LLM

---

## 🔧 LLM 配置

### 方式1：环境变量（推荐）

在项目根目录或 backend 目录创建 `.env` 文件：

```bash
# LLM 配置
LLM_PROVIDER=openai
OPENAI_API_KEY=<YOUR_API_KEY>
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### 方式2：系统环境变量

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="<YOUR_API_KEY>"

# Windows (CMD)
set OPENAI_API_KEY=<YOUR_API_KEY>

# Linux/Mac
export OPENAI_API_KEY=<YOUR_API_KEY>
```

### 方式3：启动时传递

```bash
# 直接在命令行设置
OPENAI_API_KEY=sk-xxx python backend/main.py
```

---

## 🌟 支持的 LLM 服务

### 1. OpenAI 官方
```bash
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### 2. DeepSeek
```bash
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 3. 阿里云 Qwen
```bash
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus
```

### 4. 其他兼容 OpenAI API 的服务
只需修改 `OPENAI_BASE_URL` 和 `OPENAI_MODEL`

---

## 📊 模板列表

### 内置8个模板

1. **通用会议纪要** (general_meeting)
   - 会议摘要、关键讨论、决策结论、待办事项

2. **周会总结** (weekly_meeting)
   - 本周亮点、遇到的问题、下周计划

3. **项目评审** (project_review)
   - 项目进展、关键里程碑、风险评估、下一步计划

4. **客户沟通** (customer_communication)
   - 客户需求、业务场景、方案讨论、下一步行动

5. **销售会议** (sales_meeting)
   - 销售目标、市场分析、销售策略、行动计划

6. **面试记录** (interview_record)
   - 候选人背景、能力评估、综合评价

7. **产品需求讨论** (product_requirement)
   - 核心需求、用户价值、讨论重点、技术风险、待办事项、最终决策

8. **项目复盘** (project_retrospective)
   - 项目成果、成功经验、遇到的问题、改进建议

---

## 🚀 启动方式

### 未配置 API Key（Mock 模式）
```bash
# 直接启动，会自动使用 mock 总结
python backend/main.py
```

**后端日志**：
```
[BACKEND] LLM not configured, using mock summary
[BACKEND] using mock summary (no real LLM)
```

### 已配置 API Key（真实 LLM）
```bash
# 设置环境变量后启动
export OPENAI_API_KEY=sk-xxx
python backend/main.py
```

**后端日志**：
```
[BACKEND] using real LLM for summary generation
[BACKEND] calling LLM API...
[LLM] summary generated: length=1234
[BACKEND] summary generated successfully
```

---

## 🔍 日志验证

### 前端日志
```
[FRONTEND] generate_summary called: meeting_id=xxx, template_id=general_meeting
[FRONTEND] summary endpoint: http://localhost:8000/api/meetings/xxx/summarize
[FRONTEND] summary response status: 200
[FRONTEND] get_summary called: meeting_id=xxx
[FRONTEND] get_summary response status: 200
```

### 后端日志（真实 LLM）
```
[BACKEND] summarize called: meeting_id=xxx
[BACKEND] template_id: general_meeting
[BACKEND] transcript length: 5678
[BACKEND] using real LLM for summary generation
[BACKEND] calling LLM API...
[LLM] summary generated: length=1234
[BACKEND] summary generated successfully: length=1234
[BACKEND] summary task completed
```

### 后端日志（Mock 模式）
```
[BACKEND] summarize called: meeting_id=xxx
[BACKEND] template_id: general_meeting
[BACKEND] transcript length: 5678
[BACKEND] LLM not configured, using mock summary
[BACKEND] using mock summary (no real LLM)
[BACKEND] summary generated (mock): length=2048
```

---

## ✅ 验收标准

### 1. 内容真实性
**测试方法**：使用不同的 transcript 测试
- ✅ 不同会议内容应得到不同总结
- ❌ 如果所有会议总结都一样，说明仍是 mock

### 2. 模板差异性
**测试方法**：选择不同模板生成总结
- ✅ "产品需求讨论"应包含：核心需求、用户价值、技术风险
- ✅ "面试记录"应包含：背景、能力评估、综合评价
- ❌ 如果所有模板结构一样，说明没有使用模板

### 3. LLM 调用验证
**测试方法**：查看后端日志
- ✅ 配置 API Key 后应看到 `[LLM] summary generated`
- ✅ 未配置应看到 `[BACKEND] using mock summary`

---

## 📝 总结生成 Prompt

### 系统Prompt结构
```
你是一个专业会议总结助手。

请根据以下会议文字稿，按照用户选择的总结模板生成 Markdown 会议总结。

模板名称：{template_name}
模板说明：{template_description}
模板输出结构：{sections}
模板要求：{template_prompt}

会议文字稿：{transcript}

要求：
1. 必须严格按照模板结构输出
2. 不要编造会议中没有的信息
3. 待办事项要包含负责人、事项、截止时间，如果没有则写"未明确"
4. 输出 Markdown 格式
5. 不要输出无关解释
```

---

## 🛠️ 故障排除

### 问题1：总结内容固定不变
**原因**：仍在使用 mock 模式
**解决**：
1. 检查是否配置了 `OPENAI_API_KEY`
2. 查看后端日志是否有 `[LLM] summary generated`

### 问题2：LLM 调用失败
**原因**：API Key 错误或网络问题
**解决**：
1. 验证 API Key 是否正确
2. 检查 `OPENAI_BASE_URL` 是否可访问
3. 查看后端详细错误信息

### 问题3：总结不符合模板结构
**原因**：LLM 未严格遵守格式
**解决**：
1. 调整系统 prompt，强调结构要求
2. 使用更强的模型（如 gpt-4）
3. 在 prompt 中添加更多示例

---

## 💰 成本估算

### OpenAI GPT-4o-mini
- 输入：$0.15 / 1M tokens
- 输出：$0.60 / 1M tokens
- 一次会议总结（约 2000 tokens）：成本 < $0.01

### DeepSeek
- 输入：¥1 / 1M tokens
- 输出：¥2 / 1M tokens
- 一次会议总结：成本 < ¥0.01

---

**创建时间**: 2026-05-13
**版本**: v1.0
**状态**: ✅ 已完成并测试
