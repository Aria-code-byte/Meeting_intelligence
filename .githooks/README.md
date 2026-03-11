# Git Hooks - 预检钩子

本目录包含项目的 Git 钩子模板，用于防止敏感信息提交和保证代码质量。

## 已安装的钩子

### pre-commit（提交前检查）

在每次 `git commit` 执行前自动运行，检查以下内容：

1. **禁止的文件类型**
   - `.env` 文件（环境变量配置）
   - `.bak` 文件（备份文件）
   - `.swp` 文件（编辑器临时文件）
   - 密钥文件（`*.key`, `*.pem`, `id_rsa`）

2. **敏感信息内容**
   - API Keys（OpenAI, Anthropic, DeepSeek 等）
   - 密码字段
   - Token 值
   - Secret 值

3. **大文件警告**
   - 文件超过 1MB 时发出警告

4. **Python 语法检查**
   - Python 文件语法错误检测

## 安装钩子

### 自动安装

```bash
./scripts/install-hooks.sh
```

### 手动安装

```bash
# 复制钩子到 Git 目录
cp .githooks/pre-commit .git/hooks/pre-commit

# 添加执行权限
chmod +x .git/hooks/pre-commit
```

### 配置 Git 使用模板目录（推荐）

```bash
# 设置钩子模板路径
git config core.hooksPath .githooks
```

## 测试钩子

创建一个包含敏感信息的测试文件：

```bash
echo "DEEPSEEK_API_KEY=sk-xxxxx" > test.txt
git add test.txt
git commit -m "test"
```

预期输出：
```
❌ 预检钩子检查失败！

发现以下问题:
  - 包含敏感信息
```

## 跳过钩子（不推荐）

如果需要临时跳过钩子检查：

```bash
git commit --no-verify -m "message"
```

⚠️ **警告**: 仅在确保安全的情况下使用此选项。

## 自定义钩子

编辑 `.githooks/pre-commit` 文件来自定义检查规则：

### 添加新的敏感信息模式

在 `PATTERNS` 数组中添加正则表达式：

```bash
PATTERNS=(
    # ... 现有模式 ...
    "你的新正则表达式"
)
```

### 添加新的禁止文件类型

在 `FORBIDDEN_FILES` 数组中添加：

```bash
FORBIDDEN_FILES=(
    # ... 现有模式 ...
    "你的文件模式"
)
```

## 常见问题

### Q: 钩子不执行？
A: 检查文件权限：`ls -la .git/hooks/pre-commit` 应该显示可执行权限（`-rwxr-xr-x`）

### Q: 如何临时禁用某个检查？
A: 编辑 `.githooks/pre-commit`，注释掉对应的检查代码块

### Q: 团队成员如何安装？
A: 运行 `./scripts/install-hooks.sh` 或将 `.githooks/pre-commit` 复制到其 `.git/hooks/` 目录

### Q: 已提交的敏感信息如何清理？
A: 运行 `./cleanup_history.sh` 清理 Git 历史

## 安全最佳实践

1. ✅ **永远不要** 将 `.env` 文件提交到 Git
2. ✅ 使用 `.env.example` 作为配置模板
3. ✅ 定期检查 `git log` 确保无敏感信息
4. ✅ 在 API 平台定期轮换 Keys
5. ✅ 为不同的环境使用不同的 Keys

## 相关文件

- `.gitignore` - 定义忽略的文件
- `.env.example` - 环境变量配置模板
- `cleanup_history.sh` - Git 历史清理脚本
- `scripts/install-hooks.sh` - 钩子安装脚本
