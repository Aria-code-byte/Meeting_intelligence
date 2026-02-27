#!/usr/bin/env python3
"""
Full Pipeline Test Script

完整的会议处理流程测试脚本：
视频 → 音频提取 → Whisper 转录 → 文稿整理 → 多模板总结

Usage:
    python test_full_pipeline.py path/to/video.mp4

Output:
    outputs/{video_filename}/
        ├── transcript_raw.json       # 原始转录 JSON
        ├── transcript_clean.md       # 格式化文稿
        ├── summary_product-manager.md # 产品经理模板总结
        ├── summary_executive.md      # 高管模板总结
        └── summary_general.md        # 通用模板总结
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import traceback

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv 未安装时忽略


def print_step(step: str, status: str = "processing"):
    """打印步骤信息"""
    icons = {
        "start": "▶",
        "processing": "○",
        "success": "✓",
        "error": "✗",
        "info": "→"
    }
    icon = icons.get(status, "○")
    print(f"{icon} {step}")


def print_success(message: str):
    """打印成功信息"""
    print(f"  ✓ {message}")


def print_error(message: str):
    """打印错误信息"""
    print(f"  ✗ {message}")


def print_info(message: str):
    """打印信息"""
    print(f"  → {message}")


def setup_output_directory(video_path: Path) -> Path:
    """
    设置输出目录

    Args:
        video_path: 视频文件路径

    Returns:
        输出目录路径
    """
    # 获取视频文件名（不含扩展名）
    video_name = video_path.stem
    output_dir = Path("outputs") / video_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def step1_extract_audio(video_path: Path, output_dir: Path) -> Path:
    """
    步骤 1: 从视频中提取音频

    Args:
        video_path: 视频文件路径
        output_dir: 输出目录

    Returns:
        提取的音频文件路径
    """
    print_step("步骤 1: 提取音频", "start")

    try:
        from audio.extract_audio import extract_audio, ProcessedAudio
        from audio.preprocess import convert_to_wav

        # 提取音频
        print_info(f"从视频提取音频: {video_path.name}")
        extracted = extract_audio(str(video_path))

        # 转换为 WAV 格式（Whisper 需要）
        print_info("转换为 WAV 格式 (16kHz, mono)")
        processed = convert_to_wav(extracted.path)

        # 保存到输出目录
        audio_output = output_dir / "audio.wav"
        import shutil
        shutil.copy(processed.path, audio_output)

        print_success(f"音频已保存: {audio_output}")
        return audio_output

    except Exception as e:
        print_error(f"音频提取失败: {e}")
        raise


def step2_transcribe(audio_path: Path, output_dir: Path) -> dict:
    """
    步骤 2: Whisper 转录

    Args:
        audio_path: 音频文件路径
        output_dir: 输出目录

    Returns:
        转录结果字典
    """
    print_step("步骤 2: Whisper 转录", "start")

    try:
        from asr.transcribe import transcribe

        print_info(f"正在转录音频...")
        print_info(f"音频文件: {audio_path}")

        # 执行转录
        result = transcribe(
            str(audio_path),
            language="auto",
            model_size="base",  # 使用 base 模型平衡速度和准确度
            enable_postprocess=True
        )

        # 保存原始转录结果
        transcript_path = output_dir / "transcript_raw.json"
        result_dict = {
            "metadata": {
                "audio_path": str(audio_path),
                "duration": result.duration,
                "asr_provider": result.asr_provider,
                "model_size": "base",
                "created_at": datetime.now().isoformat(),
                "utterance_count": len(result.utterances)
            },
            "utterances": [
                {
                    "start": u.start,
                    "end": u.end,
                    "text": u.text
                }
                for u in result.utterances
            ]
        }

        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

        print_success(f"转录完成: {len(result.utterances)} 个语音片段")
        print_success(f"时长: {result.duration:.1f} 秒")
        print_success(f"已保存: {transcript_path}")

        return result_dict

    except Exception as e:
        print_error(f"转录失败: {e}")
        raise


def step3_format_transcript(transcript_path: Path, output_dir: Path) -> Path:
    """
    步骤 3: 格式化文稿

    Args:
        transcript_path: 转录文件路径
        output_dir: 输出目录

    Returns:
        格式化文稿文件路径
    """
    print_step("步骤 3: 格式化文稿", "start")

    try:
        from transcript.formatter import format_transcript, FormatterConfig

        print_info("正在格式化文稿...")

        # 配置格式化参数
        config = FormatterConfig(
            paragraph_max_length=300,
            section_break_gap=10.0,
            add_missing_punctuation=True
        )

        # 执行格式化
        formatted_output = output_dir / "transcript_clean.md"
        from transcript.formatter import FormatMethod
        formatted = format_transcript(
            str(transcript_path),
            output_path=str(formatted_output),
            config=config,
            method=FormatMethod.RULE_BASED,
            output_format="markdown"
        )

        print_success(f"格式化完成")
        print_success(f"段落数: {formatted.total_paragraph_count()}")
        print_success(f"章节数: {len(formatted.sections)}")
        print_success(f"总字数: {formatted.total_word_count()}")
        print_success(f"已保存: {formatted_output}")

        return formatted_output

    except Exception as e:
        print_error(f"格式化失败: {e}")
        raise


def step4_generate_summaries(
    transcript_path: Path,
    output_dir: Path,
    templates: list = None
) -> list[Path]:
    """
    步骤 4: 为每个模板生成总结

    Args:
        transcript_path: 转录文件路径
        output_dir: 输出目录
        templates: 模板列表（可选，默认使用所有模板）

    Returns:
        生成的总结文件路径列表
    """
    print_step("步骤 4: 生成多模板总结", "start")

    try:
        from template.manager import get_template_manager
        from summarizer.llm import GLMProvider, OpenAIProvider, AnthropicProvider
        from summarizer.generate import generate_summary
        from summarizer.types import SummaryResult
        import time

        # 获取模板管理器
        manager = get_template_manager()

        # 确定要使用的模板
        if templates is None:
            # 使用所有可用模板
            all_templates = manager.list_templates()
            templates = [t["name"] for t in all_templates if t.get("name")]

        print_info(f"使用模板: {', '.join(templates)}")

        # 确定 LLM provider
        provider_name = os.environ.get("DEFAULT_LLM_PROVIDER", "glm")

        if provider_name == "glm" and os.environ.get("ZHIPU_API_KEY"):
            from summarizer.llm import GLMProvider
            llm = GLMProvider(model=os.environ.get("DEFAULT_LLM_MODEL", "glm-4-flash"))
            provider_display = f"GLM ({llm.model})"
        elif provider_name == "openai" and os.environ.get("OPENAI_API_KEY"):
            from summarizer.llm import OpenAIProvider
            llm = OpenAIProvider(model=os.environ.get("DEFAULT_LLM_MODEL", "gpt-3.5-turbo"))
            provider_display = f"OpenAI ({llm.model})"
        elif provider_name == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
            from summarizer.llm import AnthropicProvider
            llm = AnthropicProvider(model=os.environ.get("DEFAULT_LLM_MODEL", "claude-3-haiku-20240307"))
            provider_display = f"Anthropic ({llm.model})"
        else:
            raise RuntimeError(
                "未设置 API Key。请设置以下环境变量之一:\n"
                "  - ZHIPU_API_KEY (推荐)\n"
                "  - OPENAI_API_KEY\n"
                "  - ANTHROPIC_API_KEY"
            )

        print_info(f"LLM Provider: {provider_display}")

        # 读取转录文本
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        # 合并 utterances 为文本
        transcript_text = " ".join([
            u.get("text", "") for u in transcript_data.get("utterances", [])
        ])

        generated_files = []

        # 为每个模板生成总结
        for template_name in templates:
            print()
            print_info(f"正在生成总结: {template_name}")

            try:
                # 获取模板
                template = manager.get_template(template_name)

                # 记录开始时间
                start_time = time.time()

                # 生成总结（使用内部接口以简化流程）
                from template.render import create_system_prompt, create_user_prompt

                system_prompt = create_system_prompt(template)
                user_prompt = create_user_prompt(template, transcript_text, {})

                # 调用 LLM
                response = llm.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt
                )

                # 解析响应
                from summarizer.generate import _parse_summary_response
                sections = _parse_summary_response(response.content, template)

                processing_time = time.time() - start_time

                # 创建结果
                summary = SummaryResult(
                    sections=sections,
                    transcript_path=str(transcript_path),
                    template_name=template.name,
                    template_role=template.role,
                    llm_provider=llm.name,
                    llm_model=llm.model,
                    processing_time=processing_time
                )

                # 保存为 Markdown
                summary_filename = f"summary_{template_name}.md"
                summary_path = output_dir / summary_filename

                # 转换为 Markdown 格式
                markdown_content = summary.to_markdown()

                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                generated_files.append(summary_path)

                print_success(f"{template_name}: 完成 ({processing_time:.2f}s)")
                print_success(f"  生成 {len(sections)} 个 sections")
                print_success(f"  已保存: {summary_filename}")

                # 添加延迟避免速率限制（智谱 API 限制较严格）
                time.sleep(3)

            except Exception as e:
                print_error(f"{template_name}: 失败 - {e}")
                # 出错后也等待一下
                time.sleep(2)
                continue

        print()
        print_success(f"总结生成完成: {len(generated_files)}/{len(templates)}")

        return generated_files

    except Exception as e:
        print_error(f"总结生成失败: {e}")
        traceback.print_exc()
        raise


def run_full_pipeline(
    video_path: str,
    templates: list = None,
    skip_existing: bool = False
) -> dict:
    """
    运行完整的处理流程

    Args:
        video_path: 视频文件路径
        templates: 要使用的模板列表（None 表示全部）
        skip_existing: 是否跳过已存在的文件

    Returns:
        处理结果字典
    """
    video_path = Path(video_path)

    # 验证输入文件
    if not video_path.exists():
        print_error(f"文件不存在: {video_path}")
        sys.exit(1)

    video_extensions = ['.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv']
    if video_path.suffix.lower() not in video_extensions:
        print_error(f"不支持的视频格式: {video_path.suffix}")
        print_info(f"支持的格式: {', '.join(video_extensions)}")
        sys.exit(1)

    # 打印开始信息
    print("=" * 60)
    print("AI Meeting Assistant - Full Pipeline Test")
    print("=" * 60)
    print()
    print(f"输入文件: {video_path}")
    print(f"文件大小: {video_path.stat().st_size / 1024 / 1024:.1f} MB")
    print()

    # 设置输出目录
    output_dir = setup_output_directory(video_path)
    print(f"输出目录: {output_dir}")
    print()

    # 检查是否需要跳过
    if skip_existing:
        existing_files = list(output_dir.glob("*"))
        if existing_files:
            print_info(f"输出目录已存在 {len(existing_files)} 个文件，跳过处理")
            return {
                "status": "skipped",
                "output_dir": str(output_dir),
                "existing_files": len(existing_files)
            }

    results = {
        "video_path": str(video_path),
        "output_dir": str(output_dir),
        "start_time": datetime.now().isoformat()
    }

    try:
        # 步骤 1: 提取音频
        audio_path = step1_extract_audio(video_path, output_dir)
        results["audio_path"] = str(audio_path)

        print()

        # 步骤 2: 转录
        transcript_dict = step2_transcribe(audio_path, output_dir)
        results["transcript"] = {
            "utterance_count": transcript_dict["metadata"]["utterance_count"],
            "duration": transcript_dict["metadata"]["duration"]
        }

        print()

        # 步骤 3: 格式化文稿
        transcript_path = output_dir / "transcript_raw.json"
        formatted_path = step3_format_transcript(transcript_path, output_dir)
        results["formatted_path"] = str(formatted_path)

        print()

        # 步骤 4: 生成总结
        summary_files = step4_generate_summaries(transcript_path, output_dir, templates)
        results["summary_files"] = [str(f) for f in summary_files]

        # 打印完成信息
        print()
        print("=" * 60)
        print_success("Pipeline 执行完成!")
        print("=" * 60)
        print()
        print(f"输出目录: {output_dir}")
        print()
        print("生成的文件:")
        for f in sorted(output_dir.iterdir()):
            size = f.stat().st_size / 1024
            print(f"  • {f.name} ({size:.1f} KB)")

        results["status"] = "success"
        results["end_time"] = datetime.now().isoformat()

        return results

    except Exception as e:
        print()
        print("=" * 60)
        print_error(f"Pipeline 执行失败: {e}")
        print("=" * 60)
        print()

        results["status"] = "failed"
        results["error"] = str(e)
        results["end_time"] = datetime.now().isoformat()

        # 保存错误日志
        error_log = output_dir / "error_log.txt"
        with open(error_log, "w", encoding="utf-8") as f:
            f.write(f"Error: {e}\n\n")
            f.write(traceback.format_exc())
        print_info(f"错误日志已保存: {error_log}")

        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI Meeting Assistant - Full Pipeline Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理单个视频（所有模板）
  python test_full_pipeline.py meeting.mp4

  # 指定模板
  python test_full_pipeline.py meeting.mp4 --templates product-manager executive

  # 跳过已存在的输出
  python test_full_pipeline.py meeting.mp4 --skip-existing

输出目录结构:
  outputs/{video_filename}/
    ├── audio.wav
    ├── transcript_raw.json
    ├── transcript_clean.md
    ├── summary_product-manager.md
    ├── summary_executive.md
    └── summary_general.md
        """
    )

    parser.add_argument(
        "input",
        help="输入视频文件路径"
    )

    parser.add_argument(
        "--templates", "-t",
        nargs="+",
        help="指定模板列表（默认使用所有可用模板）"
    )

    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="如果输出目录已存在则跳过"
    )

    parser.add_argument(
        "--model-size", "-m",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小（默认: base）"
    )

    args = parser.parse_args()

    # 运行流程
    results = run_full_pipeline(
        video_path=args.input,
        templates=args.templates,
        skip_existing=args.skip_existing
    )

    # 保存运行结果
    output_dir = Path(results["output_dir"])
    results_file = output_dir / "pipeline_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 根据状态退出
    if results["status"] == "success":
        sys.exit(0)
    elif results["status"] == "skipped":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
