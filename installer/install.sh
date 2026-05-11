#!/bin/bash
#
# AI Meeting Assistant - 安装脚本
# 支持: Linux, macOS
#
# 用法: bash install.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 打印带颜色的消息
print_header() {
    echo -e "${BLUE}"
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查 Python 版本
check_python() {
    print_header "检查 Python 版本"

    if ! command_exists python3; then
        print_error "未找到 python3"
        print_info "请安装 Python 3.10 或更高版本"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    print_success "找到 Python $PYTHON_VERSION"

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        print_error "Python 版本过低（需要 3.10+）"
        exit 1
    fi

    print_success "Python 版本满足要求"
}

# 检查 FFmpeg
check_ffmpeg() {
    print_header "检查 FFmpeg"

    if command_exists ffmpeg; then
        FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n1)
        print_success "FFmpeg 已安装: $FFPEG_VERSION"
        return 0
    fi

    print_warning "FFmpeg 未安装"

    # 尝试自动安装
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "尝试自动安装 FFmpeg..."
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
            print_success "FFmpeg 安装成功"
        elif command_exists yum; then
            sudo yum install -y ffmpeg
            print_success "FFmpeg 安装成功"
        else
            print_error "无法自动安装 FFmpeg"
            print_info "请手动安装: sudo apt-get install ffmpeg"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "检测到 macOS"
        if command_exists brew; then
            print_info "使用 Homebrew 安装 FFmpeg..."
            brew install ffmpeg
            print_success "FFmpeg 安装成功"
        else
            print_error "未找到 Homebrew"
            print_info "请先安装 Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    fi
}

# 创建虚拟环境
create_venv() {
    print_header "创建虚拟环境"

    cd "$PROJECT_ROOT"

    if [ -d ".venv" ]; then
        print_warning "虚拟环境已存在"
        read -p "是否重新创建？[y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .venv
            print_info "已删除旧虚拟环境"
        else
            print_info "使用现有虚拟环境"
            return 0
        fi
    fi

    python3 -m venv .venv
    print_success "虚拟环境创建成功"
}

# 激活虚拟环境
activate_venv() {
    print_header "激活虚拟环境"

    source "$PROJECT_ROOT/.venv/bin/activate"
    print_success "虚拟环境已激活"
}

# 升级 pip
upgrade_pip() {
    print_header "升级 pip"

    python -m pip install --upgrade pip
    print_success "pip 已升级到最新版本"
}

# 安装依赖
install_dependencies() {
    print_header "安装 Python 依赖"

    cd "$PROJECT_ROOT"

    print_info "正在安装依赖包..."
    pip install -r requirements.txt

    print_success "依赖安装完成"
}

# 安装额外依赖
install_extra_deps() {
    print_header "安装额外依赖"

    # tqdm（进度条）
    pip install tqdm
    print_success "tqdm 已安装"

    # python-dotenv（环境变量）
    pip install python-dotenv
    print_success "python-dotenv 已安装"
}

# 运行配置向导
run_setup_wizard() {
    print_header "配置向导"

    cd "$PROJECT_ROOT"

    print_info "启动配置向导..."
    python installer/setup_wizard.py
}

# 创建启动脚本
create_launch_scripts() {
    print_header "创建启动脚本"

    cd "$PROJECT_ROOT"

    # CLI 启动脚本
    cat > run.sh << 'EOF'
#!/bin/bash
# AI Meeting Assistant - 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 激活虚拟环境
source "$SCRIPT_DIR/.venv/bin/activate"

# 检查是否首次运行
if [ -f "$SCRIPT_DIR/.config/preferences.json" ]; then
    INTERFACE=$(python -c "import json; print(json.load(open('$SCRIPT_DIR/.config/preferences.json'))['interface_mode'])")

    if [ "$INTERFACE" = "web" ]; then
        cd "$SCRIPT_DIR/web_backend"
        streamlit run app.py --server.port 8501
    else
        python -m meeting_intelligence.cli
    fi
else
    # 首次运行，默认使用 CLI
    python -m meeting_intelligence.cli
fi
EOF

    chmod +x run.sh
    print_success "创建 run.sh"

    # 桌面快捷方式（仅 Linux）
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        cat > ~/Desktop/ai-meeting-assistant.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AI Meeting Assistant
Comment=AI-powered meeting transcription and summarization
Exec=$PROJECT_ROOT/run.sh
Icon=$PROJECT_ROOT/docs/icon.png
Terminal=true
Categories=Office;AudioVideo;
EOF
        chmod +x ~/Desktop/ai-meeting-assistant.desktop
        print_success "创建桌面快捷方式"
    fi
}

# 打印完成信息
print_completion() {
    print_header "安装完成"

    echo ""
    print_success "AI Meeting Assistant 已成功安装！"
    echo ""
    echo "🚀 开始使用："
    echo "   方式 1: ./run.sh"
    echo "   方式 2: source .venv/bin/activate && python -m meeting_intelligence.cli"
    echo ""
    echo "📖 文档: README.md"
    echo "🐛 问题反馈: GitHub Issues"
    echo ""
}

# 主函数
main() {
    echo ""
    print_header "AI Meeting Assistant - 安装程序"
    echo ""
    print_info "开始安装..."
    echo ""

    # 检查依赖
    check_python
    check_ffmpeg

    # 设置 Python 环境
    create_venv
    activate_venv
    upgrade_pip

    # 安装依赖
    install_dependencies
    install_extra_deps

    # 配置
    run_setup_wizard

    # 创建启动脚本
    create_launch_scripts

    # 完成
    print_completion
}

# 运行主函数
main "$@"
