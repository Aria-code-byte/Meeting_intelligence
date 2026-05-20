#!/bin/bash
# ============================================================
# Jinni Meeting Intelligence - 统一启动脚本
# ============================================================
#
# 功能：
# 1. 清理占用端口 8000 和 5173 的进程
# 2. 启动后端服务（端口 8000）
# 3. 启动前端服务（端口 5173）- React + TypeScript + Tailwind
# 4. 使用最新的 React UI 版本
#
# 使用方法：
# chmod +x start_jinni.sh
# ./start_jinni.sh
#
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "  Jinni Meeting Intelligence"
echo "  统一启动脚本 (React UI)"
echo "========================================"
echo ""
echo "[1/5] 清理端口占用..."
echo ""

# ============================================================
# 步骤 1: 安全清理端口占用
# ============================================================

echo "[*] 清理端口 8000（后端）..."
fuser -k 8000/tcp 2>/dev/null || true

echo "[*] 清理端口 5173（前端 React）..."
fuser -k 5173/tcp 2>/dev/null || true

echo "[*] 等待端口释放..."
sleep 2

echo "    端口清理完成"
echo ""

# ============================================================
# 步骤 2: 启动后端服务
# ============================================================

echo "[2/5] 启动后端服务..."
echo ""

source .venv/bin/activate

echo "[*] 后端服务：backend/main.py"
echo "[*] 服务地址：http://localhost:8000"
echo "[*] API 文档：http://localhost:8000/docs"
echo ""

cd backend
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "[*] 后端启动命令已执行 (PID: $BACKEND_PID)"
echo ""

echo "[*] 等待后端初始化..."
sleep 5

echo "[*] 检查后端健康状态..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "    后端服务启动成功"
else
    echo "[!] 警告：后端可能未启动，请检查错误信息"
    echo "[*] 日志文件：logs/backend.log"
fi
echo ""

# ============================================================
# 步骤 3: 启动前端服务（React）
# ============================================================

echo "[3/5] 启动前端服务（React）..."
echo ""

echo "[*] 前端服务：web_backend/react-ui"
echo "[*] 服务地址：http://localhost:5173"
echo "[*] 技术栈：React + TypeScript + Tailwind + Vite"
echo "[*] 上传限制：2GB"
echo ""

cd web_backend/react-ui
nohup npm run dev > ../../logs/react-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

echo "[*] 前端启动命令已执行 (PID: $FRONTEND_PID)"
echo ""

echo "[*] 等待前端初始化（Vite 需要 10-15 秒）..."
sleep 12

echo "[*] 检查前端状态..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "    前端服务启动成功"
else
    echo "[!] 警告：前端可能仍在启动中，请稍后再试"
    echo "[*] 日志文件：logs/react-frontend.log"
    echo "[*] Vite 服务器可能需要更长时间，请检查日志"
fi
echo ""

# ============================================================
# 步骤 4: 显示访问信息
# ============================================================

echo "[4/5] 服务访问信息"
echo ""
echo "========================================"
echo "  前端地址（React UI）"
echo "========================================"
echo ""
echo "  http://localhost:5173"
echo ""
echo "========================================"
echo "  后端地址"
echo "========================================"
echo ""
echo "  http://localhost:8000"
echo "  http://localhost:8000/docs"
echo ""
echo "========================================"
echo "  启动完成！"
echo "========================================"
echo ""
echo "[5/5] 使用说明"
echo ""
echo "1. 在浏览器中访问：http://localhost:5173"
echo "2. React UI 包含：工作台、会议库、模板管理"
echo ""
echo "3. 停止服务："
echo "   - 运行：./stop_jinni.sh"
echo "   - 或执行：fuser -k 8000/tcp && fuser -k 5173/tcp"
echo ""
echo "4. 查看日志："
echo "   - 后端：tail -f logs/backend.log"
echo "   - 前端：tail -f logs/react-frontend.log"
echo ""
echo "========================================"

# 保存 PID 到文件
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid
