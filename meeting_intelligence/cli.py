#!/usr/bin/env python3
"""
AI 会议内容理解助手 - CLI 工具

真实版本：支持真实音视频文件转录和 LLM 总结。
"""

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

# 加载 .env（可选）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass


# ============================================================
# 数据类型定义
# ============================================================

@dataclass
class Template:
    """用户模板"""
    name: str           # 模板名称（主视角）
    description: str    # 模板描述（增强 Prompt）

    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "description": self.description}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Template":
        return cls(name=data["name"], description=data["description"])


# ============================================================
# 输出目录配置
# ============================================================

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_output_filename(base_name: str, suffix: str, ext: str = "txt") -> Path:
    """
    生成输出文件名

    Args:
        base_name: 基础名称（通常是视频/音频文件名）
        suffix: 后缀（如 "文字稿", "通用总结" 等）
        ext: 文件扩展名（默认: txt）

    Returns:
        输出文件路径
    """
    filename = f"{base_name}_{suffix}.{ext}"
    return OUTPUT_DIR / filename


def get_cache_filename(base_name: str) -> Path:
    """
    生成缓存文件名（用于断点续传）

    Args:
        base_name: 基础名称

    Returns:
        缓存文件路径
    """
    filename = f"{base_name}_enhanced_cache.json"
    return OUTPUT_DIR / filename


# ============================================================
# 模板存储管理
# ============================================================

class TemplateStorage:
    """模板存储管理器"""

    DEFAULT_TEMPLATES = [
        Template(
            name="通用总结",
            description="请提供会议的全面总结，包括主要议题、讨论要点、达成的共识和后续行动计划。"
        ),
        Template(
            name="大学生视角",
            description="从大学生学习的角度总结会议内容，突出重点知识点、学习要点和实际应用价值。"
        )
    ]

    def __init__(self, storage_path: Optional[Path] = None):
        """初始化存储"""
        if storage_path is None:
            self.storage_path = Path(__file__).parent.parent / "templates.json"
        else:
            self.storage_path = storage_path

        self._templates: Dict[str, Template] = {}
        self._load_or_initialize()

    def _load_or_initialize(self) -> None:
        """加载或初始化模板"""
        if self.storage_path.exists():
            self._load()
        else:
            self._initialize_defaults()

    def _load(self) -> None:
        """从文件加载模板"""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._templates = {}
            for item in data.get("templates", []):
                template = Template.from_dict(item)
                self._templates[template.name] = template

        except json.JSONDecodeError as e:
            print(f"警告: JSON 格式错误，将重新初始化模板 ({e})")
            self._initialize_defaults()
        except Exception as e:
            print(f"警告: 加载模板失败，将重新初始化 ({e})")
            self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """初始化默认模板"""
        self._templates = {t.name: t for t in self.DEFAULT_TEMPLATES}
        self.save()

    def save(self) -> None:
        """保存模板到文件"""
        try:
            data = {
                "version": "1.0",
                "templates": [t.to_dict() for t in self._templates.values()]
            }

            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"错误: 保存模板失败 - {e}")

    def list_templates(self) -> List[Template]:
        """列出所有模板"""
        return list(self._templates.values())

    def get_template(self, name: str) -> Optional[Template]:
        """获取指定模板"""
        return self._templates.get(name)

    def add_template(self, template: Template) -> bool:
        """添加模板"""
        if template.name in self._templates:
            return False
        self._templates[template.name] = template
        self.save()
        return True

    def update_template(self, old_name: str, new_name: str = None, new_description: str = None) -> bool:
        """更新模板"""
        if old_name not in self._templates:
            return False

        template = self._templates[old_name]

        if new_name is not None and new_name != old_name:
            if new_name in self._templates:
                return False
            del self._templates[old_name]
            template.name = new_name
            self._templates[new_name] = template
        elif new_name is not None:
            template.name = new_name

        if new_description is not None:
            template.description = new_description

        self.save()
        return True

    def delete_template(self, name: str) -> bool:
        """删除模板"""
        if name not in self._templates:
            return False
        del self._templates[name]
        self.save()
        return True

    def template_exists(self, name: str) -> bool:
        """检查模板是否存在"""
        return name in self._templates


# ============================================================
# LLM 服务
# ============================================================

