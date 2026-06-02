# 演示会议导入说明

## 📋 演示会议信息

**会议标题**：V2.0 产品需求讨论会  
**会议时长**：1小时15分钟  
**参与人数**：4人  
**转录条数**：10条（带时间戳和发言人）  
**总结内容**：完整的结构化总结（包含会议背景、需求讨论、技术方案、决策事项、行动项）

---

## 🚀 导入方法（3种）

### 方法一：浏览器控制台导入（推荐）

1. 打开 JINNI 会议精灵：http://localhost:5173
2. 按 `F12` 打开浏览器开发者工具
3. 切换到 `Console`（控制台）标签
4. 复制以下代码并粘贴到控制台：

```javascript
fetch('/import-demo-meeting.js').then(r=>r.text()).then(eval)
```

5. 按回车执行，页面会自动刷新
6. 刷新后进入"会议库"即可看到演示会议

### 方法二：手动复制粘贴

1. 打开项目文件：`/web_backend/react-ui/public/import-demo-meeting.js`
2. 复制文件中的所有代码
3. 打开 http://localhost:5173
4. 按 `F12` 打开开发者工具，切换到 Console 标签
5. 粘贴代码并按回车执行
6. 页面会自动刷新

### 方法三：使用数据文件（开发者）

```typescript
import { demoMeeting } from '/src/data/demoMeeting';

// 在组件中使用
const meetings = JSON.parse(localStorage.getItem('jinni_meetings') || '[]');
meetings.push(demoMeeting);
localStorage.setItem('jinni_meetings', JSON.stringify(meetings));
```

---

## 📊 演示会议内容

### 参与人员
- 张伟（产品经理）
- 李娜（UI 设计师）
- 王强（后端开发）
- 赵敏（前端开发）

### 讨论内容
1. 移动端性能优化（提升30%加载速度）
2. 数据导出功能（Excel/CSV格式）
3. 用户权限管理（角色管理功能）

### 输出内容
- ✅ 带时间戳的说话人转录
- ✅ 完整的会议文字稿
- ✅ 结构化总结（6个部分）
- ✅ 4个行动项（含负责人和截止日期）

---

## 🎯 查看演示会议

导入成功后：

1. 进入**会议库**页面
2. 找到"V2.0 产品需求讨论会"
3. 点击进入会议详情
4. 可以查看：
   - 📝 原始转录（带说话人和时间戳）
   - 📋 结构化总结
   - ✅ 行动项列表

---

## 🔧 重新导入

如果需要重新导入或更新演示数据：

```javascript
// 在控制台执行
localStorage.removeItem('jinni_meetings');
location.reload();
// 然后重新执行导入脚本
```

---

## 📝 注意事项

- 演示会议数据保存在浏览器 localStorage 中
- 清除浏览器数据会删除演示会议
- 可以多次导入，会自动更新已存在的演示会议

---

**创建日期**：2024-06-01  
**适用版本**：JINNI 会议精灵 v1.0+
