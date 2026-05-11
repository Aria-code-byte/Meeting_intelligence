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
