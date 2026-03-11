#!/bin/bash
# =============================================================================
# Git 历史敏感信息清理脚本
# 用途: 从 Git 历史中彻底清除 DeepSeek API Key
# 警告: 此操作将改写 Git 历史，需要强制推送！
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 敏感信息
SENSITIVE_KEY="***REMOVED***"

echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║     Git 历史敏感信息清理 - 警告：操作不可逆！              ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "敏感 Key: ${SENSITIVE_KEY:0:20}... (已隐藏完整内容)"
echo ""

# =============================================================================
# 步骤 1: 安全检查
# =============================================================================
echo -e "${YELLOW}[1/6] 安全检查${NC}"

# 检查是否在 Git 仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}✗ 错误: 当前目录不是 Git 仓库${NC}"
    exit 1
fi

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}✗ 错误: 存在未提交的更改，请先提交或暂存${NC}"
    git status --short
    exit 1
fi

# 显示当前分支
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}✓ 当前分支: $CURRENT_BRANCH${NC}"

# 显示远程仓库
REMOTE_URL=$(git remote get-url origin)
echo -e "${GREEN}✓ 远程仓库: $REMOTE_URL${NC}"
echo ""

# =============================================================================
# 步骤 2: 创建备份
# =============================================================================
echo -e "${YELLOW}[2/6] 创建备份${NC}"

BACKUP_DIR="../Meeting_intelligence_backup_$(date +%Y%m%d_%H%M%S)"
git clone --bare . "$BACKUP_DIR"

echo -e "${GREEN}✓ 备份创建于: $BACKUP_DIR${NC}"
echo -e "${YELLOW}  清理完成后可使用: rm -rf $BACKUP_DIR${NC}"
echo ""

# =============================================================================
# 步骤 3: 扫描当前代码中的敏感信息
# =============================================================================
echo -e "${YELLOW}[3/6] 扫描当前代码${NC}"

FOUND_FILES=()

# 扫描 .env 文件
if [ -f ".env" ] && grep -q "$SENSITIVE_KEY" .env 2>/dev/null; then
    FOUND_FILES+=(".env")
fi

# 扫描 .claude 目录
if [ -d ".claude" ] && grep -r "$SENSITIVE_KEY" .claude/ >/dev/null 2>&1; then
    FOUND_FILES+=(".claude/settings.local.json")
fi

# 扫描 Python 文件
while IFS= read -r file; do
    FOUND_FILES+=("$file")
done < <(grep -rl "$SENSITIVE_KEY" --include="*.py" . 2>/dev/null || true)

if [ ${#FOUND_FILES[@]} -gt 0 ]; then
    echo -e "${RED}⚠ 发现包含敏感 Key 的文件:${NC}"
    for file in "${FOUND_FILES[@]}"; do
        echo "  - $file"
    done
else
    echo -e "${GREEN}✓ 当前代码中未发现硬编码的 Key${NC}"
fi
echo ""

# =============================================================================
# 步骤 4: 清理本地文件
# =============================================================================
echo -e "${YELLOW}[4/6] 清理本地文件${NC}"

# 清理 .env 文件
if [ -f ".env" ] && grep -q "$SENSITIVE_KEY" .env 2>/dev/null; then
    # 使用 sed 替换 Key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/$SENSITIVE_KEY/your_deepseek_key_here/g" .env
    else
        # Linux
        sed -i "s/$SENSITIVE_KEY/your_deepseek_key_here/g" .env
    fi
    echo -e "${GREEN}✓ 已清理 .env 文件${NC}"
fi

# 清理 .claude 目录
if [ -f ".claude/settings.local.json" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/$SENSITIVE_KEY/***REMOVED***/g" .claude/settings.local.json
    else
        sed -i "s/$SENSITIVE_KEY/***REMOVED***/g" .claude/settings.local.json
    fi
    echo -e "${GREEN}✓ 已清理 .claude/settings.local.json${NC}"
fi
echo ""

# =============================================================================
# 步骤 5: 清理 Git 历史
# =============================================================================
echo -e "${YELLOW}[5/6] 清理 Git 历史${NC}"
echo -e "${RED}⚠️ 即将改写 Git 历史，此操作不可逆！${NC}"

read -p "是否继续? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}✗ 已取消清理${NC}"
    exit 0
fi

# 检查 git-filter-repo 是否安装
if ! command -v git-filter-repo &> /dev/null; then
    echo "安装 git-filter-repo..."
    pip install git-filter-repo
fi

# 创建敏感字符串文件
cat > /tmp/secrets.txt << EOF
$SENSITIVE_KEY==>***REMOVED***
EOF

# 执行清理
echo "开始清理 Git 历史..."
git filter-repo --replace-text /tmp/secrets.txt

# 清理临时文件
rm -f /tmp/secrets.txt

echo -e "${GREEN}✓ Git 历史已清理${NC}"
echo ""

# =============================================================================
# 步骤 6: 验证和推送
# =============================================================================
echo -e "${YELLOW}[6/6] 验证和推送${NC}"

# 验证敏感信息是否已清除
if git log --all --source --full-history -S "$SENSITIVE_KEY" 2>/dev/null | grep -q .; then
    echo -e "${RED}✗ 警告: Git 历史中仍可能存在敏感信息${NC}"
    echo "请手动检查: git log --all -S \"$SENSITIVE_KEY\""
else
    echo -e "${GREEN}✓ 验证通过: Git 历史中已无敏感信息${NC}"
fi
echo ""

# 询问是否推送
echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  即将强制推送到远程，这将改写远程仓库的历史！         ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
read -p "是否强制推送到远程? (yes/no): " push_confirm

if [ "$push_confirm" = "yes" ]; then
    git push origin main --force
    echo -e "${GREEN}✓ 已强制推送到远程${NC}"
else
    echo -e "${YELLOW}✗ 已取消推送，请手动执行: git push origin main --force${NC}"
fi
echo ""

# =============================================================================
# 完成
# =============================================================================
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                      清理完成                             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}后续事项:${NC}"
echo "1. 通知所有协作者执行: git fetch origin && git reset --hard origin/main"
echo "2. 在 DeepSeek 平台撤销已暴露的 API Key: https://platform.deepseek.com"
echo "3. 生成新的 API Key 并更新本地 .env 文件"
echo "4. 确认无误后删除备份: rm -rf $BACKUP_DIR"
echo ""
