"""
数据库模型定义 - SQLAlchemy ORM
使用 SQLite 单文件存储，方便竞赛部署与数据迁移
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Meeting(Base):
    """
    会议记录表
    存储上传的音视频文件元数据和处理状态
    """
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    video_path = Column(String(500), nullable=False)  # 存储相对路径，便于迁移
    video_size = Column(Integer)  # 文件大小（字节）
    duration = Column(Float)  # 音频时长（秒），C++ 引擎处理后更新
    status = Column(String(20), nullable=False, default="pending", index=True)
    # pending: 待处理
    # processing: C++ 引擎处理中
    # completed: 处理完成
    # failed: 处理失败

    # 新增：一句话概括（用于会议库预览）
    one_line_summary = Column(Text)  # AI 生成的一句话概括

    error_message = Column(Text)  # 失败时的错误信息
    progress = Column(Integer, default=0)  # 处理进度 0-100
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联结果表（一对多，支持多种模板总结）
    results = relationship("Result", back_populates="meeting", cascade="all, delete-orphan")

    def to_dict(self):
        """序列化为字典，用于 API 返回"""
        return {
            "id": self.id,
            "title": self.title,
            "video_path": self.video_path,
            "video_size": self.video_size,
            "duration": self.duration,
            "status": self.status,
            "error_message": self.error_message,
            "progress": self.progress,
            "one_line_summary": self.one_line_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Result(Base):
    """
    处理结果表
    存储 C++ 引擎输出的转录文本和 AI 总结
    支持多种模板（角色视角）的总结结果
    """
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)

    # 转录结果
    transcript_raw = Column(Text, nullable=False)  # 原始转录文本（C++ Whisper 输出）
    transcript_enhanced = Column(Text)  # 增强转录（LLM 修正错别字、优化语句）

    # AI 总结结果（JSON 格式存储多模板结果）
    # 结构: {"templates": [{"role": "产品经理", "content": "..."}, ...]}
    summary_json = Column(JSON, nullable=False)

    # 元数据
    llm_provider = Column(String(50))  # 使用的 LLM (deepseek/openai/claude)
    llm_model = Column(String(100))  # 具体模型
    processing_time = Column(Float)  # C++ 引擎处理耗时（秒）
    word_count = Column(Integer)  # 转录字数

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关联会议表
    meeting = relationship("Meeting", back_populates="results")

    def to_dict(self):
        """序列化为字典，用于 API 返回"""
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "transcript_raw": self.transcript_raw,
            "transcript_enhanced": self.transcript_enhanced,
            "summary_json": self.summary_json,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "processing_time": self.processing_time,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Template(Base):
    """
    总结模板表
    存储用户自定义的 AI 总结模板
    """
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # 模板名称
    description = Column(Text, nullable=False)  # 模板描述/Prompt 引导
    is_system = Column(Integer, default=0)  # 是否为系统模板 (0=用户自定义, 1=系统预设)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """序列化为字典，用于 API 返回"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Summary(Base):
    """
    总结结果表
    存储基于特定模板生成的总结内容（MD 格式）
    """
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False, index=True)

    content = Column(Text, nullable=False)  # Markdown 格式的总结内容
    llm_provider = Column(String(50))  # 使用的 LLM
    llm_model = Column(String(100))  # 具体模型
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """序列化为字典，用于 API 返回"""
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "template_id": self.template_id,
            "content": self.content,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
