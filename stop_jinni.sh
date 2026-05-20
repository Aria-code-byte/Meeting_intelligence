#!/bin/bash
# ============================================================
# Jinni Meeting Intelligence - 停止服务脚本
# ============================================================

echo ""
echo "========================================"
echo "  Jinni Meeting Intelligence"
echo "  停止服务"
echo "========================================"
echo ""

# 从 PID 文件读取
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "[*] 停止后端服务 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "[*] 停止前端服务 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm .frontend.pid
fi

# 强制清理端口（包括可能的 Vite/node 进程）
echo "[*] 清理端口占用..."
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true

sleep 2

echo ""
echo "========================================"
echo "  服务已停止"
echo "========================================"
echo ""
