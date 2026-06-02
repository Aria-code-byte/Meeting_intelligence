"""
存储抽象层
"""

from typing import Dict, List, Any, Optional
from .models import Meeting, Task


class MemoryStorage:
    """内存存储（本阶段使用）"""

    def __init__(self):
        self.meetings: Dict[str, Dict[str, Any]] = {}
        self.transcription_tasks: Dict[str, Dict[str, Any]] = {}
        self.summary_tasks: Dict[str, Dict[str, Any]] = {}
        self.enhancement_tasks: Dict[str, Dict[str, Any]] = {}

    # 会议相关
    def create_meeting(self, meeting: Meeting) -> None:
        """创建会议"""
        self.meetings[meeting.meeting_id] = meeting.to_dict()

    def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """获取会议"""
        return self.meetings.get(meeting_id)

    def update_meeting(self, meeting_id: str, updates: Dict[str, Any]) -> None:
        """更新会议"""
        if meeting_id in self.meetings:
            self.meetings[meeting_id].update(updates)

    def delete_meeting(self, meeting_id: str) -> None:
        """删除会议"""
        self.meetings.pop(meeting_id, None)

    def list_meetings(self) -> List[Dict[str, Any]]:
        """列出所有会议"""
        return list(self.meetings.values())

    # 任务相关
    def create_task(self, task: Task, task_type: str) -> None:
        """创建任务"""
        task_dict = task.to_dict()
        if task_type == "transcription":
            self.transcription_tasks[task.task_id] = task_dict
        elif task_type == "summary":
            self.summary_tasks[task.task_id] = task_dict
        elif task_type == "enhancement":
            self.enhancement_tasks[task.task_id] = task_dict

    def get_task(self, task_id: str, task_type: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        if task_type == "transcription":
            return self.transcription_tasks.get(task_id)
        elif task_type == "summary":
            return self.summary_tasks.get(task_id)
        elif task_type == "enhancement":
            return self.enhancement_tasks.get(task_id)
        return None

    def update_task(self, task_id: str, task_type: str, updates: Dict[str, Any]) -> None:
        """更新任务"""
        if task_type == "transcription" and task_id in self.transcription_tasks:
            self.transcription_tasks[task_id].update(updates)
        elif task_type == "summary" and task_id in self.summary_tasks:
            self.summary_tasks[task_id].update(updates)
        elif task_type == "enhancement" and task_id in self.enhancement_tasks:
            self.enhancement_tasks[task_id].update(updates)


# 全局存储实例
storage = MemoryStorage()
