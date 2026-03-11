#!/usr/bin/env python3
"""
测试不同模板的总结生成

使用 30分钟音频，生成不同角度的模板总结
"""

import os
import sys
from pathlib import Path

# 加载环境变量
if Path('.env').exists():
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from summarizer.pipeline import audio_to_summary
from summarizer.llm import GLMProvider
from datetime import datetime


def test_template_summary(template_name: str):
    """测试指定模板的总结生成"""
    print(f"\n{'='*60}")
    print(f"测试模板: {template_name}")
    print(f"{'='*60}")

    audio_path = "data/raw_audio/test_meeting_30min.wav"

    if not Path(audio_path).exists():
        print(f"❌ 音频文件不存在: {audio_path}")
        return None

    # 创建 LLM Provider
    llm = GLMProvider(api_key=os.environ.get("ZHIPU_API_KEY"), model="glm-4-flash")

    try:
        # 生成总结
        summary = audio_to_summary(
            audio_path=audio_path,
            template_name=template_name,
            llm_provider=llm
        )

        print(f"\n✅ 总结生成成功!")
        print(f"  模板: {summary.template_name}")
        print(f"  角色: {summary.template_role}")
        print(f"  Sections: {len(summary.sections)} 个")
        print(f"  处理时间: {summary.processing_time:.2f} 秒")

        # 显示 sections
        print(f"\n📋 生成的 Sections:")
        for section in summary.sections:
            print(f"  - {section.title}")

        # 检查保存位置
        if summary.output_path:
            print(f"\n💾 保存位置: {summary.output_path}")
        else:
            print(f"\n⚠️  未保存到文件")

        return summary

    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("="*60)
    print("模板总结测试 - 30分钟音频")
    print("="*60)

    # 检查 API Key
    if not os.environ.get("ZHIPU_API_KEY"):
        print("❌ 未设置 ZHIPU_API_KEY")
        return 1

    # 测试不同模板
    templates = [
        "general",
        "product-manager",
        "course-student",
        "executive"
    ]

    results = {}
    for template in templates:
        result = test_template_summary(template)
        if result:
            results[template] = result

    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")

    # 查找所有生成的总结文件
    summaries_dir = Path("data/summaries")
    if summaries_dir.exists():
        # 查找今天的文件
        today = datetime.now().strftime("%Y%m%d")
        today_files = list(summaries_dir.glob(f"summary_*_{today}*.json"))

        print(f"\n📁 今天的总结文件 ({len(today_files)} 个):")
        for f in sorted(today_files):
            # 提取模板名称
            parts = f.stem.split('_')
            if len(parts) >= 3:
                template = '_'.join(parts[1:-1])  # 中间部分是模板名
            else:
                template = "unknown"
            print(f"  - {f.name} (模板: {template})")

    print(f"\n✅ 完成! 生成了 {len(results)} 个模板总结")
    print(f"📁 总结文件位置: data/summaries/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