def create_llm_provider(provider_name: str = "mock", model: str = None):
    """创建 LLM Provider"""
    if provider_name == "mock":
        from summarizer.llm.mock import MockLLMProvider
        return MockLLMProvider()

    elif provider_name == "glm":
        from summarizer.llm.glm import GLMProvider
        api_key = os.environ.get("ZHIPU_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 ZHIPU_API_KEY 环境变量")
        model = model or os.environ.get("DEFAULT_LLM_MODEL", "glm-4-flash")
        return GLMProvider(api_key=api_key, model=model)

    elif provider_name == "openai":
        from summarizer.llm.openai import OpenAIProvider
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 OPENAI_API_KEY 环境变量")
        model = model or os.environ.get("DEFAULT_LLM_MODEL", "gpt-4o-mini")
        return OpenAIProvider(api_key=api_key, model=model)

    elif provider_name == "anthropic":
        from summarizer.llm.anthropic import AnthropicProvider
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 ANTHROPIC_API_KEY 环境变量")
        model = model or os.environ.get("DEFAULT_LLM_MODEL", "claude-3-5-sonnet-20241022")
        return AnthropicProvider(api_key=api_key, model=model)

    elif provider_name == "deepseek":
        from summarizer.llm.deepseek import DeepSeekProvider
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("未设置 DEEPSEEK_API_KEY 环境变量")
        model = model or "deepseek-chat"  # 使用 DeepSeek 默认模型
        return DeepSeekProvider(api_key=api_key, model=model)

    else:
        raise ValueError(f"不支持的 provider: {provider_name}")


# ============================================================
# 主应用类
# ============================================================

