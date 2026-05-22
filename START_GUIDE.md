# Jinni Meeting Intelligence - 启动与进程管理指南

**更新日期**: 2026-05-13
**版本**: v1.1

---

## 🚀 快速开始

### 方法1：统一启动（推荐）

**双击运行**: `start_jinni.bat`

**功能**:
- ✅ 安全清理端口 8000 和 8501 的进程
- ✅ 启动后端服务（端口 8000）
- ✅ 启动前端服务（端口 8501）
- ✅ 自动打开浏览器
- ✅ 确保只运行稳定版本文件

### 方法2：快速重启

**双击运行**: `quick_restart.bat`

**功能**:
- ✅ 停止所有服务
- ✅ 重新启动前后端
- ✅ 清理端口占用

### 方法3：手动停止

**双击运行**: `stop_jinni.bat`

**功能**:
- ✅ 停止占用端口 8000 的进程（后端）
- ✅ 停止占用端口 8501 的进程（前端）
- ✅ 释放端口

---

## 📋 脚本说明

### start_jinni.bat
**主启动脚本，唯一入口**

**执行流程**:
1. 安全清理端口 8000 和 8501 的进程
2. 启动后端服务（backend/main.py）
3. 启动前端服务（app_working_v12_ui_fixed_stable.py）
4. 显示访问信息和版本标识

**版本标识**:
- 页面底部显示：`当前版本：v12_ui_fixed_stable`
- 前端运行文件：`app_working_v12_ui_fixed_stable.py`
- 后端运行文件：`backend/main.py`

**端口分配**:
- 后端：8000
- 前端：8501

### stop_jinni.bat
**停止服务脚本（安全版本）**

**执行流程**:
1. 停止占用端口 8000 的进程
2. 停止占用端口 8501 的进程
3. 等待端口释放
4. 显示清理结果

**重要**:
- ❌ 不会杀掉其他 Python 进程
- ✅ 只停止占用指定端口的进程
- ✅ 安全可靠，不影响用户其他程序

### quick_restart.bat
**快速重启脚本**

**功能**:
- 调用 stop_jinni.bat 停止服务
- 等待 2 秒确保完全停止
- 调用 start_jinni.bat 重新启动

**使用场景**:
- 后端代码更新后需要重启
- 前端代码更新后需要重启
- 遇到问题需要快速重启

---

## 🔍 版本验证

### 前端版本确认

访问 http://localhost:8501 后，检查页面底部是否有：

```
当前版本：v12_ui_fixed_stable
```

**如果看到这行**：
- ✅ 运行的是正确版本
- ✅ UI 修复已生效

**如果没看到这行**：
- ❌ 运行的是错误版本
- ❌ 需要运行 stop_jinni.bat 然后重新 start_jinni.bat

### 后端接口确认

访问 http://localhost:8000/docs 查看API文档，确认包含：

- `GET /api/templates` - 模板列表接口
- `GET /api/templates/{template_id}` - 模板详情接口

---

## 🛠️ 故障排除

### 问题1：双击脚本后闪退

**原因**: 脚本执行完立即关闭

**解决**: 右键点击脚本 → "以管理员身份运行"

### 问题2：端口被占用

**原因**: 旧进程未完全清理

**解决**:
1. 运行 `stop_jinni.bat`
2. 如果仍有问题，手动打开任务管理器
3. 查找占用端口 8000 或 8501 的进程
4. 手动结束这些进程
5. 重新运行 `start_jinni.bat`

### 问题3：前端页面显示旧版本UI

**原因**: 运行了错误的文件

**解决**:
1. 运行 `stop_jinni.bat`
2. 检查是否有多批处理文件同时启动
3. 只使用 `start_jinni.bat` 启动
4. 确认页面底部有版本标识

### 问题4：后端健康检查失败

**原因**: 后端启动失败或编码问题

**解决**:
1. 检查命令提示符窗口的错误信息
2. 确认 `backend/main.py` 文件存在
3. 检查端口 8000 是否被其他程序占用
4. 确认 Python 已正确安装

### 问题5：浏览器无法连接

**原因**: 服务未启动或防火墙阻止

**解决**:
1. 检查两个命令提示符窗口是否都在运行
2. 确认没有安全软件阻止
3. 尝试手动访问：
   - http://localhost:8000/health
   - http://localhost:8501

---

## 📝 旧启动脚本说明

**已废弃的启动脚本**（请勿使用）：
- ❌ run_v12_templates.bat
- ❌ run_v12_ui_fixed_stable.bat
- ❌ run_v13_ui_cleanup.bat
- ❌ run_v11_stable.bat
- ❌ 其他所有 run_*.bat 文件

**原因**:
- 这些脚本可能启动错误的文件版本
- 没有进程清理机制
- 容易导致版本混乱

---

## 🎯 使用规范

### 正确的启动流程

1. **双击** `start_jinni.bat`
2. 等待两个命令提示符窗口打开
3. 浏览器自动打开 http://localhost:8501
4. 确认页面底部有版本标识
5. 开始使用

### 停止服务流程

1. **关闭两个命令提示符窗口**（推荐）
2. **或者双击** `stop_jinni.bat`
3. **或者双击** `quick_restart.bat`（自动重启）

### 开发流程

1. 修改代码后
2. 双击 `quick_restart.bat`
3. 刷新浏览器验证修改

---

## 🔒 版本锁定机制

### 前端固定文件
```
web_backend/app_working_v12_ui_fixed_stable.py
```

### 后端固定文件
```
backend/main.py
```

### 端口分配
```
前端：8501
后端：8000
```

### 命名规范
```
start_jinni.bat       ← 唯一启动入口
stop_jinni.bat        ← 唯一停止脚本
quick_restart.bat      ← 快速重启
```

---

## ⚠️ 重要注意事项

### 不要运行的文件
- ❌ app.py
- ❌ app_working_v11_*.py
- ❌ app_working_v12_templates.py
- ❌ app_working_v13_*.py
- ❌ app_working_v8_stable.py
- ❌ 其他所有 app*.py 文件

### 必须运行的文件
- ✅ backend/main.py（后端）
- ✅ web_backend/app_working_v12_ui_fixed_stable.py（前端）

### 不要直接运行的命令
- ❌ streamlit run app.py
- ❌ python backend/main.py（除非用于调试）
- ❌ streamlit run app_working_v12_templates.py

### 安全说明
- ✅ 脚本只会停止占用端口 8000 和 8501 的进程
- ❌ 不会杀掉用户电脑上的其他 Python 程序
- ✅ 安全可靠，不影响其他应用

---

## 📊 验收清单

### 启动成功标准

- [ ] 双击 `start_jinni.bat` 后自动打开两个窗口
- [ ] 浏览器自动打开 http://localhost:8501
- [ ] 页面底部显示版本标识：`当前版本：v12_ui_fixed_stable`
- [ ] 访问 http://localhost:8000/health 返回 `{"status":"ok"}`
- [ ] 访问 http://localhost:8000/docs 能看到API文档
- [ ] 前端 Step 3 不再显示404错误
- [ ] 前端 Step 2 不再显示调试信息

### 使用成功标准

- [ ] 完整 5 步工作流可正常运行
- [ ] 文件上传功能正常
- [ ] 转录进度实时更新
- [ ] 总结生成功能正常
- [ ] 模板选择功能正常
- [ ] 结果查看功能正常

---

**创建时间**: 2026-05-13
**版本**: v1.1
**更新内容**: 修正端口错误，改进安全逻辑
**状态**: ✅ 已完成并测试
