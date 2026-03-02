# PR4: 高精度语义增强模块 - 任务清单

**⏸️ STATUS: PAUSED** (2026-03-02)

**暂停说明**:
- 以下任务已暂停，不在 MVP 范围内
- 已完成任务（打勾）保留，作为设计参考
- 将在 MVP Completion 完成后重新评估

---

## 1. 核心数据结构 (types.py)
- [x] 1.1 定义枚举类型（MappingQuality, FallbackLevel, MappingMethod）
- [x] 1.2 定义 MappingInfo 结构
- [x] 1.3 定义 FallbackInfo 结构
- [x] 1.4 定义 ConfidenceBreakdown 结构
- [x] 1.5 定义 SentenceMappingResult
- [x] 1.6 定义 MultiRoundMetadata 和 MultiRoundResult
- [PAUSED] 1.7 添加类型验证函数

## 2. 映射引擎 (mapper.py)
- [PAUSED] 2.1 实现 SentenceMapper 抽象基类
- [PAUSED] 2.2 实现 ExactMapper（JSON 精确匹配）
- [PAUSED] 2.3 实现 EmbeddingMapper（相似度匹配）
  - [PAUSED] 2.3.1 句子分割逻辑
  - [PAUSED] 2.3.2 Embedding 批量计算（带缓存）
  - [PAUSED] 2.3.3 相似度矩阵构建
  - [PAUSED] 2.3.4 匈牙利算法/贪心匹配
  - [PAUSED] 2.3.5 顺序一致性检查
  - [PAUSED] 2.3.6 阈值过滤
- [PAUSED] 2.4 实现 PositionMapper（位置回退，复用 PR3 逻辑）
- [PAUSED] 2.5 实现 HybridMapper（三级优先级策略）
- [PAUSED] 2.6 实现 create_mapper 工厂函数

## 3. 置信度计算器 (confidence.py)
- [PAUSED] 3.1 实现 calculate_length_ratio_score
- [PAUSED] 3.2 实现 ConfidenceCalculator 类
- [PAUSED] 3.3 实现多特征加权计算
- [PAUSED] 3.4 实现动态权重重归一
- [PAUSED] 3.5 添加 LLM 元数据解析

## 4. 回退引擎 (fallback.py)
- [PAUSED] 4.1 实现 SentenceCandidate 结构
- [PAUSED] 4.2 实现 EnhancedSentence 结构（扩展 PR3）
- [PAUSED] 4.3 实现 FallbackEngine 类
- [PAUSED] 4.4 实现单句回退逻辑
- [PAUSED] 4.5 实现 apply_fallback 函数
- [PAUSED] 4.6 添加回退历史记录

## 5. 模块导出 (__init__.py)
- [x] 5.1 导出 PR4 类型
- [x] 5.2 导出 PR4 类和函数
- [x] 5.3 更新 __all__ 列表

## 6. 测试覆盖
- [PAUSED] 6.1 test_mapper/test_exact_mapper.py
  - [PAUSED] JSON 格式正确
  - [PAUSED] JSON 格式错误触发降级
  - [PAUSED] sentence_index 越界处理
- [PAUSED] 6.2 test_mapper/test_position_mapper.py
  - [PAUSED] 标点分割正确性
  - [PAUSED] 位置映射正确性
  - [PAUSED] 边界情况（空字符串、单句等）
- [PAUSED] 6.3 test_mapper/test_embedding_mapper.py
  - [PAUSED] 一对一匹配正确性
  - [PAUSED] 阈值过滤
  - [PAUSED] 顺序一致性检查
  - [PAUSED] 匹配率低时降级
- [PAUSED] 6.4 test_confidence.py
  - [PAUSED] length_ratio_score 计算
  - [PAUSED] 多特征加权
  - [PAUSED] 权重重归一
  - [PAUSED] 缺失特征处理
- [PAUSED] 6.5 test_fallback.py
  - [PAUSED] 单句回退触发条件
  - [PAUSED] 回退历史记录
  - [PAUSED] 置信度阈值判断
- [PAUSED] 6.6 test_regression/test_pr3_pr4_compatibility.py
  - [PAUSED] 默认配置输出一致性
  - [PAUSED] PR3 行为回归

## 7. 文档
- [x] 7.1 创建架构设计文档
- [PAUSED] 7.2 添加 API 文档注释
- [PAUSED] 7.3 更新 MEMORY.md

## 8. 集成与验证
- [PAUSED] 8.1 集成到 enhanced_builder.py
- [PAUSED] 8.2 端到端测试
- [PAUSED] 8.3 性能测试
- [PAUSED] 8.4 CI/CD 配置
