#!/bin/bash
# AI Meeting Assistant - 启动脚本
# FastAPI 后端 + React 前端

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/web_backend/react-ui"

echo ""
echo "========================================"
echo "  AI Meeting Assistant"
echo "========================================"
echo ""
echo "正在启动服务..."
echo ""

# 检查虚拟环境
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[错误] 虚拟环境不存在"
    echo "       请先创建: python3 -m venv .venv"
    exit 1
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 启动后端 (端口 8000)
echo "[1/2] 启动后端服务 (端口 8000)..."
cd "$BACKEND_DIR"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端 (端口 5173)
echo "[2/2] 启动前端服务 (端口 5173)..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "📊 后端: http://localhost:8000"
echo "🎨 前端: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 等待信号
wait
