# Change: PR4 - 高精度语义增强模块

**Status**: ⏸️ **PAUSED** (Out of MVP Scope)

**Pause Date**: 2026-03-02

**Reason**:
- PR4 属于精度优化功能，而非 MVP 必需功能
- PR3 已具备可用的增强能力（整块回退、多模板支持）
- 当前优先目标是打通产品闭环（CLI + 配置 + 可运行流程）
- 将在 MVP Completion 完成后重新评估是否继续 PR4

---

## Why (Original)

PR3 实现了轻量级 LLM 增强，但存在以下精度问题：

1. **整块回退粒度过粗** - 单句失败导致整块使用原文，浪费有效增强
2. **位置映射易误匹配** - 按标点分割 + 位置映射在 LLM 改写时容易错位
3. **置信度二元化** - 只有"通过/失败"两种状态，缺乏质量量化
4. **缺乏语义验证** - 无法检测 LLM 是否偏离原文语义

PR4 通过单句级回退、混合映射策略、多特征置信度计算，提升增强精度和可控性。

## What Changes

### 核心功能模块

- **ADDED**: `transcript/llm/types.py` - PR4 数据类型定义
  - `MappingQuality`, `FallbackLevel`, `MappingMethod` 枚举
  - `MappingInfo`, `FallbackInfo`, `ConfidenceBreakdown` 结构
  - `SentenceMappingResult`, `MultiRoundResult`

- **ADDED**: `transcript/llm/mapper.py` - 映射引擎
  - `ExactMapper` - JSON 精确匹配（sentence_index）
  - `EmbeddingMapper` - Embedding 相似度匹配
  - `PositionMapper` - 位置回退映射
  - `HybridMapper` - 三级优先级混合策略

- **ADDED**: `transcript/llm/confidence.py` - 置信度计算器
  - 多特征加权（embedding_similarity, length_ratio, llm_metadata）
  - 动态权重重归一（处理缺失特征）

- **ADDED**: `transcript/llm/fallback.py` - 回退引擎
  - 单句级回退（而非整块）
  - 置信度阈值判断
  - 回退历史记录

- **MODIFIED**: `transcript/llm/__init__.py` - 导出 PR4 新类型和函数

- **ADDED**: `docs/architecture/pr4-precision-enhancement.md` - 完整设计文档

### 测试文件

- **ADDED**: `tests/test_mapper/test_exact_mapper.py` - 精确映射测试
- **ADDED**: `tests/test_mapper/test_position_mapper.py` - 位置映射测试
- **ADDED**: `tests/test_confidence.py` - 置信度计算测试
- **ADDED**: `tests/test_fallback.py` - 回退逻辑测试

## Impact

- **Affected specs**: 新增 capability `llm-precision-enhancement`
- **Affected code**:
  - 新增: `transcript/llm/types.py`, `transcript/llm/mapper.py`, `transcript/llm/confidence.py`, `transcript/llm/fallback.py`
  - 修改: `transcript/llm/__init__.py`
  - 新增测试: 4+ 新测试文件，73+ 测试用例
- **Dependencies**: 无新增外部依赖
- **Backwards Compatibility**: 完全兼容 PR3，默认配置保持 PR3 行为

## Key Design Decisions

1. **三级映射优先级**: Exact → Embedding → Position，保证在大多数情况下找到最佳映射
2. **单句回退**: 置信度低于阈值时仅回退单句，不影响块内其他句子
3. **责任分离**: Mapper、ConfidenceCalculator、Fallback 各司其职，职责清晰
4. **向后兼容**: 默认配置 = PR3 行为，用户可渐进式升级

## Success Criteria

- [ ] 所有单元测试通过
- [ ] 回归测试验证 PR3 兼容性
- [ ] 混合映射策略在各种边界情况下表现稳定
- [ ] 置信度计算合理反映增强质量
- [ ] 单句回退正确触发
- [ ] 文档完整（设计文档 + 代码注释）

## Timeline

进行中（已创建架构文档和部分代码骨架）
