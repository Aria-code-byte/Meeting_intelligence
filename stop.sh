#!/bin/bash
# AI Meeting Assistant - 停止脚本

echo ""
echo "========================================"
echo "  停止 AI Meeting Assistant"
echo "========================================"
echo ""

# 停止后端 (端口 8000)
echo "[1/2] 停止后端服务..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 停止前端 (端口 5173)
echo "[2/2] 停止前端服务..."
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo ""
echo "✅ 服务已停止"
echo ""
