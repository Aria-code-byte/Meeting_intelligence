# Spec: LLM Precision Enhancement

## Overview

在 PR3 轻量级 LLM 增强基础上，提升增强精度和语义理解质量。通过单句级回退、混合映射策略、多特征置信度计算，实现更精确的转录文本增强。

## ADDED Requirements

### REQ-1: 三级混合映射策略

系统应支持三级优先级的映射策略，按顺序尝试直到成功。

**Acceptance Criteria**:
- 优先级 1: ExactMapper - 通过 LLM 返回的 sentence_index 直接映射
- 优先级 2: EmbeddingMapper - 通过 embedding 相似度匹配句子
- 优先级 3: PositionMapper - 通过位置回退映射（PR3 方案）

#### Scenario: ExactMapper 成功
- **GIVEN** LLM 返回有效的 JSON 格式，包含 sentence_index
- **WHEN** 解析 LLM 输出
- **THEN** 使用 sentence_index 直接映射到原句
- **AND** 映射质量标记为 HIGH
- **AND** 置信度约为 0.95

#### Scenario: ExactMapper 失败降级到 EmbeddingMapper
- **GIVEN** LLM 返回非 JSON 格式或 JSON 缺少 sentence_index
- **WHEN** ExactMapper 解析失败
- **THEN** 降级到 EmbeddingMapper
- **AND** 使用 embedding 相似度匹配句子

#### Scenario: EmbeddingMapper 匹配率低降级到 PositionMapper
- **GIVEN** EmbeddingMapper 计算相似度矩阵
- **WHEN** 匹配率 < 60% 或严重乱序
- **THEN** 降级到 PositionMapper
- **AND** 使用位置映射作为兜底

#### Scenario: 所有 Mapper 都失败
- **GIVEN** 三级映射都尝试失败
- **WHEN** 无法找到有效映射
- **THEN** 触发 CHUNK fallback（整块回退）
- **AND** 使用原句作为增强结果

### REQ-2: Embedding 相似度匹配

系统应支持基于 embedding 的句子相似度匹配。

**Acceptance Criteria**:
- 构建相似度矩阵 [原句数量 × LLM输出句子数量]
- 使用匈牙利算法或贪心策略进行一对一匹配
- 相似度阈值默认 0.7，可配置
- 顺序一致性检查（防止严重乱序）

#### Scenario: 一对一匹配成功
- **GIVEN** 原句和 LLM 输出句子数量相同
- **WHEN** 计算相似度矩阵
- **THEN** 每个原句匹配到一个 LLM 句子
- **AND** 相似度 > 0.7 的匹配被接受

#### Scenario: 相似度过低
- **GIVEN** 某对句子的相似度 < 0.7
- **WHEN** 应用阈值过滤
- **THEN** 该匹配被跳过
- **AND** 对应原句使用原文

#### Scenario: 顺序不一致
- **GIVEN** 匹配结果导致句子严重乱序（跳跃 > 2）
- **WHEN** 检查顺序一致性
- **THEN** 该匹配被跳过

#### Scenario: LLM 两句合成一句
- **GIVEN** LLM 输出句子数 < 原句数
- **WHEN** 一对一匹配后有剩余原句
- **THEN** 剩余原句使用原文

### REQ-3: 多特征置信度计算

系统应支持多特征加权的置信度计算。

**Acceptance Criteria**:
- 特征 1: embedding 相似度（可选，权重 0.6）
- 特征 2: 长度比率（必须，权重 0.2）
- 特征 3: LLM 元数据（可选，权重 0.2）
- 支持动态权重重归一（处理缺失特征）

#### Scenario: 完整特征计算
- **GIVEN** 所有特征都有值
- **WHEN** 计算置信度
- **THEN** 使用配置的权重计算加权平均值
- **AND** 返回完整的 ConfidenceBreakdown

#### Scenario: 缺失 embedding 特征
- **GIVEN** ExactMapper 或 PositionMapper 使用（无 embedding）
- **WHEN** 计算置信度
- **THEN** 权重重分配到 length_ratio 和 llm_metadata
- **AND** length_ratio 权重变为 0.5，llm_metadata 权重变为 0.5

#### Scenario: 长度比率在理想范围
- **GIVEN** 增强文本长度是原文的 0.8-1.5 倍
- **WHEN** 计算 length_ratio_score
- **THEN** 返回 1.0

