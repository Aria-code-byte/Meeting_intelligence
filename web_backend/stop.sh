#!/bin/bash
# Jinni 会议精灵 - 停止服务脚本
# ===============================

echo "🛑 停止 Jinni 会议精灵服务..."
echo ""

# 从 PID 文件读取并停止
if [ -f ".api_pid" ]; then
    API_PID=$(cat .api_pid)
    if ps -p $API_PID > /dev/null 2>&1; then
        kill $API_PID
        echo "✅ 后端服务已停止 (PID: $API_PID)"
    fi
    rm -f .api_pid
fi

if [ -f ".frontend_pid" ]; then
    FRONTEND_PID=$(cat .frontend_pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo "✅ 前端服务已停止 (PID: $FRONTEND_PID)"
    fi
    rm -f .frontend_pid
fi

# 额外检查：杀死可能残留的进程
pkill -f "uvicorn main:app" 2>/dev/null && echo "✅ 清理残留后端进程"
pkill -f "streamlit run app.py" 2>/dev/null && echo "✅ 清理残留前端进程"

echo ""
echo "✅ 所有服务已停止"
