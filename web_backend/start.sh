#!/bin/bash
# Jinni 会议精灵 - 一键启动脚本
# ===============================
# 用于竞赛现场快速部署演示

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🧞 Jinni 会议精灵 - 一键启动                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装"
    exit 1
fi

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  未找到 FFmpeg，音频处理功能将不可用"
    echo "   安装方法: sudo apt-get install ffmpeg"
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
if [ ! -f ".deps_installed" ]; then
    echo "📥 安装依赖..."
    pip install -q -r requirements.txt
    touch .deps_installed
fi

# 初始化项目
if [ ! -f "storage/db/jinni.db" ]; then
    echo "🗄️  初始化数据库..."
    python init_project.py
fi

echo ""
echo "✅ 环境准备完成！"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  启动服务..."
echo "════════════════════════════════════════════════════════════"
echo ""

# 检查端口占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  端口 $1 已被占用，请先关闭占用进程"
        echo "   查找命令: lsof -i :$1"
        return 1
    fi
    return 0
}

# 启动后端
if check_port 8000; then
    echo "🚀 启动 FastAPI 后端 (端口 8000)..."
    python main.py > logs/api.log 2>&1 &
    API_PID=$!
    echo "   PID: $API_PID"
    sleep 2

    # 检查后端是否启动成功
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "   ✅ 后端启动成功"
    else
        echo "   ❌ 后端启动失败，查看日志: logs/api.log"
        exit 1
    fi
else
    echo "⚠️  跳过后端启动（端口 8000 被占用）"
    API_PID=""
fi

echo ""

# 启动前端
if check_port 8501; then
    echo "🎨 启动 Streamlit 前端 (端口 8501)..."
    streamlit run app.py --server.port 8501 > logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   PID: $FRONTEND_PID"
    sleep 2

    echo "   ✅ 前端启动成功"
else
    echo "⚠️  跳过前端启动（端口 8501 被占用）"
    FRONTEND_PID=""
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  🎉 服务启动完成！"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  📱 前端界面: http://localhost:8501"
echo "  📚 API 文档: http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止服务"
echo ""

# 保存 PID 到文件（用于停止脚本）
if [ -n "$API_PID" ]; then
    echo $API_PID > .api_pid
fi
if [ -n "$FRONTEND_PID" ]; then
    echo $FRONTEND_PID > .frontend_pid
fi

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $API_PID $FRONTEND_PID 2>/dev/null; rm -f .api_pid .frontend_pid; echo '✅ 服务已停止'; exit 0" INT TERM

# 保持脚本运行
while true; do
    sleep 1
done
