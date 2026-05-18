# React UI 已启动成功！✅

## 访问地址

```
http://localhost:5173/
```

## 当前状态

- ✅ 依赖已安装
- ✅ 开发服务器已启动
- ✅ 端口 5173 正在监听

## 如果无法访问

### 检查1：确认服务器正在运行

在 WSL 终端中应该看到：
```
VITE v5.4.21  ready in 904 ms
➜  Local:   http://localhost:5173/
```

### 检查2：在浏览器中打开

1. 打开浏览器（Chrome/Edge/Firefox）
2. 访问：`http://localhost:5173/`
3. 如果自动打开没有生效，手动输入地址

### 检查3：WSL 端口转发

如果使用 WSL，可能需要端口转发：

**Windows PowerShell（管理员身份）运行：**
```powershell
netsh interface portproxy show all
```

如果有 `127.0.0.1` 的转发，先删除：
```powershell
netsh interface portproxy delete v4tov4 listenport=5173 listenaddress=127.0.0.1
```

然后重新运行服务器。

## 停止服务器

在运行 `npm run dev` 的终端按 `Ctrl + C`

## 重新启动

```bash
cd /mnt/d/projects/Meeting_intelligence/web_backend/react-ui
npm run dev
```

## 功能说明

启动后可以看到以下页面：

1. **首页** - 上传音频/视频文件，查看统计
2. **会议库** - 查看历史会议记录
3. **模板管理** - 管理总结模板
4. **AI 总结详情** - 查看会议总结和待办事项

点击左侧菜单可以切换不同页面。
