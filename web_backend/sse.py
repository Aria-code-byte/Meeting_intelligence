#!/usr/bin/env python3
"""
SSE (Server-Sent Events) 流式响应模块
=====================================
用途：将 CLI 处理进度实时推送到 Web 前端

对应 CLI 输出格式：
    [1/3] 原始转录中...
    [2/3] 增强文稿（书面化）中...
    [3/3] 带时间索引的纯净实录生成中...
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncIterator, Optional, Dict, Any
from fastapi import HTTPException
from contextlib import asynccontextmanager

from cli_wrapper import ProcessRequest, CLIMeetingProcessor, ProgressEvent


# ============================================================
# 任务管理器
# ============================================================

class TaskManager:
    """
    异步任务管理器

    管理后台处理任务的生命周期
    """

    def __init__(self):
        self.tasks: Dict[str, CLIMeetingProcessor] = {}
        self.results: Dict[str, Any] = {}
        self.task_status: Dict[str, str] = {}  # pending, running, completed, failed

    def create_task(self, request: ProcessRequest) -> str:
        """
        创建新任务

        Args:
            request: 处理请求

        Returns:
            str: 任务 ID
        """
        task_id = uuid.uuid4().hex
        self.task_status[task_id] = "pending"
        return task_id

    async def start_task(
        self,
        task_id: str,
        request: ProcessRequest,
        progress_queue: asyncio.Queue
    ):
        """
        启动任务（在后台执行）

        Args:
            task_id: 任务 ID
            request: 处理请求
            progress_queue: 进度队列（用于 SSE 推送）
        """
        self.task_status[task_id] = "running"

        def progress_callback(event: ProgressEvent):
            """进度回调：将事件放入队列"""
            asyncio.create_task(progress_queue.put(event))

        try:
            processor = CLIMeetingProcessor(
                request=request,
                progress_callback=None  # 内部处理
            )
            self.tasks[task_id] = processor

            result = await processor.process()
            self.results[task_id] = result
            self.task_status[task_id] = "completed" if result.success else "failed"

            # 发送完成事件
            asyncio.create_task(progress_queue.put(ProgressEvent(
                stage="complete",
                step=3,
                progress=100,
                message="处理完成" if result.success else f"处理失败: {result.error_message}",
                data={
                    "success": result.success,
                    "processing_time": result.processing_time,
                    "utterance_count": result.utterance_count,
                }
            )))

        except Exception as e:
            self.task_status[task_id] = "failed"
            self.results[task_id] = {"error": str(e)}

            asyncio.create_task(progress_queue.put(ProgressEvent(
                stage="error",
                step=0,
                progress=0,
                message=f"处理失败: {str(e)}",
                data={"error": str(e)}
            )))

    def get_task_status(self, task_id: str) -> str:
        """获取任务状态"""
        return self.task_status.get(task_id, "unknown")

    def get_task_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果"""
        return self.results.get(task_id)


# 全局任务管理器
task_manager = TaskManager()


# ============================================================
# SSE 事件生成器
# ============================================================

async def sse_event_stream(task_id: str) -> AsyncIterator[str]:
    """
    SSE 事件流生成器

    格式：
        data: {"stage": "asr", "step": 1, "progress": 50, "message": "处理中..."}
        event: progress

    Args:
        task_id: 任务 ID

    Yields:
        str: SSE 格式的事件数据
    """
    progress_queue = asyncio.Queue()

    # 发送初始事件
    yield _format_sse_event({
        "stage": "init",
        "step": 0,
        "progress": 0,
        "message": "任务已创建，等待开始...",
        "task_id": task_id,
        "timestamp": datetime.now().isoformat()
    })

    # 监控任务状态
    status = task_manager.get_task_status(task_id)
    if status == "unknown":
        yield _format_sse_error("任务不存在", 404)
        return

    # 等待任务结果
    max_wait = 3600  # 最多等待 1 小时
    waited = 0
    check_interval = 0.5  # 检查间隔（秒）

    while waited < max_wait:
        status = task_manager.get_task_status(task_id)

        if status == "completed":
            result = task_manager.get_task_result(task_id)
            yield _format_sse_event({
                "stage": "complete",
                "step": 3,
                "progress": 100,
                "message": "处理完成",
                "data": {
                    "success": result.success,
                    "processing_time": result.processing_time,
                    "utterance_count": result.utterance_count,
                    "enhanced_text_preview": result.enhanced_text[:200] if result.enhanced_text else None,
                    "refined_text_preview": result.refined_text[:200] if result.refined_text else None,
                },
                "timestamp": datetime.now().isoformat()
            })
            break

        elif status == "failed":
            result = task_manager.get_task_result(task_id)
            error_msg = result.get("error", "未知错误") if result else "未知错误"
            yield _format_sse_error(error_msg, 500)
            break

        elif status == "running":
            # 任务运行中，发送心跳
            yield _format_sse_heartbeat()

        # 等待一段时间再检查
        await asyncio.sleep(check_interval)
        waited += check_interval

    else:
        yield _format_sse_error("任务超时", 408)


def _format_sse_event(data: dict) -> str:
    """
    格式化 SSE 事件

    Args:
        data: 事件数据

    Returns:
        str: SSE 格式字符串
    """
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _format_sse_error(message: str, code: int) -> str:
    """
    格式化 SSE 错误事件

    Args:
        message: 错误消息
        code: 错误代码

    Returns:
        str: SSE 格式错误字符串
    """
    return f"event: error\ndata: {json.dumps({'message': message, 'code': code}, ensure_ascii=False)}\n\n"


def _format_sse_heartbeat() -> str:
    """
    格式化 SSE 心跳事件

    Returns:
        str: SSE 格式心跳字符串
    """
    return f": heartbeat\n\n"


# ============================================================
# 带进度监控的处理器（用于实时 SSE 推送）
# ============================================================

class StreamingProcessor:
    """
    流式处理器

    在处理过程中实时推送进度到 SSE 队列
    """

    def __init__(self, request: ProcessRequest, progress_queue: asyncio.Queue):
        """
        初始化流式处理器

        Args:
            request: 处理请求
            progress_queue: 进度队列
        """
        self.request = request
        self.progress_queue = progress_queue
        self.processor = CLIMeetingProcessor(
            request=request,
            progress_callback=self._on_progress
        )

    def _on_progress(self, event: ProgressEvent):
        """
        进度回调（由 CLI 处理器调用）

        Args:
            event: 进度事件
        """
        # 将事件转换为 SSE 格式并放入队列
        asyncio.create_task(self.progress_queue.put({
            "stage": event.stage,
            "step": event.step,
            "progress": event.progress,
            "message": event.message,
            "data": event.data or {},
            "timestamp": datetime.now().isoformat()
        }))

    async def process(self) -> AsyncIterator[dict]:
        """
        执行处理并流式推送进度

        Yields:
            dict: 进度事件
        """
        # 发送开始事件
        yield {
            "stage": "start",
            "step": 0,
            "progress": 0,
            "message": "开始处理...",
            "timestamp": datetime.now().isoformat()
        }

        # 执行处理
        result = await self.processor.process()

        # 发送完成事件
        yield {
            "stage": "complete",
            "step": 3,
            "progress": 100,
            "message": "处理完成" if result.success else f"处理失败: {result.error_message}",
            "data": {
                "success": result.success,
                "processing_time": result.processing_time,
                "utterance_count": result.utterance_count,
                "enhanced_text": result.enhanced_text,
                "refined_text": result.refined_text,
            },
            "timestamp": datetime.now().isoformat()
        }
