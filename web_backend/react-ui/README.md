# Jinni AI - React Dashboard UI

这是基于 React + TypeScript + Tailwind CSS 构建的现代化仪表盘界面。

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式系统
- **Vite** - 构建工具
- **Lucide React** - 图标库

## 项目结构

```
react-ui/
├── src/
│   ├── components/       # 可复用组件
│   │   ├── ActionItemCard.tsx
│   │   ├── RecentMeetingCard.tsx
│   │   ├── Sidebar.tsx
│   │   ├── StatCard.tsx
│   │   ├── StatusBadge.tsx
│   │   ├── TemplateCard.tsx
│   │   └── TopNav.tsx
│   ├── pages/           # 页面组件
│   │   ├── DashboardPage.tsx
│   │   ├── MeetingLibraryPage.tsx
│   │   ├── ProcessingPage.tsx
│   │   ├── SummaryDetailPage.tsx
│   │   └── TemplatePage.tsx
│   ├── App.tsx          # 主应用组件
│   ├── main.tsx         # 应用入口
│   └── index.css        # 全局样式
├── index.html           # HTML 模板
├── package.json         # 项目配置
├── tsconfig.json        # TypeScript 配置
├── vite.config.ts       # Vite 配置
└── tailwind.config.js   # Tailwind CSS 配置
```

## 快速开始

### 安装依赖

```bash
cd react-ui
npm install
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:5173` 启动。

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 功能页面

### 1. 首页 (Dashboard)
- 文件上传区域
- 统计卡片展示
- 最近会议列表

### 2. 会议库 (Meeting Library)
- 会议列表表格
- 搜索和筛选功能
- 分页导航

### 3. 模板管理 (Templates)
- 模板卡片网格
- 内置/自定义模板分类
- 模板操作功能

### 4. AI 总结详情 (Summary Detail)
- 会议概要展示
- 关键决策卡片
- 待办事项列表
- 完整文字稿查看

### 5. 处理中页面 (Processing)
- 实时进度显示
- 转录步骤指示
- 实时转录预览

## 设计规范

### 颜色系统

- **主色**: #061B35 (深海军蓝)
- **背景**: #EEF8FC (浅蓝灰)
- **边框**: #D6E1EA (浅灰蓝)
- **成功**: #10B981 (绿色)
- **警告**: #FFA54D (橙色)
- **错误**: #FF6B6B (红色)

### 组件规范

- **卡片圆角**: 1rem - 1.5rem
- **按钮圆角**: 0.5rem - 0.75rem
- **阴影**: 轻微柔和阴影
- **间距**: 基于 4px 栅格系统

## 与后端集成

当前版本使用 Mock 数据。要连接到后端 API:

1. 在组件中添加 API 调用
2. 使用 `fetch` 或 Axios 与后端通信
3. 后端 API 地址: `http://localhost:8000`

## 开发说明

### 添加新页面

1. 在 `src/pages/` 创建新页面组件
2. 在 `App.tsx` 中添加路由逻辑
3. 在 `Sidebar.tsx` 中添加导航项

### 修改样式

- 全局样式: `src/index.css`
- Tailwind 配置: `tailwind.config.js`
- 组件样式: 使用 Tailwind 类名

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge

## 许可证

MIT
