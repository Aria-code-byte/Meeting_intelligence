#!/bin/bash
# 自动等待并生成所有总结的脚本

echo "================================================"
echo "  会议智能助手 - 自动生成总结"
echo "================================================"
echo ""
echo "由于智谱 API 速率限制，脚本将自动等待并重试..."
echo ""

# 激活虚拟环境
source /mnt/d/meeting_intelligence/venv/bin/activate

# 定义模板列表
templates=("product-manager" "developer" "executive" "general" "designer")

# 等待时间（秒）
wait_time=900  # 15 分钟

echo "等待 $wait_time 秒后开始执行..."
echo "预计开始时间: $(date -d '+$wait_time seconds' '+%H:%M:%S')"
echo ""

# 倒计时
for ((i=$wait_time; i>0; i-=60)); do
    minutes=$((i / 60))
    seconds=$((i % 60))
    if [ $minutes -gt 0 ]; then
        echo -ne "\r等待中: ${minutes}分${seconds}秒 "
    else
        echo -ne "\r等待中: ${seconds}秒 "
    fi
    sleep 5
done
echo ""
echo "开始执行!"
echo ""

# 创建输出目录
output_dir="/mnt/d/meeting_intelligence/outputs/meeting_01"
mkdir -p "$output_dir"

# 逐个执行模板
success_count=0
for template in "${templates[@]}"; do
    echo ""
    echo "▶ 正在生成: $template 模板总结..."

    if python -m meeting_intelligence summarize \
        "/mnt/d/meeting_intelligence/outputs/meeting_01/transcript_clean.md" \
        --template "$template" \
        --provider glm \
        --model glm-4-flash \
        > "/tmp/summary_${template}.log" 2>&1; then
        echo "  ✓ $template 模板成功"
        ((success_count++))

        # 如果保存了文件，移动到输出目录
        if [ -f "/mnt/d/meeting_intelligence/data/summaries/summary_${template}.md" ]; then
            mv "/mnt/d/meeting_intelligence/data/summaries/summary_${template}.md" \
               "$output_dir/summary_${template}.md"
        fi
    else
        echo "  ✗ $template 模板失败"
    fi

    # 每个模板之间等待 15 秒，避免触发速率限制
    if [ $template != "${templates[-1]}" ]; then
        echo "  → 等待 15 秒后处理下一个模板..."
        sleep 15
    fi
done

echo ""
echo "================================================"
echo "  执行完成! 成功: $success_count / ${#templates[@]}"
echo "================================================"
echo ""
echo "输出目录: $output_dir"
echo ""
ls -la "$output_dir"/summary_*.md 2>/dev/null || echo "未找到总结文件"
