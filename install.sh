#!/bin/bash
# =============================================================================
# AI 会议智能助手 - 自动安装脚本 (Linux/macOS)
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印横幅
print_banner() {
    echo -e "${BLUE}"
    echo "============================================================================"
    echo "  AI 会议智能助手 - 自动安装脚本"
    echo "  AI Meeting Assistant - Installation Script"
    echo "============================================================================"
    echo -e "${NC}"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/debian_version ]; then
            DISTRO="debian"
        elif [ -f /etc/redhat-release ]; then
            DISTRO="redhat"
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        print_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    print_success "检测到操作系统: $OS"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查 Python 版本
check_python() {
    print_info "检查 Python 版本..."

    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

        print_success "找到 Python $PYTHON_VERSION"

        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
            print_error "Python 版本过低，需要 3.10 或更高版本"
            print_info "当前版本: $PYTHON_VERSION"
            exit 1
        fi

        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_VERSION=$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

        print_success "找到 Python $PYTHON_VERSION"

        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
            print_error "Python 版本过低，需要 3.10 或更高版本"
            exit 1
        fi

        PYTHON_CMD="python"
    else
        print_error "未找到 Python，请先安装 Python 3.10+"
        exit 1
    fi
}

# 检查 Node.js
check_nodejs() {
    print_info "检查 Node.js..."

    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        print_success "找到 Node.js $(node --version)"

        if [ "$NODE_VERSION" -lt 18 ]; then
            print_warning "Node.js 版本过低（推荐 18+），当前版本: $(node --version)"
            read -p "是否继续安装？(y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        print_error "未找到 Node.js，请先安装 Node.js 18+"
        print_info "访问 https://nodejs.org/ 下载安装"
        exit 1
    fi
}

# 检查 FFmpeg
check_ffmpeg() {
    print_info "检查 FFmpeg..."

    if command_exists ffmpeg; then
        print_success "找到 FFmpeg $(ffmpeg -version 2>&1 | head -n1)"
        FFMPEG_INSTALLED=true
    else
        print_warning "未找到 FFmpeg"
        FFMPEG_INSTALLED=false
    fi
}

# 安装 FFmpeg
install_ffmpeg() {
    if [ "$FFMPEG_INSTALLED" = true ]; then
        return
    fi

    print_info "安装 FFmpeg..."

    if [ "$OS" == "linux" ]; then
        if [ "$DISTRO" == "debian" ]; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        elif [ "$DISTRO" == "redhat" ]; then
            sudo yum install -y ffmpeg
        else
            print_error "无法自动安装 FFmpeg，请手动安装"
            exit 1
        fi
    elif [ "$OS" == "macos" ]; then
        if command_exists brew; then
            brew install ffmpeg
        else
            print_error "请先安装 Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    fi

    print_success "FFmpeg 安装完成"
}

# 创建虚拟环境
create_venv() {
    print_info "创建 Python 虚拟环境..."

    if [ -d ".venv" ]; then
        print_warning "虚拟环境已存在，跳过创建"
    else
        $PYTHON_CMD -m venv .venv
        print_success "虚拟环境创建完成"
    fi
}

# 激活虚拟环境
activate_venv() {
    print_info "激活虚拟环境..."
    source .venv/bin/activate
    print_success "虚拟环境已激活"
}

# 升级 pip
upgrade_pip() {
    print_info "升级 pip..."
    pip install --upgrade pip -q
    print_success "pip 升级完成"
}

# 安装后端依赖
install_backend_deps() {
    print_info "安装后端依赖..."

    if [ -f "backend/requirements.txt" ]; then
        pip install -r backend/requirements.txt -q
        print_success "后端依赖安装完成"
    else
        print_error "未找到 backend/requirements.txt"
        exit 1
    fi
}

# 配置环境变量
setup_env() {
    print_info "配置环境变量..."

    if [ ! -f "backend/.env" ]; then
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            print_success "已创建 backend/.env（使用默认配置）"
            print_warning "请编辑 backend/.env 配置您的 API Key"
        else
            print_warning "未找到 backend/.env.example"
        fi
    else
        print_info "backend/.env 已存在，跳过"
    fi
}

# 安装前端依赖
install_frontend_deps() {
    print_info "安装前端依赖..."

    if [ -d "web_backend/react-ui" ]; then
        cd web_backend/react-ui

        if command_exists npm; then
            npm install
            print_success "前端依赖安装完成"
        else
            print_error "未找到 npm"
            exit 1
        fi

        cd ../..
    else
        print_error "未找到 web_backend/react-ui 目录"
        exit 1
    fi
}

# 创建启动脚本
create_start_scripts() {
    print_info "创建启动脚本..."

    # Linux/macOS 启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash
# 启动 AI 会议智能助手

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "启动 AI 会议智能助手..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境不存在，请先运行 install.sh"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 启动后端（后台运行）
echo "启动后端服务..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > .backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务..."
cd web_backend/react-ui
npm run dev > ../../.frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../../.frontend.pid
echo "前端 PID: $FRONTEND_PID"
cd ../..

echo ""
echo "=========================================="
echo "  AI 会议智能助手已启动！"
echo "=========================================="
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "=========================================="
echo ""
echo "停止服务: ./stop.sh"
echo "查看日志: tail -f .backend.log 或 .frontend.log"
EOF

    chmod +x start.sh

    # 停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash
# 停止 AI 会议智能助手

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "停止 AI 会议智能助手..."

# 停止后端
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "已停止后端 (PID: $BACKEND_PID)"
    fi
    rm .backend.pid
fi

# 停止前端
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo "已停止前端 (PID: $FRONTEND_PID)"
    fi
    rm .frontend.pid
fi

echo "服务已停止"
EOF

    chmod +x stop.sh

    print_success "启动脚本创建完成 (start.sh, stop.sh)"
}

# 运行测试
run_tests() {
    print_info "运行测试套件..."

    if [ "$1" == "--skip-tests" ]; then
        print_warning "跳过测试"
        return
    fi

    read -p "是否运行测试套件？(Y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_warning "跳过测试"
        return
    fi

    print_info "运行测试..."
    pytest tests/ -v --tb=short

    if [ $? -eq 0 ]; then
        print_success "所有测试通过！"
    else
        print_warning "部分测试失败，请检查"
    fi
}

# 打印安装完成信息
print_completion() {
    echo ""
    echo -e "${GREEN}============================================================================"
    echo "  安装完成！"
    echo "============================================================================${NC}"
    echo ""
    echo "下一步操作："
    echo ""
    echo "1. 配置环境变量（如果需要使用 AI 功能）："
    echo "   编辑 backend/.env 文件"
    echo ""
    echo "2. 启动服务："
    echo "   ./start.sh"
    echo ""
    echo "3. 访问应用："
    echo -e "   ${BLUE}http://localhost:5173${NC}"
    echo ""
    echo "4. 停止服务："
    echo "   ./stop.sh"
    echo ""
    echo -e "${YELLOW}注意: 首次运行会下载 Whisper 模型，可能需要较长时间${NC}"
    echo ""
}

# 主安装流程
main() {
    print_banner

    # 检测环境
    detect_os
    check_python
    check_nodejs
    check_ffmpeg

    # 安装依赖
    install_ffmpeg
    create_venv
    activate_venv
    upgrade_pip
    install_backend_deps
    setup_env
    install_frontend_deps

    # 创建脚本
    create_start_scripts

    # 运行测试
    run_tests "$1"

    # 完成
    print_completion
}

# 运行主程序
main "$@"
