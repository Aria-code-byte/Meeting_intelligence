# Meeting Intelligence - 文档目录

## 📂 文档结构

```
docs/
├── README.md                                    # 本文件
├── progress/                                    # 开发进度报告
│   └── 2026-03-02-pr1-pr3-completed-pr4-in-progress.md
├── architecture/                                # 架构设计文档
│   ├── transcript-artifact-layering.md          # PR1: Raw/Enhanced 工件分层
│   └── pr4-precision-enhancement.md             # PR4: 高精度语义增强设计
├── archive/                                     # 历史文档归档
│   ├── 2026-02-26-status.md                     # 早期状态记录
│   └── 2026-02-27-deep-audit.md                 # 深度审计报告
├── REFACTOR_PROPOSAL.md                         # 重构提案
└── TRANSCRIPT_REFINER_USAGE.md                  # 转录优化器使用说明
```

---

## 📊 开发进度报告

### 最新进度 (2026-03-02)

**文件**: `progress/2026-03-02-pr1-pr3-completed-pr4-in-progress.md`

| 状态 | PR/阶段 | 描述 |
|------|---------|------|
| ✅ | PR1 | Raw/Enhanced 工件分层 |
| ✅ | PR2 | 确定性分块 + 整数毫秒模型 |
| ✅ | PR3 | 轻量级 LLM 接入 |
| ⏸️ | PR4 | 高精度语义增强模块 (已暂停，非 MVP) |
| ✅ | MVP Iteration 0 | 环境与依赖规范化 |
| ✅ | MVP Iteration 1 | LLM 抽象层验证 |
| ✅ | MVP Iteration 4 | 最小 CLI 入口 |
| 🚀 | MVP Completion | 进行中 |

**测试覆盖**: 413 tests passing

**当前主线**: MVP Completion (openspec/changes/2026-02-25-mvp-completion/)

---

## 🏗️ 架构文档

### PR1: Raw/Enhanced 工件分层

**文件**: `architecture/transcript-artifact-layering.md`

- 保留原始 ASR 工件
- 为增强版本预留存储路径
- `transcript_path` → raw ASR
- `enhanced_transcript_path` → LLM enhanced

### PR4: 高精度语义增强设计

**文件**: `architecture/pr4-precision-enhancement.md` (782 行)

- 三级混合映射策略 (Exact → Embedding → Position)
- 单句级回退 (而非整块)
- 多特征置信度计算
- 完整数据结构设计

---

## 📦 已归档文档

| 日期 | 文件 | 内容 |
|------|------|------|
| 2026-02-26 | `archive/2026-02-26-status.md` | 早期开发状态，GLM Provider 集成 |
| 2026-02-27 | `archive/2026-02-27-deep-audit.md` | 深度审计报告，全栈架构分析 |

---

## 📄 其他文档

| 文件 | 描述 |
|------|------|
| `REFACTOR_PROPOSAL.md` | 重构提案 |
| `TRANSCRIPT_REFINER_USAGE.md` | 转录优化器使用说明 |

---

## 🔍 快速导航

### 开发者

- 查看**最新进度**: `progress/2026-03-02-pr1-pr3-completed-pr4-in-progress.md`
- 查看**架构设计**: `architecture/`
- 查看**OpenSpec**: `openspec/changes/`

### 新人入门

1. 先读 `progress/` 下的最新进度报告了解项目状态
2. 再读 `architecture/` 下的设计文档了解技术细节
3. 参考 `CLAUDE.md` 了解开发约定

---

*更新时间: 2026-03-02*
