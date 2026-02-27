#!/usr/bin/env python3
"""
AI Meeting Assistant CLI

主入口文件 - 提供命令行接口
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import time

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    # 尝试从项目根目录加载 .env
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv 未安装时忽略

# 尝试导入 rich，如果不可用则使用普通输出
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False


def main():
    parser = argparse.ArgumentParser(
        prog="meeting-intelligence",
        description="AI Meeting Assistant - 智能会议总结工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理音频文件
  python -m meeting_intelligence process meeting.mp3 --template product-manager

  # 处理视频文件
  python -m meeting_intelligence process meeting.mp4 --template developer

  # 列出可用模板
  python -m meeting_intelligence template list

  # 查看模板详情
  python -m meeting_intelligence template show product-manager

  # 使用指定模型
  python -m meeting_intelligence process meeting.mp3 --model gpt-4
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # ============================================
    # process 命令
    # ============================================
    process_parser = subparsers.add_parser('process', help='处理会议文件')
    process_parser.add_argument('input', help='输入文件路径（音频或视频）')
    process_parser.add_argument('--template', '-t', default='general',
                               help='模板名称（默认: general）')
    process_parser.add_argument('--model', '-m',
                               default=os.environ.get('DEFAULT_LLM_MODEL', 'glm-4-flash'),
                               help='LLM 模型（默认: glm-4-flash）')
    process_parser.add_argument('--provider', '-p',
                               default=os.environ.get('DEFAULT_LLM_PROVIDER', 'glm'),
                               choices=['openai', 'anthropic', 'glm'],
                               help='LLM 提供商（默认: glm）')
    process_parser.add_argument('--output', '-o', help='输出文件路径（默认自动生成）')
    process_parser.add_argument('--no-save', action='store_true',
                               help='不保存结果到文件')

    # ============================================
    # template 命令
    # ============================================
    template_parser = subparsers.add_parser('template', help='模板管理')
    template_subparsers = template_parser.add_subparsers(dest='template_command')

    # template list
    list_parser = template_subparsers.add_parser('list', help='列出所有模板')

    # template show
    show_parser = template_subparsers.add_parser('show', help='显示模板详情')
    show_parser.add_argument('name', help='模板名称')

    # ============================================
    # config 命令
    # ============================================
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_subparsers = config_parser.add_subparsers(dest='config_command')

    # config init
    init_parser = config_subparsers.add_parser('init', help='初始化配置文件')
    init_parser.add_argument('--path', help='配置文件路径（默认: ~/.meeting-assistant/config.yaml）')

    # ============================================
    # summarize 命令 - 从转录文本生成总结
    # ============================================
    summarize_parser = subparsers.add_parser('summarize', help='从转录文本生成总结（跳过ASR）')
    summarize_parser.add_argument('input', help='转录文件路径（.txt 或 .md）')
    summarize_parser.add_argument('--template', '-t', default='general',
                                  help='模板名称（默认: general）')
    summarize_parser.add_argument('--model', '-m',
                                  default=os.environ.get('DEFAULT_LLM_MODEL', 'glm-4-flash'),
                                  help='LLM 模型（默认: glm-4-flash）')
    summarize_parser.add_argument('--provider', '-p',
                                  default=os.environ.get('DEFAULT_LLM_PROVIDER', 'glm'),
                                  choices=['openai', 'anthropic', 'glm'],
                                  help='LLM 提供商（默认: glm）')
    summarize_parser.add_argument('--max-chars', type=int, default=12000,
                                  help='单次请求最大字符数（用于分块处理大文稿，默认: 12000）')

    # ============================================
    # format 命令 - 格式化转录文稿
    # ============================================
    format_parser = subparsers.add_parser('format', help='格式化转录文稿为可读文本')
    format_parser.add_argument('input', help='转录文件路径（.json）')
    format_parser.add_argument('--output', '-o', help='输出文件路径（默认自动生成）')
    format_parser.add_argument('--format', '-f', default='markdown',
                               choices=['markdown', 'md', 'plain', 'txt', 'html'],
                               help='输出格式（默认: markdown）')
    format_parser.add_argument('--max-length', type=int, default=300,
                               help='单段落最大字数（默认: 300）')
    format_parser.add_argument('--section-gap', type=float, default=10.0,
                               help='分段停顿阈值（秒，默认: 10.0）')

    # ============================================
    # refine 命令 - LLM 优化转录文本
    # ============================================
    refine_parser = subparsers.add_parser('refine', help='使用 LLM 优化转录文本可读性')
    refine_parser.add_argument('input', help='输入文件路径（.txt, .md 或 .json）')
    refine_parser.add_argument('--output', '-o', help='输出文件路径（默认自动生成）')
    refine_parser.add_argument('--mode', '-m',
                               choices=['conservative', 'balanced', 'aggressive'],
                               default='balanced',
                               help='优化模式（默认: balanced）')
    refine_parser.add_argument('--provider', '-p',
                               default=os.environ.get('DEFAULT_LLM_PROVIDER', 'glm'),
                               choices=['openai', 'anthropic', 'glm'],
                               help='LLM 提供商（默认: glm）')
    refine_parser.add_argument('--model',
                               default=os.environ.get('DEFAULT_LLM_MODEL', 'glm-4-flash'),
                               help='LLM 模型（默认: glm-4-flash）')
    refine_parser.add_argument('--rules-only', action='store_true',
                               help='仅使用规则优化（不调用 LLM，快速模式）')

    # 解析参数
    args = parser.parse_args()

    # 如果没有命令，显示帮助
    if args.command is None:
        parser.print_help()
        return 0

    # 执行命令
    if args.command == 'process':
        return cmd_process(args)
    elif args.command == 'template':
        return cmd_template(args)
    elif args.command == 'config':
        return cmd_config(args)
    elif args.command == 'summarize':
        return cmd_summarize(args)
    elif args.command == 'format':
        return cmd_format(args)
    elif args.command == 'refine':
        return cmd_refine(args)
    else:
        parser.print_help()
        return 0


def cmd_process(args):
    """处理会议文件命令"""
    input_path = Path(args.input)

    if not input_path.exists():
        print_error(f"文件不存在: {args.input}")
        return 1

    # 检查文件类型
    video_extensions = ['.mp4', '.mkv', '.mov']
    audio_extensions = ['.mp3', '.wav', '.m4a']

    is_video = input_path.suffix.lower() in video_extensions
    is_audio = input_path.suffix.lower() in audio_extensions

    if not (is_video or is_audio):
        print_error(f"不支持的文件格式: {input_path.suffix}")
        print_info(f"支持的格式: 视频 {video_extensions}, 音频 {audio_extensions}")
        return 1

    # 显示处理信息
    print_header("AI Meeting Assistant")
    print(f"输入文件: {input_path}")
    print(f"文件类型: {'视频' if is_video else '音频'}")
    print(f"使用模板: {args.template}")
    print(f"LLM 配置: {args.provider}/{args.model}")
    print()

    # 检查 API Key
    if args.provider == 'openai' and not os.environ.get('OPENAI_API_KEY'):
        print_error("未设置 OPENAI_API_KEY 环境变量")
        print_info("请设置: export OPENAI_API_KEY=sk-xxx")
        return 1
    elif args.provider == 'anthropic' and not os.environ.get('ANTHROPIC_API_KEY'):
        print_error("未设置 ANTHROPIC_API_KEY 环境变量")
        print_info("请设置: export ANTHROPIC_API_KEY=sk-ant-xxx")
        return 1
    elif args.provider == 'glm' and not os.environ.get('ZHIPU_API_KEY'):
        print_error("未设置 ZHIPU_API_KEY 环境变量")
        print_info("请设置: export ZHIPU_API_KEY=your-key")
        return 1

    # 创建 LLM provider
    try:
        if args.provider == 'openai':
            from summarizer.llm import OpenAIProvider
            llm = OpenAIProvider(model=args.model)
        elif args.provider == 'anthropic':
            from summarizer.llm import AnthropicProvider
            llm = AnthropicProvider(model=args.model)
        elif args.provider == 'glm':
            from summarizer.llm import GLMProvider
            llm = GLMProvider(model=args.model)
    except ImportError as e:
        print_error(f"无法导入 {args.provider} SDK: {e}")
        install_map = {
            'openai': 'openai',
            'anthropic': 'anthropic',
            'glm': 'zhipuai'
        }
        print_info(f"请运行: pip install {install_map.get(args.provider, args.provider)}")
        return 1

    # 处理文件
    try:
        print_status("开始处理...")

        if is_video:
            from summarizer.pipeline import video_to_summary
            summary = video_to_summary(
                video_path=str(input_path),
                template_name=args.template,
                llm_provider=llm
            )
        else:
            from summarizer.pipeline import audio_to_summary
            summary = audio_to_summary(
                audio_path=str(input_path),
                template_name=args.template,
                llm_provider=llm
            )

        # 显示结果
        print()
        print_success("处理完成!")
        print()
        print(f"模板: {summary.template_name} ({summary.template_role})")
        print(f"LLM: {summary.llm_provider}/{summary.llm_model}")
        print(f"处理时间: {summary.processing_time:.2f} 秒")
        print(f"生成 sections: {len(summary.sections)} 个")
        print()

        # 显示内容预览
        for section in summary.sections:
            print(f"[bold]{section.title}[/bold]" if RICH_AVAILABLE else f"{section.title}:")
            preview = section.content[:200] + "..." if len(section.content) > 200 else section.content
            print(f"  {preview}")
            print()

        if summary.output_path:
            print(f"总结文件: {summary.output_path}")

        return 0

    except Exception as e:
        print()
        print_error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_template(args):
    """模板管理命令"""
    from template.manager import get_template_manager

    manager = get_template_manager()

    if args.template_command == 'list':
        templates = manager.list_templates()

        print_header("可用模板")

        for t in templates:
            marker = "★" if t.get('is_default') else " "
            name = t['name']
            role = t.get('role', '')
            desc = t.get('description', '')

            if RICH_AVAILABLE:
                console.print(f"  {marker} [cyan]{name.ljust(20)}[/cyan] {role}")
                if desc:
                    console.print(f"     {desc}")
            else:
                print(f"  {marker} {name:20} {role}")
                if desc:
                    print(f"     {desc}")
            print()

        return 0

    elif args.template_command == 'show':
        try:
            template = manager.get_template(args.name)

            print_header(f"模板: {template.name}")
            print(f"角色: {template.role}")
            print(f"角度: {template.angle.value}")
            print(f"关注: {', '.join(template.focus)}")
            print()

            print_header("输出结构")

            for section in template.sections:
                req = "必需" if section.required else "可选"
                print(f"  {section.order}. {section.title} ({req})")
                print(f"     {section.prompt}")
                print()

            return 0

        except FileNotFoundError:
            print_error(f"模板不存在: {args.name}")
            return 1

    return 0


def cmd_config(args):
    """配置管理命令"""
    from meeting_intelligence.config import init_config, DEFAULT_CONFIG_PATH

    if args.config_command == 'init':
        # 确定配置文件路径
        if args.path:
            config_path = Path(args.path)
        else:
            config_path = DEFAULT_CONFIG_PATH

        # 检查是否已存在
        if config_path.exists():
            print_warning(f"配置文件已存在: {config_path}")
            confirm = input("是否覆盖? (y/n): ")
            if confirm.lower() != 'y':
                print_info("已取消")
                return 0

        # 创建配置文件
        try:
            created_path = init_config(config_path)
            print_success(f"配置文件已创建: {created_path}")
            print()
            print_info("请编辑配置文件以设置您的偏好:")
            print(f"  {created_path}")
            print()
            print_info("或使用环境变量覆盖配置:")
            print("  export OPENAI_API_KEY=sk-xxx")
            print("  export ANTHROPIC_API_KEY=sk-ant-xxx")
            return 0
        except Exception as e:
            print_error(f"创建配置文件失败: {e}")
            return 1

    return 0


def cmd_summarize(args):
    """从转录文本生成总结命令"""
    input_path = Path(args.input)

    if not input_path.exists():
        print_error(f"文件不存在: {args.input}")
        return 1

    # 显示处理信息
    print_header("AI Meeting Assistant")
    print(f"输入文件: {input_path}")
    print(f"使用模板: {args.template}")
    print(f"LLM 配置: {args.provider}/{args.model}")
    print()

    # 检查 API Key
    if args.provider == 'glm' and not os.environ.get('ZHIPU_API_KEY'):
        print_error("未设置 ZHIPU_API_KEY 环境变量")
        print_info("请设置: export ZHIPU_API_KEY=your-key")
        return 1
    elif args.provider == 'openai' and not os.environ.get('OPENAI_API_KEY'):
        print_error("未设置 OPENAI_API_KEY 环境变量")
        return 1
    elif args.provider == 'anthropic' and not os.environ.get('ANTHROPIC_API_KEY'):
        print_error("未设置 ANTHROPIC_API_KEY 环境变量")
        return 1

    # 读取转录文本
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
    except Exception as e:
        print_error(f"读取文件失败: {e}")
        return 1

    # 创建 LLM provider
    try:
        if args.provider == 'glm':
            from summarizer.llm import GLMProvider
            llm = GLMProvider(model=args.model)
        elif args.provider == 'openai':
            from summarizer.llm import OpenAIProvider
            llm = OpenAIProvider(model=args.model)
        else:
            from summarizer.llm import AnthropicProvider
            llm = AnthropicProvider(model=args.model)
    except ImportError as e:
        print_error(f"无法导入 {args.provider} SDK: {e}")
        return 1

    # 生成总结
    try:
        from summarizer.generate import generate_summary
        from template.manager import get_template_manager

        # 获取模板
        manager = get_template_manager()
        template = manager.get_template(args.template)

        # 直接调用 generate 的内部逻辑
        import time
        start_time = time.time()

        # 构建提示词
        from template.render import create_system_prompt, create_user_prompt
        system_prompt = create_system_prompt(template)

        # 检查是否需要分块处理
        transcript_length = len(transcript_text)
        max_chars = args.max_chars

        if transcript_length > max_chars:
            print_status(f"文稿较大 ({transcript_length} 字符)，将分块处理...")
            print()

            # 分块处理
            chunks = []
            chunk_count = (transcript_length + max_chars - 1) // max_chars

            for i in range(chunk_count):
                start = i * max_chars
                end = min(start + max_chars, transcript_length)
                chunk_text = transcript_text[start:end]

                print_status(f"处理第 {i+1}/{chunk_count} 块...")

                # 对第一块使用完整提示词，后续块简化提示词
                if i == 0:
                    user_prompt = create_user_prompt(template, chunk_text, {})
                else:
                    user_prompt = f"继续总结以下会议内容（这是第{i+1}部分，共{chunk_count}部分）：\n\n{chunk_text}\n\n请继续按模板结构输出。"

                response = llm.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt
                )

                chunks.append(response.content)
                print(f"  完成第 {i+1}/{chunk_count} 块")

                # 块之间稍作等待，避免速率限制
                if i < chunk_count - 1:
                    time.sleep(2)

            # 合并所有块
            print_status("合并结果...")
            combined_content = "\n\n".join(chunks)

            # 解析合并后的响应
            from summarizer.generate import _parse_summary_response
            sections = _parse_summary_response(combined_content, template)

        else:
            print_status("正在生成总结...")

            # 单次请求处理
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
        from summarizer.types import SummaryResult
        summary = SummaryResult(
            sections=sections,
            transcript_path=str(input_path),
            template_name=template.name,
            template_role=template.role,
            llm_provider=llm.name,
            llm_model=llm.model,
            processing_time=processing_time
        )

        # 保存结果
        summary.save()

        # 显示结果
        print()
        print_success("处理完成!")
        print()
        print(f"模板: {summary.template_name} ({summary.template_role})")
        print(f"LLM: {summary.llm_provider}/{summary.llm_model}")
        print(f"处理时间: {summary.processing_time:.2f} 秒")
        print(f"生成 sections: {len(summary.sections)} 个")
        print()

        # 显示内容
        for section in summary.sections:
            print(f"[bold]{section.title}[/bold]" if RICH_AVAILABLE else f"{section.title}:")
            print(section.content)
            print()

        if summary.output_path:
            print(f"总结文件: {summary.output_path}")

        return 0

    except Exception as e:
        print()
        print_error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_format(args):
    """格式化转录文稿命令"""
    input_path = Path(args.input)

    if not input_path.exists():
        print_error(f"文件不存在: {args.input}")
        return 1

    if input_path.suffix.lower() != '.json':
        print_error(f"不支持的文件格式: {input_path.suffix}")
        print_info("格式化命令需要 .json 转录文件")
        return 1

    # 显示处理信息
    print_header("AI Meeting Assistant - 文稿格式化")
    print(f"输入文件: {input_path}")
    print(f"输出格式: {args.format}")
    print()

    # 创建配置
    from transcript.formatter import FormatterConfig, FormatMethod, format_transcript

    config = FormatterConfig(
        paragraph_max_length=args.max_length,
        section_break_gap=args.section_gap
    )

    # 生成输出路径
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.format in ['markdown', 'md']:
            output_path = f"data/formatted/formatted_{timestamp}.md"
        elif args.format in ['plain', 'txt']:
            output_path = f"data/formatted/formatted_{timestamp}.txt"
        else:
            output_path = f"data/formatted/formatted_{timestamp}.html"

    try:
        print_status("正在格式化文稿")

        import time
        start_time = time.time()

        # 格式化
        result = format_transcript(
            str(input_path),
            output_path=output_path,
            config=config,
            method=FormatMethod.RULE_BASED,
            output_format=args.format
        )

        processing_time = time.time() - start_time

        # 显示结果
        print()
        print_success("格式化完成!")
        print()
        print(f"段落数: {result.total_paragraph_count()}")
        print(f"章节数: {len(result.sections)}")
        print(f"总字数: {result.total_word_count()}")
        print(f"处理时间: {processing_time:.2f} 秒")
        print()

        # 显示预览
        print("内容预览:")
        print("-" * 60)
        for section in result.sections[:2]:  # 只显示前两个章节
            for para in section.paragraphs[:2]:  # 每个章节只显示前两段
                preview = para.text[:100] + "..." if len(para.text) > 100 else para.text
                print(preview)
                print()
        if len(result.sections) > 2:
            print(f"... (还有 {len(result.sections) - 2} 个章节)")
        print("-" * 60)
        print()

        print(f"输出文件: {output_path}")

        return 0

    except Exception as e:
        print()
        print_error(f"格式化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


# ============================================
        return 0

    except Exception as e:
        print()
        print_error(f"优化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_refine(args):
    """优化转录文本命令"""
    input_path = Path(args.input)

    if not input_path.exists():
        print_error(f"文件不存在: {args.input}")
        return 1

    # 显示处理信息
    print_header("AI Meeting Assistant - 文稿优化")
    print(f"输入文件: {input_path}")
    print(f"优化模式: {args.mode}")

    if args.rules_only:
        print("模式: 规则优化（不调用 LLM）")
    else:
        print(f"LLM: {args.provider}/{args.model}")
    print()

    # 生成输出路径
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/output/refined_{timestamp}.md"

    try:
        print_status("正在优化文稿")

        import time
        start_time = time.time()

        if args.rules_only:
            # 仅规则优化
            from transcript.refiner import refine_with_rules, RefinerConfig
            from transcript.refiner import RefineMode

            # 读取文件
            if input_path.suffix == '.json':
                import json
                from transcript.load import load_transcript
                document = load_transcript(str(input_path))
                text = document.get_full_text()
            else:
                with open(input_path, 'r', encoding='utf-8') as f:
                    text = f.read()

            # 规则优化
            refined = refine_with_rules(text)

            # 保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(refined)

        else:
            # LLM 优化
            # 创建 LLM provider
            if args.provider == 'glm':
                from summarizer.llm import GLMProvider
                llm = GLMProvider(model=args.model)
            elif args.provider == 'openai':
                from summarizer.llm import OpenAIProvider
                llm = OpenAIProvider(model=args.model)
            else:
                from summarizer.llm import AnthropicProvider
                llm = AnthropicProvider(model=args.model)

            # 优化
            from transcript.refiner import refine_transcript_file, RefineMode

            mode_map = {
                'conservative': RefineMode.CONSERVATIVE,
                'balanced': RefineMode.BALANCED,
                'aggressive': RefineMode.AGGRESSIVE
            }

            output_path = refine_transcript_file(
                str(input_path),
                output_path,
                llm,
                mode=mode_map[args.mode]
            )

        processing_time = time.time() - start_time

        # 显示结果
        print()
        print_success("优化完成!")
        print()
        print(f"处理时间: {processing_time:.2f} 秒")
        print()

        # 显示预览
        print("内容预览:")
        print("-" * 60)
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            preview = content[:500] + "..." if len(content) > 500 else content
            print(preview)
        print("-" * 60)
        print()

        print(f"输出文件: {output_path}")

        return 0

    except Exception as e:
        print()
        print_error(f"优化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


# ============================================
# 辅助函数
# ============================================

def print_header(text: str):
    """打印标题"""
    if RICH_AVAILABLE:
        console.print(f"\n[bold cyan]{text}[/bold cyan]")
    else:
        print(f"\n{'='*60}")
        print(text)
        print(f"{'='*60}")


def print_success(text: str):
    """打印成功消息"""
    if RICH_AVAILABLE:
        console.print(f"[bold green]✓ {text}[/bold green]")
    else:
        print(f"✓ {text}")


def print_error(text: str):
    """打印错误消息"""
    if RICH_AVAILABLE:
        console.print(f"[bold red]✗ {text}[/bold red]")
    else:
        print(f"✗ {text}")


def print_info(text: str):
    """打印信息消息"""
    if RICH_AVAILABLE:
        console.print(f"  {text}")
    else:
        print(f"  {text}")


def print_warning(text: str):
    """打印警告消息"""
    if RICH_AVAILABLE:
        console.print(f"[bold yellow]⚠ {text}[/bold yellow]")
    else:
        print(f"⚠ {text}")


def print_status(text: str):
    """打印状态消息"""
    if RICH_AVAILABLE:
        console.print(f"[dim]{text}...[/dim]")
    else:
        print(f"{text}...")


if __name__ == '__main__':
    sys.exit(main())