#### Scenario: 长度比率异常
- **GIVEN** 增强文本长度是原文的 5 倍以上
- **WHEN** 计算 length_ratio_score
- **THEN** 返回 0.2（低分）

### REQ-4: 单句级回退

系统应支持单句级别的回退，而非整块回退。

**Acceptance Criteria**:
- 置信度 < 阈值时回退单句
- embedding 相似度 < 阈值时回退单句
- 长度比率异常时回退单句
- 记录回退原因和历史

#### Scenario: 置信度低于阈值
- **GIVEN** 某句的置信度为 0.4
- **WHEN** 阈值为 0.6
- **THEN** 该句回退到原文
- **AND** fallback_level 标记为 SENTENCE
- **AND** fallback_reason 为 "low_confidence"

#### Scenario: 语义偏离
- **GIVEN** 某句的 embedding 相似度为 0.5
- **WHEN** 阈值为 0.7
- **THEN** 该句回退到原文
- **AND** fallback_reason 为 "semantic_drift"

#### Scenario: 块内混合回退
- **GIVEN** 一个 chunk 有 10 句
- **WHEN** 3 句置信度高，7 句置信度低
- **THEN** 3 句使用增强文本，7 句回退到原文
- **AND** 输出包含混合内容

### REQ-5: PR3 向后兼容

系统应完全兼容 PR3 的默认行为。

**Acceptance Criteria**:
- 默认配置下输出与 PR3 一致
- 所有 PR3 测试通过
- 配置字段默认值保持 PR3 行为

#### Scenario: 默认配置兼容
- **GIVEN** 使用默认配置
  - enable_per_sentence_fallback = False
  - mapping_strategy = "simple"
- **WHEN** 处理转录
- **THEN** 输出与 PR3 完全一致
- **AND** 所有 PR3 测试通过

#### Scenario: 渐进式升级
- **GIVEN** 用户逐步启用 PR4 功能
- **WHEN** 首先启用 enable_per_sentence_fallback
- **THEN** 仅改变回退粒度，其他行为不变
- **AND** 回归测试通过

## Non-Functional Requirements

### NFR-1: Performance
- Embedding 计算应支持批量处理（batch_size=32）
- Embedding 结果应缓存避免重复计算
- 单个 chunk 处理时间 < 30 秒（不包括 LLM 调用时间）

### NFR-2: Reliability
- 任何 Mapper 失败都应有明确错误信息
- 回退逻辑应有完整的历史记录
- 置信度计算应处理所有缺失特征

### NFR-3: Maintainability
- Mapper、ConfidenceCalculator、Fallback 职责清晰分离
- 所有边界情况有对应测试
- 设计文档完整

## Data Structures

```python
@dataclass
class MappingInfo:
    """映射信息"""
    quality: MappingQuality  # HIGH / MEDIUM / LOW
    method: MappingMethod    # EXACT / EMBEDDING / POSITION
    trace: Dict[str, Any]
    embedding_similarity: Optional[float] = None

@dataclass
class FallbackInfo:
    """回退信息"""
    level: FallbackLevel  # NONE / SENTENCE / CHUNK / FINAL
    reason: Optional[str]
    history: List[str]

@dataclass
class ConfidenceBreakdown:
    """置信度分解"""
    total: float
    embedding_similarity: Optional[float]
    length_ratio: Optional[float]
    llm_metadata: Optional[float]

@dataclass
class SentenceMappingResult:
    """单句映射结果"""
    sentence_index: int
    enhanced_text: str
    embedding_similarity: Optional[float]
    mapping_quality: MappingQuality
```

## Configuration

```python
@dataclass
class LLMEnhancerConfig:
    # PR3 字段
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    fallback_on_error: bool = True

    # PR4 新增字段
    enable_per_sentence_fallback: bool = False  # 单句回退开关
    confidence_threshold: float = 0.6           # 置信度阈值
    mapping_strategy: str = "hybrid"            # 映射策略
    embedding_similarity_threshold: float = 0.7  # 相似度阈值
    strict_json_mode: bool = False              # JSON 解析模式
```

## Testing Strategy

### 单元测试
- 各 Mapper 独立测试
- ConfidenceCalculator 各种特征组合测试
- Fallback 逻辑测试

### 集成测试
- 端到端混合映射流程
- 边界情况（句子合并、拆分、乱序）
- PR3 兼容性测试

### 回归测试
- PR3 行为回归测试
- 默认配置输出一致性验证
