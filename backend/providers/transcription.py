"""
Transcription Provider
====================
音频转录服务提供商适配器

支持：
- FallbackTranscriptionProvider: 模拟转录（测试/开发用）
- WhisperTranscriptionProvider: 真实 Whisper ASR（需要安装 whisper 包）
- WhisperXTranscriptionProvider: WhisperX + pyannote 说话人分离（阶段 10B-3 新增）
"""
import os
import time
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base import BaseProvider, ProviderResult, ProviderType


# ============================================================
# 环境变量读取
# ============================================================

def _get_env(key: str, default: Any = None) -> Any:
    """安全读取环境变量"""
    value = os.getenv(key, default)
    if value is None or value == "":
        return default
    if isinstance(default, bool):
        return str(value).lower() in ("true", "1", "yes", "on")
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    return value


# WhisperX 环境变量
TRANSCRIPTION_PROVIDER = _get_env("TRANSCRIPTION_PROVIDER", _get_env("AI_TRANSCRIPTION_PROVIDER", "fallback"))
WHISPERX_MODEL = _get_env("WHISPERX_MODEL", "large-v3-turbo")
WHISPERX_LANGUAGE = _get_env("WHISPERX_LANGUAGE", "zh")
WHISPERX_DEVICE = _get_env("WHISPERX_DEVICE", "auto")
WHISPERX_COMPUTE_TYPE = _get_env("WHISPERX_COMPUTE_TYPE", None)
WHISPERX_BATCH_SIZE = _get_env("WHISPERX_BATCH_SIZE", 16)
WHISPERX_SKIP_ALIGN = _get_env("WHISPERX_SKIP_ALIGN", False)
DIARIZATION_ENABLED = _get_env("DIARIZATION_ENABLED", True)
PYANNOTE_DIARIZE_MODEL = _get_env("PYANNOTE_DIARIZE_MODEL", "pyannote/speaker-diarization-community-1")
HF_TOKEN = _get_env("HF_TOKEN") or _get_env("HUGGINGFACE_TOKEN")
DIARIZATION_MIN_SPEAKERS = _get_env("DIARIZATION_MIN_SPEAKERS", None)
DIARIZATION_MAX_SPEAKERS = _get_env("DIARIZATION_MAX_SPEAKERS", None)
DIARIZATION_MERGE_GAP = _get_env("DIARIZATION_MERGE_GAP", 1.0)


class FallbackTranscriptionProvider(BaseProvider):
    """回退转录提供商（模拟）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider_type = ProviderType.FALLBACK

    def transcribe(self, audio_path: str, **kwargs) -> ProviderResult:
        """
        模拟转录（回退模式）

        Args:
            audio_path: 音频文件路径（此参数在 fallback 模式下不使用）
            **kwargs: 额外参数

        Returns:
            ProviderResult with mock transcript
        """
        start_time = time.time()

        mock_transcript = """[00:00:01] Speaker 1：本次会议主要讨论项目进展。
[00:00:15] Speaker 2：前端开发已完成80%。
[00:00:30] Speaker 1：很好，后端API进展如何？
[00:00:45] Speaker 2：后端API开发已完成60%，预计本周内完成。
[00:01:00] Speaker 1：好的，继续保持。
[00:01:15] Speaker 2：还有个问题需要讨论，关于用户认证模块的设计。
[00:01:30] Speaker 1：这个问题我们需要在下次会议详细讨论。"""

        processing_time = int((time.time() - start_time) * 1000)

        return ProviderResult(
            success=True,
            data={
                "transcript": mock_transcript,
                "segments": [
                    {"start": "00:00:01", "speaker": "Speaker 1", "text": "本次会议主要讨论项目进展。"},
                    {"start": "00:00:15", "speaker": "Speaker 2", "text": "前端开发已完成80%。"},
                    {"start": "00:00:30", "speaker": "Speaker 1", "text": "很好，后端API进展如何？"},
                    {"start": "00:00:45", "speaker": "Speaker 2", "text": "后端API开发已完成60%，预计本周内完成。"},
                    {"start": "01:00:00", "speaker": "Speaker 1", "text": "好的，继续保持。"},
                    {"start": "01:01:15", "speaker": "Speaker 2", "text": "还有个问题需要讨论，关于用户认证模块的设计。"},
                    {"start": "01:01:30", "speaker": "Speaker 1", "text": "这个问题我们需要在下次会议详细讨论。"}
                ],
                "duration": 90,
                "word_count": len(mock_transcript.split()),
                "model": "fallback"
            },
            provider=self.provider_type,
            is_fallback=True,
            processing_time_ms=processing_time
        )


class WhisperTranscriptionProvider(BaseProvider):
    """Whisper ASR 转录提供商（真实调用）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider_type = ProviderType.BACKEND
        self.model_size = config.get("model_size", "base") if config else "base"
        self.language = config.get("language", "zh") if config else "zh"
        self.device = config.get("device", "auto") if config else "auto"

    def is_available(self) -> bool:
        """检查 Whisper 是否可用"""
        try:
            # 检查 ASR 模块是否可用
            from asr.transcribe import transcribe
            # 检查音频处理模块是否可用
            from audio.extract_audio import _get_audio_duration
            return True
        except ImportError as e:
            print(f"[WhisperTranscriptionProvider] Import error: {e}")
            return False
        except Exception as e:
            print(f"[WhisperTranscriptionProvider] Availability check failed: {e}")
            return False

    def transcribe(self, audio_path: str, **kwargs) -> ProviderResult:
        """
        使用 Whisper 进行真实转录

        Args:
            audio_path: 音频文件路径
            **kwargs: 额外参数（model_size, language等）

        Returns:
            ProviderResult with transcript
        """
        start_time = time.time()
        start_datetime = datetime.now()

        try:
            # 动态导入 ASR 模块（避免启动时加载失败）
            from asr.transcribe import transcribe

            print(f"[WhisperTranscriptionProvider] Starting transcription...")
            print(f"[WhisperTranscriptionProvider] Audio: {audio_path}")
            print(f"[WhisperTranscriptionProvider] Model: {self.model_size}")
            print(f"[WhisperTranscriptionProvider] Language: {self.language}")

            # 调用 ASR 转录
            result = transcribe(
                audio_path=audio_path,
                provider="whisper",  # 使用 Whisper provider
                language=self.language,
                model_size=self.model_size,
                enable_postprocess=True
            )

            print(f"[WhisperTranscriptionProvider] Transcription completed")
            print(f"[WhisperTranscriptionProvider] Utterances: {len(result.utterances)}")
            print(f"[WhisperTranscriptionProvider] Duration: {result.duration:.2f}s")

            # 构建转录文本
            transcript_lines = []
            segments = []

            for utterance in result.utterances:
                timestamp = utterance.start
                speaker = getattr(utterance, 'speaker', 'Speaker')
                text = utterance.text

                # 格式化时间戳
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                time_str = f"{minutes:02d}:{seconds:02d}"

                transcript_lines.append(f"[{time_str}] {speaker}：{text}")
                segments.append({
                    "start": time_str,
                    "speaker": speaker,
                    "text": text
                })

            full_transcript = "\n".join(transcript_lines)
            processing_time = int((datetime.now() - start_datetime).total_seconds() * 1000)

            return ProviderResult(
                success=True,
                data={
                    "transcript": full_transcript,
                    "segments": segments,
                    "duration": result.duration,
                    "word_count": len(full_transcript.split()),
                    "model": f"whisper-{self.model_size}",
                    "processed_at": datetime.now().isoformat()
                },
                provider=self.provider_type,
                is_fallback=False,
                processing_time_ms=processing_time
            )

        except ImportError as e:
            error_msg = f"ASR 模块导入失败: {str(e)}"
            print(f"[WhisperTranscriptionProvider] ERROR: {error_msg}")
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error=error_msg,
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        except FileNotFoundError as e:
            error_msg = f"音频文件不存在: {str(e)}"
            print(f"[WhisperTranscriptionProvider] ERROR: {error_msg}")
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error=error_msg,
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        except Exception as e:
            error_msg = f"转录失败: {str(e)}"
            print(f"[WhisperTranscriptionProvider] ERROR: {error_msg}")
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error=error_msg,
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )


# ============================================================
# WhisperX Transcription Provider
# ============================================================

class WhisperXTranscriptionProvider(BaseProvider):
    """WhisperX + pyannote 说话人分离转录提供商（阶段 10B-3 新增）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider_type = ProviderType.BACKEND  # WhisperX 是真实的后端服务
        self.config = config or {}

        # 从配置或环境变量读取参数
        # 注意：每次实例化时重新读取环境变量，确保使用最新值
        self.model = self.config.get("model", _get_env("WHISPERX_MODEL", "large-v3-turbo"))
        self.language = self.config.get("language", _get_env("WHISPERX_LANGUAGE", "zh"))
        self.device = self.config.get("device", _get_env("WHISPERX_DEVICE", "auto"))
        self.compute_type = self.config.get("compute_type", _get_env("WHISPERX_COMPUTE_TYPE"))
        self.batch_size = self.config.get("batch_size", _get_env("WHISPERX_BATCH_SIZE", 16))
        self.skip_align = self.config.get("skip_align", _get_env("WHISPERX_SKIP_ALIGN", False))
        self.diarization_enabled = self.config.get("diarization_enabled", _get_env("DIARIZATION_ENABLED", True))
        self.diarize_model = self.config.get("diarize_model", _get_env("PYANNOTE_DIARIZE_MODEL", "pyannote/speaker-diarization-community-1"))
        self.hf_token = self.config.get("hf_token", _get_env("HF_TOKEN") or _get_env("HUGGINGFACE_TOKEN"))

    def is_available(self) -> bool:
        """检查 WhisperX 是否可用"""
        try:
            # 检查 whisperx_service 是否可导入
            from services.whisperx_service import transcribe_with_whisperx
            return True
        except ImportError as e:
            print(f"[WhisperXTranscriptionProvider] Import error: {e}")
            return False
        except Exception as e:
            print(f"[WhisperXTranscriptionProvider] Availability check failed: {e}")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        base_info = super().get_provider_info()

        # 添加 WhisperX 特定信息
        base_info.update({
            "model": self.model,
            "language": self.language,
            "device": self.device,
            "batchSize": self.batch_size,
            "skipAlign": self.skip_align,
            "diarizationEnabled": self.diarization_enabled,
            "diarizationProvider": "pyannote" if self.diarization_enabled else None,
            "diarizationModel": self.diarize_model if self.diarization_enabled else None,
            "hfTokenConfigured": bool(self.hf_token),
            # 重要：不要返回真实 token
        })

        return base_info

    def transcribe(self, audio_path: str, **kwargs) -> ProviderResult:
        """
        使用 WhisperX 进行真实转录

        Args:
            audio_path: 音频文件路径
            **kwargs: 额外参数（覆盖实例配置）

        Returns:
            ProviderResult with transcript and transcriptTurns
        """
        start_time = time.time()
        start_datetime = datetime.now()

        try:
            # 导入 WhisperX 服务
            from services.whisperx_service import transcribe_with_whisperx

            print(f"[WhisperXTranscriptionProvider] Starting transcription...")
            print(f"[WhisperXTranscriptionProvider] Audio: {audio_path}")
            print(f"[WhisperXTranscriptionProvider] Model: {self.model}")
            print(f"[WhisperXTranscriptionProvider] Diarization: {self.diarization_enabled}")

            # 调用 WhisperX 服务（允许 kwargs 覆盖实例配置）
            result = transcribe_with_whisperx(
                audio_path=audio_path,
                model=kwargs.get("model", self.model),
                language=kwargs.get("language", self.language),
                device=kwargs.get("device", self.device),
                compute_type=kwargs.get("compute_type", self.compute_type),
                batch_size=kwargs.get("batch_size", self.batch_size),
                skip_align=kwargs.get("skip_align", self.skip_align),
                diarization_enabled=kwargs.get("diarization_enabled", self.diarization_enabled),
                hf_token=kwargs.get("hf_token", self.hf_token)
            )

            print(f"[WhisperXTranscriptionProvider] Transcription completed")
            print(f"[WhisperXTranscriptionProvider] Turns: {len(result.get('turns', []))}")

            # 构建返回数据
            # 注意：service 返回的 'turns' 在 API 层应映射为 'transcriptTurns'
            data = {
                "transcript": result.get("text", ""),
                "transcriptTurns": result.get("turns", []),
                "segments": result.get("segments", []),
                "language": result.get("language", self.language),
                "transcriptionProvider": "whisperx",
                "transcriptionModel": self.model,
                "diarizationEnabled": result.get("diarizationEnabled", False),
                "diarizationProvider": result.get("diarizationProvider"),
                "diarizationModel": result.get("diarizationModel"),
                "alignmentStatus": result.get("alignmentStatus"),
                "alignmentError": result.get("alignmentError"),
                "raw": result.get("raw", {})
            }

            processing_time = int((datetime.now() - start_datetime).total_seconds() * 1000)

            return ProviderResult(
                success=True,
                data=data,
                provider=self.provider_type,
                is_fallback=False,
                processing_time_ms=processing_time
            )

        except ValueError as e:
            # 配置错误（如缺少 HF_TOKEN）
            error_msg = str(e)
            print(f"[WhisperXTranscriptionProvider] ERROR: {error_msg}")
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error=error_msg,
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        except ImportError as e:
            error_msg = f"WhisperX 模块导入失败: {str(e)}"
            print(f"[WhisperXTranscriptionProvider] ERROR: {error_msg}")
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error=error_msg,
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        except FileNotFoundError as e:
            error_msg = f"音频文件不存在: {str(e)}"
            print(f"[WhisperXTranscriptionProvider] ERROR: {error_msg}")
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error=error_msg,
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )

        except Exception as e:
            error_msg = f"WhisperX 转录失败: {str(e)}"
            print(f"[WhisperXTranscriptionProvider] ERROR: {error_msg}")
            return ProviderResult(
                success=False,
                data=None,
                provider=self.provider_type,
                is_fallback=False,
                error=error_msg,
                processing_time_ms=int((datetime.now() - start_datetime).total_seconds() * 1000)
            )


class TranscriptionProvider:
    """转录提供商工厂（唯一版本）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._init_provider()

    def _init_provider(self):
        """初始化提供商（基于环境变量）"""
        # 从环境变量读取 provider 类型
        # 优先检查 TRANSCRIPTION_PROVIDER，其次 AI_TRANSCRIPTION_PROVIDER
        provider_type = (
            _get_env("TRANSCRIPTION_PROVIDER") or
            os.getenv("AI_TRANSCRIPTION_PROVIDER", "fallback")
        ).lower()

        print(f"[TranscriptionProvider] Initializing with provider: {provider_type}")

        # 优先级 1: WhisperX (阶段 10B-3)
        if provider_type == "whisperx":
            print(f"[TranscriptionProvider] Initializing WhisperXTranscriptionProvider...")
            whisperx_provider = WhisperXTranscriptionProvider(self.config)

            if whisperx_provider.is_available():
                self.provider = whisperx_provider
                print(f"[TranscriptionProvider] Using WhisperX + pyannote")
            else:
                # WhisperX 配置为必需时，不可用应报错
                raise RuntimeError(
                    f"TRANSCRIPTION_PROVIDER=whisperx 但 WhisperX 不可用。"
                    f"请确保已安装: pip install whisperx>=3.1.0 pyannote.audio>=3.1.0"
                )
            return

        # 优先级 2: Whisper (openai-whisper)
        elif provider_type in ("whisper", "openai-whisper", "backend"):
            print(f"[TranscriptionProvider] Initializing WhisperTranscriptionProvider...")
            whisper_provider = WhisperTranscriptionProvider(self.config)

            if whisper_provider.is_available():
                self.provider = whisper_provider
                print(f"[TranscriptionProvider] Using Whisper ASR")
            else:
                print(f"[TranscriptionProvider] Whisper unavailable, falling back")
                self.provider = FallbackTranscriptionProvider(self.config)
            return

        # 优先级 3: Fallback
        elif provider_type == "fallback":
            print(f"[TranscriptionProvider] Using fallback (forced)")
            self.provider = FallbackTranscriptionProvider(self.config)
            return

        # 未知 provider：明确报错，不静默 fallback
        else:
            raise ValueError(
                f"未知的 TRANSCRIPTION_PROVIDER: {provider_type}。"
                f"支持的值: whisperx, whisper, openai-whisper, backend, fallback"
            )

    def transcribe(self, audio_path: str, **kwargs) -> ProviderResult:
        """转录音频"""
        return self.provider.transcribe(audio_path, **kwargs)

    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        info = self.provider.get_provider_info()

        # WhisperX provider 已经返回完整信息
        if isinstance(self.provider, WhisperXTranscriptionProvider):
            return info

        # 旧 Whisper provider 的兼容处理
        if hasattr(self.provider, 'model_size'):
            info['model'] = self.provider.model_size
        if hasattr(self.provider, 'language'):
            info['language'] = self.provider.language

        return info

    def is_using_fallback(self) -> bool:
        """是否使用回退模式"""
        return isinstance(self.provider, FallbackTranscriptionProvider)
