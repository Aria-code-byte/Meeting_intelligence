#!/usr/bin/env python3
"""
CLI 业务逻辑包装层
==================
核心原则：逻辑注入而非重写
- 直接调用 CLI 核心函数
- 100% 保留原有逻辑
- 添加进度回调支持 SSE 流式输出

单一真理来源: meeting_intelligence/__main__.py
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

# ============================================================
# 导入 CLI 核心模块（单一真理来源）
# ============================================================
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from meeting_intelligence.__main__ import (
    create_llm_provider,
    enhance_transcript,
    refine_transcript_with_timestamps,
    get_output_timestamp,
    OUTPUT_DIR as CLI_OUTPUT_DIR,
)

from asr.transcribe import transcribe as asr_transcribe
from asr.types import Utterance
from audio.extract_audio import extract_audio


# ============================================================
# 数据类型定义
# ============================================================

@dataclass
class ProcessRequest:
    """处理请求（对应 CLI argparse 参数）"""
    input_path: str                           # 对应 'input'
    template: str = "general"                 # 对应 '--template', 默认: general
    provider: str = "mock"                    # 对应 '--provider', 默认: mock
    model: Optional[str] = None               # 对应 '--model'
    no_save: bool = False                     # 对应 '--no-save'

    # 内部常量（从 CLI 提取）
    block_duration_minutes: int = 3           # __main__.py 中硬编码

    def to_dict(self) -> dict:
        return {
            "input_path": self.input_path,
            "template": self.template,
            "provider": self.provider,
            "model": self.model,
            "no_save": self.no_save,
        }


@dataclass
class ProcessResult:
    """处理结果（对应 CLI 输出文件内容）"""
    # 元数据
    timestamp: str
    input_path: str
    base_name: str
    processing_time: float

    # ASR 结果
    transcript_doc: dict

    # 步骤 1: 原始转录
    transcript_raw_path: Optional[str] = None
    utterance_count: int = 0

    # 步骤 2: 增强文稿（书面化）
    enhanced_text: Optional[str] = None
    enhanced_path: Optional[str] = None

    # 步骤 3: 带时间索引的纯净实录
    refined_text: Optional[str] = None
    refined_path: Optional[str] = None

    # 状态
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ProgressEvent:
    """进度事件（用于 SSE 推送）"""
    stage: str           # stage: asr, enhance, refine, complete
    step: int            # 当前步骤 (1/3, 2/3, 3/3)
    progress: int        # 进度百分比 0-100
    message: str         # 描述信息
    data: Optional[dict] = None  # 附加数据


# ============================================================
# CLI 逻辑包装器（核心）
# ============================================================

class CLIMeetingProcessor:
    """
    CLI 会议处理器

    核心原则：
    1. 直接调用 CLI 函数，不重写逻辑
    2. 添加进度回调支持 SSE
    3. 保留所有 CLI 常量和参数
    """

    def __init__(
        self,
        request: ProcessRequest,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None
    ):
        """
        初始化处理器

        Args:
            request: 处理请求（CLI 参数）
            progress_callback: 进度回调函数
        """
        self.request = request
        self.progress_callback = progress_callback
        self.start_time = time.time()

    def _emit_progress(self, stage: str, step: int, progress: int, message: str, data: dict = None):
        """发送进度事件"""
        if self.progress_callback:
            event = ProgressEvent(
                stage=stage,
                step=step,
                progress=progress,
                message=message,
                data=data
            )
            self.progress_callback(event)

    def _validate_input(self) -> Path:
        """
        验证输入文件（对应 CLI __main__.py:446-460）

        Returns:
            Path: 验证后的文件路径

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        input_path = Path(self.request.input_path)

        # 验证文件存在
        if not input_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.request.input_path}")

        # 验证文件格式
        video_extensions = ['.mp4', '.mkv', '.mov']
        audio_extensions = ['.mp3', '.wav', '.m4a']
        ext = input_path.suffix.lower()

        if ext not in video_extensions + audio_extensions:
            raise ValueError(f"不支持的文件格式: {ext}")

        return input_path

    async def process(self) -> ProcessResult:
        """
        执行完整处理流程（对应 CLI main() 函数）

        流程：
        1. [Step 1/3] ASR 转写
        2. [Step 2/3] 增强文稿（书面化）
        3. [Step 3/3] 带时间索引的纯净实录

        Returns:
            ProcessResult: 处理结果
        """
        try:
            # 验证输入
            input_path = self._validate_input()
            ext = input_path.suffix.lower()
            base_name = input_path.stem
            timestamp = get_output_timestamp()

            self._emit_progress("init", 0, 0, f"开始处理: {input_path.name}")

            # ============================================================
            # 步骤 1: ASR 转写（对应 CLI __main__.py:478-501）
            # ============================================================
            self._emit_progress("asr", 1, 5, "[1/3] 原始转录中...")

            # 音频提取（如果是视频）
            if ext in ['.mp4', '.mkv', '.mov']:
                self._emit_progress("asr", 1, 10, "正在从视频提取音频...")
                audio_result = await asyncio.to_thread(extract_audio, str(input_path))
                audio_path = audio_result.path
            else:
                audio_path = str(input_path)

            # 执行 ASR 转写（直接调用 CLI 函数）
            self._emit_progress("asr", 1, 20, "正在执行 ASR 转写...")
            asr_result = await asyncio.to_thread(
                asr_transcribe,
                audio_path
            )

            # 读取 ASR 结果（对应 CLI __main__.py:484-495）
            with open(asr_result.output_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)

            transcript_doc = {
                'utterances': transcript_data['utterances'],
                'audio_path': transcript_data['audio_path'],
                'duration': transcript_data['duration'],
                'asr_provider': transcript_data['asr_provider'],
                'timestamp': transcript_data.get('timestamp'),
                'document_path': asr_result.output_path
            }

            self._emit_progress("asr", 1, 33, f"[1/3] 原始转录已保存 - 识别了 {len(transcript_data['utterances'])} 个片段", {
                "utterance_count": len(transcript_data['utterances']),
                "transcript_path": asr_result.output_path
            })

            # ============================================================
            # 步骤 2: 增强文稿（书面化）（对应 CLI __main__.py:504-528）
            # ============================================================
            self._emit_progress("enhance", 2, 35, "[2/3] 增强文稿（书面化）中...")

            # 创建 LLM Provider（直接调用 CLI 函数）
            llm = create_llm_provider(self.request.provider, self.request.model)

            # 增强转录（直接调用 CLI 函数）
            enhanced_text = await asyncio.to_thread(
                enhance_transcript,
                transcript_doc,
                llm,
                self.request.template
            )

            # 保存增强文稿（对应 CLI __main__.py:517-522）
            enhanced_path = None
            if not self.request.no_save:
                enhanced_path = CLI_OUTPUT_DIR / f"{base_name}_enhanced_{timestamp}.txt"
                with open(enhanced_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_text)

            self._emit_progress("enhance", 2, 66, "[2/3] 增强文稿（书面化）已保存", {
                "enhanced_path": str(enhanced_path) if enhanced_path else None
            })

            # ============================================================
            # 步骤 3: 带时间索引的纯净实录（对应 CLI __main__.py:531-560）
            # ============================================================
            self._emit_progress("refine", 3, 70, "[3/3] 带时间索引的纯净实录生成中...")

            # 生成带时间戳的实录（直接调用 CLI 函数）
            refined_text = await asyncio.to_thread(
                refine_transcript_with_timestamps,
                transcript_doc,
                llm,
                self.request.block_duration_minutes
            )

            # 保存实录文件（对应 CLI __main__.py:548-553）
            refined_path = None
            if not self.request.no_save:
                refined_path = CLI_OUTPUT_DIR / f"{base_name}_refined_{timestamp}.txt"
                with open(refined_path, 'w', encoding='utf-8') as f:
                    f.write(refined_text)

            processing_time = time.time() - self.start_time
            self._emit_progress("complete", 3, 100, f"[3/3] 带时间索引的纯净实录已生成 - 处理时间: {processing_time:.2f} 秒", {
                "refined_path": str(refined_path) if refined_path else None,
                "processing_time": processing_time
            })

            # 返回结果
            return ProcessResult(
                timestamp=timestamp,
                input_path=str(input_path),
                base_name=base_name,
                processing_time=processing_time,
                transcript_doc=transcript_doc,
                transcript_raw_path=asr_result.output_path,
                utterance_count=len(transcript_data['utterances']),
                enhanced_text=enhanced_text,
                enhanced_path=str(enhanced_path) if enhanced_path else None,
                refined_text=refined_text,
                refined_path=str(refined_path) if refined_path else None,
            )

        except Exception as e:
            processing_time = time.time() - self.start_time
            self._emit_progress("error", 0, 0, f"处理失败: {str(e)}")

            return ProcessResult(
                timestamp=get_output_timestamp(),
                input_path=self.request.input_path,
                base_name=Path(self.request.input_path).stem,
                processing_time=processing_time,
                transcript_doc={},
                success=False,
                error_message=str(e)
            )


