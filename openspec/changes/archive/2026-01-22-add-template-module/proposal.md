# Change: Add Template Module

## Why

原始会议文档提供了完整的会议记录，但不同用户对会议的关注点不同：
- **产品经理**关注：需求、决策、行动项
- **开发者**关注：技术细节、实现方案
- **设计师**关注：用户体验、视觉相关
- **高管**关注：战略方向、资源投入

用户需要一种方式来定义"我关心什么"，让 AI 根据这个角度生成总结。

**模板是产品的"灵魂模块"**，它定义了会议如何被重新体验。

## What Changes

- 新增 `template/` 模块
- 定义 `UserTemplate` 类型（角色、角度、重点关注内容）
- 实现默认模板库
- 实现模板验证和加载
- 支持自定义用户模板

## Impact

- Affected specs: 新增 `template` 规范
- Affected code:
  - 新增 `template/` 目录
  - 新增 `template/types.py` (UserTemplate, TemplateSection)
  - 新增 `template/defaults.py` (默认模板库)
  - 新增 `template/validation.py` (模板验证)
  - 新增 `data/templates/` 数据目录
- Dependencies: 暂无（模板系统独立于其他模块）