class MeetingAssistantCLI:
    """AI 会议内容理解助手 - 主应用（真实版本）"""

    def __init__(self, llm_provider: str = "deepseek"):
        """初始化应用"""
        self.storage = TemplateStorage()
        self.llm_provider_name = llm_provider
        self.current_file_path: Optional[str] = None
        self.current_base_name: Optional[str] = None
        self.transcript_result: Optional[Any] = None
        self.current_transcript_text: Optional[str] = None
        self.running = True

    # --------------------------------------------------------
    # UI 辅助方法
    # --------------------------------------------------------

    @staticmethod
    def print_header(title: str) -> None:
        """打印标题"""
        print("\n" + "=" * 50)
        print(f"  {title}")
        print("=" * 50)

    @staticmethod
    def print_separator() -> None:
        """打印分隔线"""
        print("-" * 50)

    @staticmethod
    def print_success(message: str) -> None:
        """打印成功消息"""
        print(f"✓ {message}")

    @staticmethod
    def print_error(message: str) -> None:
        """打印错误消息"""
        print(f"✗ {message}")

    @staticmethod
    def print_info(message: str) -> None:
        """打印信息消息"""
        print(f"ℹ {message}")

    @staticmethod
    def wait_for_enter(prompt: str = "按 Enter 键继续...") -> None:
        """等待用户按 Enter"""
        input(f"\n{prompt}")

    @staticmethod
    def clear_screen() -> None:
        """清屏"""
        pass

    def show_progress(self, message: str, duration: float = 1.0) -> None:
        """显示进度"""
        print(f"\n{message}...")
        steps = 20
        for i in range(steps + 1):
            percent = int(i / steps * 100)
            bar = "█" * i + "░" * (steps - i)
            print(f"\r  [{bar}] {percent}%", end="", flush=True)
            time.sleep(duration / steps)
        print()  # 换行

    # --------------------------------------------------------
    # 菜单显示
    # --------------------------------------------------------

    def show_main_menu(self) -> None:
        """显示主菜单"""
        provider_info = f" ({self.llm_provider_name})" if self.llm_provider_name != "mock" else ""
        self.print_header(f"AI 会议内容理解助手{provider_info}")
        print("\n请选择操作：")
        print("  1. 上传音视频文件")
        print("  2. 生成文字稿")
        print("  3. 生成会议总结")
        print("  4. 模板管理")
        print("  5. 退出")
        print()

    def show_template_menu(self) -> None:
        """显示模板管理子菜单"""
        self.print_header("模板管理")
        print("\n请选择操作：")
        print("  1. 查看所有模板")
        print("  2. 新建模板")
        print("  3. 编辑模板")
        print("  4. 删除模板")
        print("  5. 返回主菜单")
        print()

    # --------------------------------------------------------
    # 功能实现
    # --------------------------------------------------------

    def upload_file(self) -> None:
        """上传音视频文件"""
        self.print_header("上传音视频文件")

        print("\n请输入文件路径（支持 .mp4, .mkv, .mov, .mp3, .wav, .m4a）")
        print("提示: 可以直接拖拽文件到终端")
        print()

        file_path = self._get_clean_input("文件路径: ", allow_empty=False)
        if not file_path:
            return

        # 清理路径（处理拖拽、URL 编码等）
        file_path = self._clean_file_path(file_path)

        # 检查文件是否存在
        path = Path(file_path)
        if not path.exists():
            self.print_error(f"文件不存在: {file_path}")
            return

        # 检查文件格式
        ext = path.suffix.lower()
        video_extensions = ['.mp4', '.mkv', '.mov']
        audio_extensions = ['.mp3', '.wav', '.m4a']

        if ext not in video_extensions + audio_extensions:
            self.print_error(f"不支持的文件格式: {ext}")
            return

        file_type = "视频" if ext in video_extensions else "音频"

        # 保存文件信息
        self.current_file_path = str(path.absolute())
        self.current_base_name = path.stem
        self.transcript_result = None
        self.current_transcript_text = None

        self.print_success(f"{file_type}文件已加载！")
        self.print_info(f"文件: {path.name}")
        self.print_info(f"类型: {file_type}")

    def generate_transcript(self) -> None:
        """生成文字稿（真实 ASR）"""
        self.print_header("生成文字稿")

        if not self.current_file_path:
            self.print_error("请先上传音视频文件！")
            return

        # 检查文件类型
        path = Path(self.current_file_path)
        ext = path.suffix.lower()

        try:
            # 如果是视频，先提取音频
            if ext in ['.mp4', '.mkv', '.mov']:
                print("\n正在从视频提取音频...")
                self.show_progress("提取音频", duration=0.5)

                from audio.extract_audio import extract_audio
                audio_result = extract_audio(self.current_file_path)
                audio_path = audio_result.path
            else:
                audio_path = self.current_file_path

            # 执行 ASR 转录
            model_size = os.environ.get("WHISPER_MODEL", "base")
            
            # 检查 Whisper 是否安装
            try:
                import whisper
            except ImportError:
                self.print_error("Whisper 未安装！")
                print()
                print("请先安装 Whisper（选择其中一种方式）:")
                print("  1. pip install openai-whisper")
                print("  2. pip install openai-whisper --index-url https://pypi.tuna.tsinghua.edu.cn/simple")
                print()
                self.print_info("安装完成后重新运行即可")
                return
            
            # 检查是否首次使用（模型未下载）
            print(f"\n正在加载 Whisper 模型 ({model_size})...")
            print("提示: 首次使用需要下载模型文件（约 70MB-3GB，取决于模型大小）")
            print("      模型大小: tiny(~40MB) < base(~140MB) < small(~460MB)")
            print("      如果下载时间较长，请耐心等待...")
            print()
            
            from asr.transcribe import transcribe

            self.transcript_result = transcribe(
                audio_path,
                language="auto",
                model_size=model_size
            )

            # 构建纯文本转录
            utterances = self.transcript_result.utterances
            raw_transcript = "\n".join([
                f"[{u.start:.1f}s - {u.end:.1f}s] {u.text}"
                for u in utterances
            ])
            
            # 保存原始文字稿
            raw_output_path = get_output_filename(self.current_base_name, "原始文字稿")
            with open(raw_output_path, "w", encoding="utf-8") as f:
                f.write(f"# 会议原始文字稿\n")
                f.write(f"# 源文件: {path.name}\n")
                f.write(f"# 生成时间: {self.transcript_result.timestamp}\n")
                f.write(f"# ASR提供商: {self.transcript_result.asr_provider}\n")
                f.write(f"# 识别时长: {self.transcript_result.duration:.1f}秒\n")
                f.write(f"# 识别片段: {len(utterances)}条\n\n")
                f.write(raw_transcript)

            self.print_success("原始文字稿生成成功！")
            self.print_info(f"识别片段: {len(utterances)} 条")
            self.print_info(f"原始文件: {raw_output_path.name}")
            
            # 生成 LLM 增强文字稿
            print("\n正在生成 LLM 增强文字稿...")
            try:
                enhanced_transcript = self._create_enhanced_transcript(utterances, path.name)

                # 保存增强文字稿（Markdown 格式）
                # 命名格式: 视频名+文字稿.md
                enhanced_output_path = OUTPUT_DIR / f"{self.current_base_name}文字稿.md"
                with open(enhanced_output_path, "w", encoding="utf-8") as f:
                    f.write(f"# 会议增强文字稿（LLM 优化）\n\n")
                    f.write(f"**源文件:** {path.name}\n")
                    f.write(f"**生成时间:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**LLM Provider:** {self.llm_provider_name}\n")
                    f.write(f"**增强方式:** 带时间戳的纯净实录\n\n")
                    f.write("---\n\n")
                    f.write(enhanced_transcript)

                self.print_success("增强文字稿生成成功！")
                self.print_info(f"增强文件: {enhanced_output_path.name}")

                # 保存到内存用于后续生成总结
                self.current_transcript_text = enhanced_transcript

            except Exception as e:
                self.print_info(f"LLM 增强失败，将使用原始文字稿: {e}")
                self.current_transcript_text = raw_transcript

        except FileNotFoundError as e:
            self.print_error(f"文件不存在: {e}")
        except RuntimeError as e:
            self.print_error(f"处理失败: {e}")
        except Exception as e:
            self.print_error(f"错误: {e}")
            import traceback
            traceback.print_exc()

    def generate_summary(self) -> None:
        """生成会议总结（真实 LLM）"""
        self.print_header("生成会议总结")

        if not self.current_transcript_text:
            self.print_error("请先生成文字稿！")
            return

        # 选择模板
        templates = self.storage.list_templates()
        if not templates:
            self.print_error("没有可用的模板！")
            return

        print("\n请选择模板：")
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template.name}")
        print()

        try:
            choice = int(input("请输入序号: ")) - 1
            if choice < 0 or choice >= len(templates):
                raise ValueError()
        except (ValueError, KeyboardInterrupt):
            self.print_error("无效的选择！")
            return

        selected_template = templates[choice]

        try:
            # 创建 LLM Provider
            print("\n正在初始化 LLM 服务...")
            llm = create_llm_provider(self.llm_provider_name)

            # 构建 Prompt
            prompt = (
                f"你是一名专业会议分析助手。请从【{selected_template.name}】的视角总结以下会议内容。\n"
                f"总结要求：{selected_template.description}。\n"
                f"请使用结构化方式输出。\n\n"
                f"会议内容：\n{self.current_transcript_text}"
            )

            print(f"\n使用模板：【{selected_template.name}】")
            print(f"LLM Provider: {self.llm_provider_name}")
            print()

            # 调用 LLM
            print("正在生成总结...")
            if self.llm_provider_name == "mock":
                self.show_progress("生成中", duration=1.0)
            else:
                print("(这可能需要几十秒...)")

            from summarizer.llm.base import LLMMessage
            messages = [LLMMessage(role="user", content=prompt)]
            
            # 使用重试机制调用 LLM
            try:
                summary_text = self._call_llm_with_retry(llm, messages)
            except Exception as e:
                error_msg = str(e)
                # 提供更友好的错误提示
                if '429' in error_msg or '1302' in error_msg or 'rate' in error_msg.lower() or 'limit' in error_msg.lower() or '速率限制' in error_msg:
                    self.print_error("API 速率限制（已重试 5 次）")
                    print()
                    print("LLM API 额度限制，建议：")
                    print()
                    print("【选项1】等待后重试")
                    print(f"  当前使用: {self.llm_provider_name}")
                    print("  建议: 等待 2-3 分钟后再试")
                    print()
                    print("【选项2】切换其他 LLM Provider")
                    print("  python meeting_cli.py --llm openai   # OpenAI GPT")
                    print("  python meeting_cli.py --llm anthropic  # Claude")
                    print("  python meeting_cli.py --llm mock      # 测试模式")
                    print()
                    print("【选项3】保存草稿")
                    print("  已生成原始文字稿和增强文字稿")
                    print("  可手动复制 LLM prompt 到其他平台生成总结")
                    print()

                    # 保存 prompt 供用户使用
                    prompt_file = get_output_filename(self.current_base_name, "LLM_Prompt")
                    with open(prompt_file, "w", encoding="utf-8") as f:
                        f.write(f"# LLM Prompt - 用于生成总结\n")
                        f.write(f"# 源文件: {Path(self.current_file_path).name}\n")
                        f.write(f"# 模板: {selected_template.name}\n\n")
                        f.write(prompt)

                    self.print_info(f"Prompt 已保存到: {prompt_file.name}")
                    self.print_info("可将 Prompt 复制到其他 LLM 平台生成总结")
                    return
                else:
                    raise

            # 保存总结（Markdown 格式）
            # 命名格式: 视频名+总结模板名+总结.md
            output_path = OUTPUT_DIR / f"{self.current_base_name}{selected_template.name}总结.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# 会议总结 - {selected_template.name}\n\n")
                f.write(f"**源文件:** {Path(self.current_file_path).name}\n")
                f.write(f"**模板:** {selected_template.name}\n")
                f.write(f"**模板描述:** {selected_template.description}\n")
                f.write(f"**LLM Provider:** {self.llm_provider_name}\n")
                f.write(f"**生成时间:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                f.write(summary_text)

            self.print_success("会议总结生成成功！")
            self.print_info(f"输出文件: {output_path.name}")

            # 显示结果
            print("\n" + "=" * 50)
            print("会议总结")
            print("=" * 50)
            print(summary_text)
            print("=" * 50)

        except RuntimeError as e:
            self.print_error(f"LLM 服务错误: {e}")
            self.print_info("请检查环境变量配置（API Key）")
        except Exception as e:
            self.print_error(f"错误: {e}")
            import traceback
            traceback.print_exc()

    # --------------------------------------------------------
    # 模板管理
    # --------------------------------------------------------

    def template_list(self) -> None:
        """查看所有模板"""
        self.print_header("模板列表")

        templates = self.storage.list_templates()
        if not templates:
            self.print_info("暂无模板")
            self.wait_for_enter()
            return

        print(f"\n共有 {len(templates)} 个模板：\n")
        for i, template in enumerate(templates, 1):
            print(f"  [{i}] {template.name}")
            print(f"      描述: {template.description}")
            print()

    def template_create(self) -> None:
        """新建模板"""
        self.print_header("新建模板")

        print("\n请输入模板信息：\n")

        name = self._get_clean_input("模板名称（主视角）: ", allow_empty=False)
        if not name:
            return

        if self.storage.template_exists(name):
            self.print_error(f"模板「{name}」已存在！")
            self.wait_for_enter()
            return

        description = self._get_clean_input("模板描述（增强 Prompt）: ", allow_empty=False)
        if not description:
            return

        template = Template(name=name, description=description)

        if self.storage.add_template(template):
            self.print_success(f"模板「{name}」创建成功！")
        else:
            self.print_error("创建模板失败！")

        self.wait_for_enter()

    def template_edit(self) -> None:
        """编辑模板"""
        self.print_header("编辑模板")

        templates = self.storage.list_templates()
        if not templates:
            self.print_info("暂无模板可编辑")
            self.wait_for_enter()
            return

        print("\n请选择要编辑的模板：")
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template.name}")
        print("  0. 取消")
        print()

        try:
            choice = int(input("请输入序号: "))
            if choice == 0:
                return
            if choice < 1 or choice > len(templates):
                raise ValueError()
        except (ValueError, KeyboardInterrupt):
            self.print_error("无效的选择！")
            return

        selected_template = templates[choice - 1]

        # 显示当前信息
        print(f"\n当前模板信息：")
        print(f"  名称: {selected_template.name}")
        print(f"  描述: {selected_template.description}")
        print()

        # 选择编辑内容
        print("请选择要修改的内容：")
        print("  1. 仅修改名称")
        print("  2. 仅修改描述")
        print("  3. 同时修改名称和描述")
        print("  0. 取消")
        print()

        try:
            edit_choice = int(input("请选择: "))
            if edit_choice == 0:
                return
            if edit_choice not in (1, 2, 3):
                raise ValueError()
        except (ValueError, KeyboardInterrupt):
            self.print_error("无效的选择！")
            return

        new_name = None
        new_description = None

        if edit_choice in (1, 3):
            print(f"\n当前名称: {selected_template.name}")
            new_name = self._get_clean_input("请输入新名称: ", allow_empty=False)

            if new_name and new_name != selected_template.name and self.storage.template_exists(new_name):
                self.print_error(f"模板「{new_name}」已存在！")
                self.wait_for_enter()
                return

        if edit_choice in (2, 3):
            print(f"\n当前描述: {selected_template.description}")
            new_description = self._get_clean_input("请输入新描述: ", allow_empty=False)

        # 执行更新
        if self.storage.update_template(selected_template.name, new_name, new_description):
            if new_name and new_name != selected_template.name:
                self.print_success(f"模板「{selected_template.name}」已更新为「{new_name}」！")
            else:
                self.print_success(f"模板「{selected_template.name}」已更新！")
        else:
            self.print_error("更新失败！")

        self.wait_for_enter()

    def template_delete(self) -> None:
        """删除模板"""
        self.print_header("删除模板")

        templates = self.storage.list_templates()
        if not templates:
            self.print_info("暂无模板可删除")
            self.wait_for_enter()
            return

        print("\n请选择要删除的模板：")
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template.name}")
        print("  0. 取消")
        print()

        try:
            choice = int(input("请输入序号: "))
            if choice == 0:
                return
            if choice < 1 or choice > len(templates):
                raise ValueError()
        except (ValueError, KeyboardInterrupt):
            self.print_error("无效的选择！")
            return

        selected_template = templates[choice - 1]

        # 确认删除
        confirm = input(f"\n确认删除模板「{selected_template.name}」？(y/n): ").strip().lower()
        if confirm != 'y':
            self.print_info("已取消删除")
            self.wait_for_enter()
            return

        if self.storage.delete_template(selected_template.name):
            self.print_success(f"模板「{selected_template.name}」已删除！")
        else:
            self.print_error("删除失败！")

        self.wait_for_enter()

    def manage_templates(self) -> None:
        """模板管理子菜单循环"""
        while self.running:
            self.clear_screen()
            self.show_template_menu()

            try:
                choice = input("请选择操作: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "1":
                self.clear_screen()
                self.template_list()
            elif choice == "2":
                self.clear_screen()
                self.template_create()
            elif choice == "3":
                self.clear_screen()
                self.template_edit()
            elif choice == "4":
                self.clear_screen()
                self.template_delete()
            elif choice == "5":
                break
            else:
                self.print_error("无效的选择，请重新输入！")
                time.sleep(0.5)

    def _clean_file_path(self, file_path: str) -> str:
        """清理文件路径，处理拖拽和各种格式"""
        if not file_path:
            return file_path
        
        # 去除首尾空格和引号
        path = file_path.strip().strip('"').strip("'")
        
        # 处理 URL 格式 (file:///)
        if path.startswith('file://'):
            path = path[7:]
            # 去除可能的额外斜杠
            while path.startswith('/'):
                path = path[1:]
        
        # 处理 Windows 路径 (C:/ 或 C:\) - 转换为 WSL 格式
        # 检测 Windows 路径格式：盘符:/
        if len(path) >= 3 and path[1] == ':' and path[2] in '/\\\\':
            # 提取盘符
            drive = path[0].lower()
            # 获取盘符后的路径部分
            rest_path = path[3:]
            # 转换反斜杠为正斜杠
            rest_path = rest_path.replace(chr(92), '/')
            # 构建 WSL 路径
            path = f'/mnt/{drive}/{rest_path}'
        
        # 处理纯反斜杠的 Windows 路径 (C:\Users\...)
        elif chr(92) in path and ':' in path:
            path = path.replace(chr(92), '/')
            # 再次检查是否需要 WSL 转换
            if len(path) >= 3 and path[1] == ':' and path[2] == '/':
                drive = path[0].lower()
                rest_path = path[3:]
                path = f'/mnt/{drive}/{rest_path}'
        
        # 去除 URL 编码 (%20 -> 空格)
        path = re.sub(r'%20', ' ', path)
        path = re.sub(r'%2F', '/', path)
        path = re.sub(r'%5C', '/', path)
        
        return path

    def _ms_to_mmss(self, ms: int) -> str:
        """将毫秒转换为 MM:SS 格式"""
        seconds = ms // 1000
        mm = seconds // 60
        ss = seconds % 60
        return f"{mm:02d}:{ss:02d}"

    def _create_time_blocks(self, utterances: list, block_duration_minutes: int = 3) -> list:
        """
        将 utterances 按时间跨度聚合为时间块
        
        Args:
            utterances: 原始 utterance 列表（Utterance 对象）
            block_duration_minutes: 每块的时长（分钟）
            
        Returns:
            时间块列表
        """
        if not utterances:
            return []
        
        block_duration_ms = block_duration_minutes * 60 * 1000
        blocks = []
        
        current_block = {
            "start_ms": int(utterances[0].start * 1000),
            "end_ms": int(utterances[0].end * 1000),
            "text": "",
        }
        
        for u in utterances:
            u_start_ms = int(u.start * 1000)
            u_end_ms = int(u.end * 1000)
            
            # 检查是否应该开始新块
            if u_start_ms >= current_block["start_ms"] + block_duration_ms and current_block["text"]:
                # 保存当前块
                blocks.append({
                    "start_ms": current_block["start_ms"],
                    "end_ms": current_block["end_ms"],
                    "text": current_block["text"].strip()
                })
                # 开始新块
                current_block = {
                    "start_ms": u_start_ms,
                    "end_ms": u_end_ms,
                    "text": "",
                }
            
            current_block["end_ms"] = max(current_block["end_ms"], u_end_ms)
            current_block["text"] += " " + u.text
        
        # 添加最后一个块
        if current_block["text"].strip():
            blocks.append({
                "start_ms": current_block["start_ms"],
                "end_ms": current_block["end_ms"],
                "text": current_block["text"].strip()
            })
        
        return blocks


    def _create_enhanced_transcript(self, utterances: list, source_filename: str) -> str:
        """
        创建 LLM 增强的转录文本（带时间戳的纯净实录）
        支持断点续传功能。

        Args:
            utterances: Whisper 识别的 utterances 列表
            source_filename: 源文件名

        Returns:
            增强后的转录文本
        """
        from template.recorder import get_recorder_prompts
        from summarizer.llm.base import LLMMessage

        # 创建时间块（每3分钟一块）
        time_blocks = self._create_time_blocks(utterances, block_duration_minutes=3)

        print(f"      ✓ 创建了 {len(time_blocks)} 个时间块")

        # 检查是否有缓存（断点续传）
        cache_file = get_cache_filename(self.current_base_name)
        start_index = 0
        refined_lines = []

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    # 验证缓存是否匹配当前文件
                    if cache.get("source_filename") == source_filename:
                        start_index = cache.get("processed_count", 0)
                        refined_lines = cache.get("refined_lines", [])
                        print(f"      ✓ 从缓存恢复，已处理 {start_index}/{len(time_blocks)} 个块")
                    else:
                        print(f"      ⚠ 缓存文件不匹配，将从头开始")
            except Exception as e:
                print(f"      ⚠ 读取缓存失败: {e}，将从头开始")

        # 处理时间块
        llm = create_llm_provider(self.llm_provider_name)

        # 请求间隔延迟（秒），避免触发速率限制
        REQUEST_DELAY = 3

        # 导入 tqdm
        try:
            from tqdm import tqdm
        except ImportError:
            print("      ⚠ 未安装 tqdm，请运行: pip install tqdm")
            # 使用简单的列表作为备用
            class SimpleTqdm:
                def __init__(self, total, initial=0, unit="", desc="", **kwargs):
                    self.total = total
                    self.n = initial
                    self.unit = unit
                    self.desc = desc
                def __iter__(self):
                    return iter(range(self.n, self.total))
                def update(self, n=1):
                    self.n += n
                    print(f"  {self.desc}: {self.n}/{self.total}")
                def set_description(self, desc):
                    self.desc = desc
                def set_postfix(self, postfix):
                    pass
                def write(self, msg):
                    print(msg)
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            tqdm = SimpleTqdm

        # 创建进度条
        total_blocks = len(time_blocks)
        with tqdm(total=total_blocks, initial=start_index,
                  unit="块", desc="生成增强文字稿",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:

            for i in range(start_index, total_blocks):
                block = time_blocks[i]
                start_time = self._ms_to_mmss(block["start_ms"])
                end_time = self._ms_to_mmss(block["end_ms"])

                # 更新进度条描述，显示当前处理的时间段
                pbar.set_description(f"[{start_time} - {end_time}] 处理中")

                # 获取提示词
                prompts = get_recorder_prompts(block["text"])

                messages = [
                    LLMMessage(role="system", content=prompts["system_prompt"]),
                    LLMMessage(role="user", content=prompts["user_prompt"])
                ]

                # 调用 LLM（带重试）
                try:
                    refined_text = self._call_llm_with_retry(llm, messages, max_retries=5)
                except Exception as e:
                    # 在进度条后缀显示错误
                    pbar.write(f"  ✗ 块 {i+1} 处理失败，使用原文: {e}")
                    refined_text = block["text"]

                # 清洗文本
                import re
                refined_text = refined_text.strip()
                refined_text = re.sub(r'\n{3,}', '\n\n', refined_text)

                # 添加时间戳
                refined_line = f"[{start_time} - {end_time}] {refined_text}"
                refined_lines.append(refined_line)

                # 保存进度到缓存
                cache_data = {
                    "source_filename": source_filename,
                    "total_blocks": total_blocks,
                    "processed_count": i + 1,
                    "refined_lines": refined_lines,
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    pbar.write(f"  ⚠ 保存缓存失败: {e}")

                # 更新进度
                pbar.update(1)

                # 在请求之间添加延迟（最后一个块不需要）
                if i < total_blocks - 1:
                    # 显示等待倒计时
                    pbar.set_description(f"[{start_time} - {end_time}] 等待中")
                    for wait_i in range(REQUEST_DELAY):
                        time.sleep(1)
                        # 更新后缀显示剩余等待时间
                        pbar.set_postfix({"等待": f"{REQUEST_DELAY - wait_i}s"})

        # 删除缓存文件（成功完成）
        if cache_file.exists():
            try:
                cache_file.unlink()
                print(f"      ✓ 清理缓存文件")
            except Exception:
                pass

        return "\n\n".join(refined_lines)



    def _call_llm_with_retry(self, llm, messages: list, max_retries: int = 5) -> str:
        """
        带重试的 LLM 调用

        Args:
            llm: LLM Provider
            messages: 消息列表
            max_retries: 最大重试次数（默认 5 次）

        Returns:
            LLM 响应内容
        """
        import time

        for attempt in range(max_retries):
            try:
                response = llm.generate(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=4000
                )
                return response.content if hasattr(response, 'content') else str(response)

            except Exception as e:
                error_msg = str(e)
                # 检查是否是速率限制错误
                is_rate_limit = (
                    '429' in error_msg or
                    '速率限制' in error_msg or
                    '1302' in error_msg or
                    'rate limit' in error_msg.lower()
                )

                if is_rate_limit and attempt < max_retries - 1:
                    # 指数退避：10, 20, 30, 40, 50 秒
                    wait_time = 10 + (attempt * 10)
                    print(f"      遇到速率限制，等待 {wait_time} 秒后重试... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise


    def _get_clean_input(self, prompt: str, allow_empty: bool = False) -> str:
        """获取用户输入，清理前后空格"""
        while True:
            try:
                value = input(prompt)
                if value.endswith('\n'):
                    value = value[:-1]
                if value.endswith('\r'):
                    value = value[:-1]

                value = value.strip()

                if not value and not allow_empty:
                    self.print_error("输入不能为空！")
                    continue

                return value
            except (EOFError, KeyboardInterrupt):
                print("\n操作已取消")
                return ""

    # --------------------------------------------------------
    # 主循环
    # --------------------------------------------------------

    def run(self) -> None:
        """运行主循环"""
        while self.running:
            self.clear_screen()
            self.show_main_menu()

            try:
                choice = input("请选择操作: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n再见！")
                break

            if choice == "1":
                self.clear_screen()
                self.upload_file()
                self.wait_for_enter()
            elif choice == "2":
                self.clear_screen()
                self.generate_transcript()
                self.wait_for_enter()
            elif choice == "3":
                self.clear_screen()
                self.generate_summary()
                self.wait_for_enter()
            elif choice == "4":
                self.manage_templates()
            elif choice == "5":
                print("\n再见！")
                break
            else:
                self.print_error("无效的选择，请重新输入！")
                time.sleep(0.5)


# ============================================================
# 入口函数
# ============================================================

def main(llm_provider: str = "deepseek"):
    """
    程序入口

    Args:
        llm_provider: LLM 提供商 (mock, glm, openai, anthropic)
    """
    cli = MeetingAssistantCLI(llm_provider=llm_provider)
    cli.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI 会议内容理解助手")
    parser.add_argument("--llm", "-l", default="deepseek",
                       choices=["mock", "glm", "openai", "anthropic", "deepseek"],
                       help="LLM 提供商（默认: deepseek）")

    args = parser.parse_args()

    main(llm_provider=args.llm)
