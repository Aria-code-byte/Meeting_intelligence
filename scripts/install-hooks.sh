#!/bin/bash
# =============================================================================
# Git Hooks 安装脚本
# 用途: 将项目钩子安装到 .git/hooks/ 目录
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}         Git Hooks 安装脚本${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_SOURCE="$PROJECT_ROOT/.githooks"
HOOKS_DEST="$PROJECT_ROOT/.git/hooks"

echo "项目根目录: $PROJECT_ROOT"
echo "钩子源目录: $HOOKS_SOURCE"
echo "钩子目标目录: $HOOKS_DEST"
echo ""

# 创建钩子目录
mkdir -p "$HOOKS_SOURCE"

# =============================================================================
# 复制现有钩子到模板目录
# =============================================================================
echo "设置钩子模板..."

# 如果 .git/hooks/pre-commit 存在，复制到模板目录
if [ -f "$HOOKS_DEST/pre-commit" ]; then
    cp "$HOOKS_DEST/pre-commit" "$HOOKS_SOURCE/pre-commit"
    echo -e "${GREEN}✓ 已保存 pre-commit 钩子到模板目录${NC}"
fi

# =============================================================================
# 设置钩子权限
# =============================================================================
echo ""
echo "设置钩子执行权限..."

find "$HOOKS_SOURCE" -type f -exec chmod +x {} \;
find "$HOOKS_DEST" -type f -exec chmod +x {} \;

echo -e "${GREEN}✓ 钩子权限已设置${NC}"
echo ""

# =============================================================================
# 配置 Git 使用模板目录
# =============================================================================
echo "配置 Git 钩子模板目录..."

git config core.hooksPath "$HOOKS_SOURCE" 2>/dev/null || {
    # 如果不支持 core.hooksPath，使用符号链接方式
    echo -e "${YELLOW}注意: Git 版本不支持 core.hooksPath，使用符号链接方式${NC}"

    # 创建符号链接
    for hook in "$HOOKS_SOURCE"/*; do
        hook_name=$(basename "$hook")
        ln -sf "$hook" "$HOOKS_DEST/$hook_name"
    done
}

echo -e "${GREEN}✓ Git 钩子已配置${NC}"
echo ""

# =============================================================================
# 列出已安装的钩子
# =============================================================================
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}         已安装的 Git 钩子${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

for hook in "$HOOKS_DEST"/*; do
    if [ -x "$hook" ]; then
        hook_name=$(basename "$hook")
        echo -e "${GREEN}✓ $hook_name${NC}"
    fi
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "完成！Git 钩子已安装并激活。"
echo ""
echo -e "${YELLOW}提示:${NC}"
echo "1. 钩子将在每次提交前自动运行"
echo "2. 如需跳过钩子，使用: git commit --no-verify"
echo "3. 如需修改钩子，编辑: $HOOKS_SOURCE/pre-commit"
echo ""