# ============================================================
# 分步处理 API（用于更细粒度的控制）
# ============================================================

class CLIStepProcessor:
    """
    CLI 分步处理器

    提供单独的处理步骤，对应 CLI 的各个函数
    """

    @staticmethod
    async def step_1_transcribe(
        input_path: str,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        步骤 1: ASR 转写（对应 CLI __main__.py:478-501）

        Args:
            input_path: 输入文件路径
            progress_callback: 进度回调

        Returns:
            dict: 转录结果
        """
        if progress_callback:
            progress_callback(ProgressEvent(
                stage="asr", step=1, progress=10,
                message="[1/3] 原始转录中..."
            ))

        input_path = Path(input_path)
        ext = input_path.suffix.lower()

        # 音频提取
        if ext in ['.mp4', '.mkv', '.mov']:
            audio_result = await asyncio.to_thread(extract_audio, str(input_path))
            audio_path = audio_result.path
        else:
            audio_path = str(input_path)

        # ASR 转写
        asr_result = await asyncio.to_thread(asr_transcribe, audio_path)

        with open(asr_result.output_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        if progress_callback:
            progress_callback(ProgressEvent(
                stage="asr", step=1, progress=100,
                message="[1/3] 原始转录完成",
                data={"utterance_count": len(transcript_data['utterances'])}
            ))

        return transcript_data

    @staticmethod
    async def step_2_enhance(
        transcript_doc: dict,
        provider: str = "mock",
        model: Optional[str] = None,
        template: str = "general",
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        步骤 2: 增强文稿（对应 CLI __main__.py:504-528）

        Args:
            transcript_doc: 转录文档
            provider: LLM 提供商
            model: LLM 模型
            template: 模板名称
            progress_callback: 进度回调

        Returns:
            str: 增强后的文本
        """
        if progress_callback:
            progress_callback(ProgressEvent(
                stage="enhance", step=2, progress=10,
                message="[2/3] 增强文稿（书面化）中..."
            ))

        llm = create_llm_provider(provider, model)
        enhanced_text = await asyncio.to_thread(
            enhance_transcript,
            transcript_doc,
            llm,
            template
        )

        if progress_callback:
            progress_callback(ProgressEvent(
                stage="enhance", step=2, progress=100,
                message="[2/3] 增强文稿完成"
            ))

        return enhanced_text

    @staticmethod
    async def step_3_refine(
        transcript_doc: dict,
        provider: str = "mock",
        model: Optional[str] = None,
        block_duration_minutes: int = 3,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        步骤 3: 带时间戳实录（对应 CLI __main__.py:531-560）

        Args:
            transcript_doc: 转录文档
            provider: LLM 提供商
            model: LLM 模型
            block_duration_minutes: 时间块时长（分钟）
            progress_callback: 进度回调

        Returns:
            str: 带时间戳的实录文本
        """
        if progress_callback:
            progress_callback(ProgressEvent(
                stage="refine", step=3, progress=10,
                message="[3/3] 带时间索引的纯净实录生成中..."
            ))

        llm = create_llm_provider(provider, model)
        refined_text = await asyncio.to_thread(
            refine_transcript_with_timestamps,
            transcript_doc,
            llm,
            block_duration_minutes
        )

        if progress_callback:
            progress_callback(ProgressEvent(
                stage="refine", step=3, progress=100,
                message="[3/3] 带时间索引的纯净实录完成"
            ))

        return refined_text
