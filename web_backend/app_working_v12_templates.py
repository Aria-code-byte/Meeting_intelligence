"""
Jinni Meeting Elf - v12 Templates System Version
基于 v11_stable，新增真实模板系统支持
保持 UI 冻结，专注业务功能
"""

import streamlit as st
import time
import requests
from datetime import datetime

# ============================================================
# 调试模式配置
# ============================================================

DEBUG_MODE = False  # 设为 True 可查看 meeting_id、task_id 等开发信息

# ============================================================
# 版本标识
# ============================================================

APP_VERSION = "v12_templates_main_2026_05_12"

# ============================================================
# API 配置层
# ============================================================

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30  # 秒
TRANSCRIPTION_POLL_INTERVAL = 2  # 轮询间隔（秒）
SUMMARY_POLL_INTERVAL = 2  # 总结生成轮询间隔（秒）

# ============================================================
# 调试模式配置
# ============================================================

DEBUG_MODE = False  # 设为 True 可查看 meeting_id、task_id 等开发信息

# ============================================================
# Mock 模板数据（v12 新增）
# ============================================================

MOCK_TEMPLATES = [
    {
        "id": "general_meeting",
        "name": "通用会议纪要",
        "description": "适合大多数会议场景，包含摘要、决策与待办事项",
        "category": "default",
        "sections": ["会议摘要", "关键讨论", "决策结论", "待办事项"],
        "prompt": "请总结本次会议，重点关注会议摘要、关键讨论内容、决策结论和待办事项。",
        "output_format": "markdown",
        "is_builtin": True
    },
    {
        "id": "weekly_meeting",
        "name": "周会总结",
        "description": "适合团队周会，包含本周成果、问题与下周计划",
        "category": "team",
        "sections": ["本周亮点", "遇到的问题", "下周计划"],
        "prompt": "请从团队协作视角总结周会，重点关注本周成果、遇到的问题和解决方案、下周重点工作。",
        "output_format": "markdown",
        "is_builtin": True
    },
    {
        "id": "project_review",
        "name": "项目评审",
        "description": "适合项目阶段评审，包含进展、风险与计划",
        "category": "project",
        "sections": ["项目进展", "关键里程碑", "风险评估", "下一步计划"],
        "prompt": "请从项目管理视角总结项目评审会议，重点关注项目进展、潜在风险和下一步行动计划。",
        "output_format": "markdown",
        "is_builtin": True
    },
    {
        "id": "customer_communication",
        "name": "客户沟通",
        "description": "适合客户会议，包含需求、方案与跟进",
        "category": "sales",
        "sections": ["客户需求", "业务场景", "方案讨论", "下一步行动"],
        "prompt": "请从客户成功视角总结客户沟通会议，重点关注客户需求、产品匹配度和后续跟进事项。",
        "output_format": "markdown",
        "is_builtin": True
    },
    {
        "id": "sales_meeting",
        "name": "销售会议",
        "description": "适合销售团队会议，包含目标、策略与行动",
        "category": "sales",
        "sections": ["销售目标", "市场分析", "销售策略", "行动计划"],
        "prompt": "请从销售管理视角总结销售会议，重点关注销售目标、市场分析和销售策略。",
        "output_format": "markdown",
        "is_builtin": True
    },
    {
        "id": "interview_record",
        "name": "面试记录",
        "description": "适合面试评估，包含背景、能力与评价",
        "category": "hr",
        "sections": ["候选人背景", "能力评估", "综合评价"],
        "prompt": "请从HR视角总结面试，重点关注候选人的专业能力、软技能和综合评价。",
        "output_format": "markdown",
        "is_builtin": True
    },
    {
        "id": "product_requirement",
        "name": "产品需求讨论",
        "description": "从产品经理视角总结需求、用户价值、风险和后续计划",
        "category": "product",
        "sections": ["核心需求", "用户价值", "讨论重点", "技术风险", "待办事项", "最终决策"],
        "prompt": "请从产品经理视角总结本次会议，重点关注需求分析、用户价值、可行性、技术风险和后续行动计划。",
        "output_format": "markdown",
        "is_builtin": True
    },
    {
        "id": "project_retrospective",
        "name": "项目复盘",
        "description": "适合项目结束复盘，包含成果、问题与改进",
        "category": "project",
        "sections": ["项目成果", "成功经验", "遇到的问题", "改进建议"],
        "prompt": "请从项目复盘视角总结会议，重点关注项目成果、经验教训和改进建议。",
        "output_format": "markdown",
        "is_builtin": True
    }
]

# ============================================================
# API Client 适配层（扩展版 - v12）
# ============================================================

class APIClient:
    """统一的 API 客户端，封装所有后端接口调用"""

    def __init__(self, base_url=API_BASE_URL, timeout=API_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

    def _check_backend_available(self):
        """检查后端是否可用"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    # ============================================================
    # 文件上传（v9 已实现）
    # ============================================================

    def upload_meeting_file(self, file, title=None):
        """
        上传会议文件到后端

        参数:
            file: Streamlit UploadedFile 对象
            title: 可选的会议标题

        返回:
            {
                "success": True/False,
                "meeting_id": "...",
                "file_name": "...",
                "file_size": 123456,
                "message": "上传成功",
                "mock": False
            }
        """
        # 文件校验
        if not file:
            return {
                "success": False,
                "message": "未选择文件"
            }

        # 文件大小校验（3GB）
        max_size = 3 * 1024 * 1024 * 1024
        if file.size > max_size:
            return {
                "success": False,
                "message": f"文件过大（{self.format_size(file.size)}），最大支持 3GB"
            }

        # 文件格式校验
        allowed_extensions = ['mp3', 'wav', 'mp4', 'm4a', 'webm']
        file_ext = file.name.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            return {
                "success": False,
                "message": f"不支持的文件格式: {file_ext}，支持格式: {', '.join(allowed_extensions)}"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # 后端不可用，返回 Mock 数据
            return {
                "success": True,
                "meeting_id": f"mock_meeting_{int(time.time())}",
                "file_name": file.name,
                "file_size": file.size,
                "message": "⚠️ 当前使用模拟上传结果，后端 API 未连接",
                "mock": True
            }

        # 调用真实后端 API
        try:
            files = {
                "file": (file.name, file.getvalue(), file.type)
            }

            data = {}
            if title:
                data["title"] = title
            else:
                data["title"] = file.name

            response = requests.post(
                f"{self.base_url}/api/upload",
                files=files,
                data=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "meeting_id": result.get("meeting_id", ""),
                    "file_name": result.get("file_name", file.name),
                    "file_size": result.get("file_size", file.size),
                    "message": result.get("message", "上传成功"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"上传失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "上传超时，请检查网络连接"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务，请确认服务已启动"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"上传失败: {str(e)}"
            }

    # ============================================================
    # 转录 API（v10 已实现，v11 修复 Mock 自动完成）
    # ============================================================

    def start_transcription(self, meeting_id):
        """
        启动会议转录任务

        参数:
            meeting_id: 会议 ID

        返回:
            {
                "success": True/False,
                "task_id": "...",
                "status": "processing",
                "message": "转录任务已启动",
                "mock": False
            }
        """
        if not meeting_id:
            return {
                "success": False,
                "message": "会议 ID 不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式
            return {
                "success": True,
                "task_id": f"mock_transcribe_{int(time.time())}",
                "status": "processing",
                "message": "⚠️ Mock 模式：转录任务已启动（模拟）",
                "mock": True
            }

        # 调用真实后端 API
        try:
            response = requests.post(
                f"{self.base_url}/api/meetings/{meeting_id}/transcribe",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "task_id": result.get("task_id", ""),
                    "status": result.get("status", "processing"),
                    "message": result.get("message", "转录任务已启动"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"启动转录失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "启动转录超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"启动转录失败: {str(e)}"
            }

    def get_transcription_status(self, meeting_id, start_time=None):
        """
        查询转录状态

        参数:
            meeting_id: 会议 ID
            start_time: 转录开始时间（用于 Mock 模式计算进度）

        返回:
            {
                "success": True/False,
                "status": "processing/completed/failed",
                "progress": 45,
                "current_step": "正在识别音频内容",
                "message": "...",
                "mock": False
            }
        """
        if not meeting_id:
            return {
                "success": False,
                "message": "会议 ID 不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：基于真实时间计算进度（v11 修复）
            if start_time is None:
                # 如果没有传入开始时间，使用当前时间
                start_time = int(time.time())

            elapsed = int(time.time()) - start_time
            progress = min(100, elapsed * 5)  # 每秒增加 5%，最多到 100%

            # 根据进度返回不同的状态文案
            if progress < 20:
                step = "正在分析音频文件"
            elif progress < 50:
                step = "正在识别语音内容"
            elif progress < 80:
                step = "正在分离发言人"
            elif progress < 100:
                step = "正在整理文字稿"
            else:
                step = "转录完成"

            # v11 修复：进度到 100% 时，status 变为 completed
            status = "completed" if progress >= 100 else "processing"

            return {
                "success": True,
                "status": status,
                "progress": progress,
                "current_step": step,
                "message": f"⚠️ Mock 模式：转录进度 {progress}%",
                "mock": True
            }

        # 调用真实后端 API
        try:
            response = requests.get(
                f"{self.base_url}/api/meetings/{meeting_id}/transcription-status",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "status": result.get("status", "processing"),
                    "progress": result.get("progress", 0),
                    "current_step": result.get("current_step", "处理中"),
                    "message": result.get("message", ""),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"查询状态失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "查询状态超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"查询状态失败: {str(e)}"
            }

    def get_transcript(self, meeting_id):
        """
        获取完整文字稿

        参数:
            meeting_id: 会议 ID

        返回:
            {
                "success": True/False,
                "transcript": "完整会议文字稿...",
                "segments": [...],
                "message": "...",
                "mock": False
            }
        """
        if not meeting_id:
            return {
                "success": False,
                "message": "会议 ID 不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：生成模拟文字稿
            mock_transcript = """[00:00:01] Speaker 1：大家好，我们开始今天的会议。
[00:00:08] Speaker 2：今天主要讨论产品需求、开发计划和后续风险。
[00:00:20] Speaker 1：我们需要在下周前完成第一版原型。
[00:00:35] Speaker 2：我同意，那我们分配一下任务。
[00:00:45] Speaker 1：你负责前端开发，我负责后端 API。
[00:01:00] Speaker 2：好的，那我们明天再同步进度。
[00:01:10] Speaker 1：没问题，会议结束。"""

            mock_segments = [
                {"start": "00:00:01", "speaker": "Speaker 1", "text": "大家好，我们开始今天的会议。"},
                {"start": "00:00:08", "speaker": "Speaker 2", "text": "今天主要讨论产品需求、开发计划和后续风险。"},
                {"start": "00:00:20", "speaker": "Speaker 1", "text": "我们需要在下周前完成第一版原型。"},
                {"start": "00:00:35", "speaker": "Speaker 2", "text": "我同意，那我们分配一下任务。"},
                {"start": "00:00:45", "speaker": "Speaker 1", "text": "你负责前端开发，我负责后端 API。"},
                {"start": "00:01:00", "speaker": "Speaker 2", "text": "好的，那我们明天再同步进度。"},
                {"start": "00:01:10", "speaker": "Speaker 1", "text": "没问题，会议结束。"}
            ]

            return {
                "success": True,
                "transcript": mock_transcript,
                "segments": mock_segments,
                "message": "⚠️ Mock 模式：模拟文字稿",
                "mock": True
            }

        # 调用真实后端 API
        try:
            response = requests.get(
                f"{self.base_url}/api/meetings/{meeting_id}/transcript",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "transcript": result.get("transcript", ""),
                    "segments": result.get("segments", []),
                    "message": result.get("message", "获取成功"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"获取文字稿失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "获取文字稿超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取文字稿失败: {str(e)}"
            }

    # ============================================================
    # 模板管理 API（v12 新增）
    # ============================================================

    def get_templates(self):
        """
        获取模板列表

        返回:
            {
                "success": True/False,
                "templates": [...],
                "message": "...",
                "mock": False
            }
        """
        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：返回本地模板列表
            return {
                "success": True,
                "templates": MOCK_TEMPLATES,
                "message": "⚠️ Mock 模式：使用本地模板列表",
                "mock": True
            }

        # 调用真实后端 API
        try:
            response = requests.get(
                f"{self.base_url}/api/templates",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "templates": result.get("templates", []),
                    "message": result.get("message", "获取成功"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"获取模板列表失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "获取模板列表超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取模板列表失败: {str(e)}"
            }

    def get_template_detail(self, template_id):
        """
        获取单个模板详情

        参数:
            template_id: 模板 ID

        返回:
            {
                "success": True/False,
                "template": {...},
                "message": "...",
                "mock": False
            }
        """
        if not template_id:
            return {
                "success": False,
                "message": "模板 ID 不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：从本地模板列表中查找
            template = next((t for t in MOCK_TEMPLATES if t["id"] == template_id), None)
            if template:
                return {
                    "success": True,
                    "template": template,
                    "message": "⚠️ Mock 模式：使用本地模板",
                    "mock": True
                }
            else:
                return {
                    "success": False,
                    "message": f"模板不存在: {template_id}"
                }

        # 调用真实后端 API
        try:
            response = requests.get(
                f"{self.base_url}/api/templates/{template_id}",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "template": result.get("template", {}),
                    "message": result.get("message", "获取成功"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"获取模板详情失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "获取模板详情超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取模板详情失败: {str(e)}"
            }

    def create_template(self, template_data):
        """
        新建模板

        参数:
            template_data: {
                "name": "...",
                "description": "...",
                "sections": [...],
                "prompt": "...",
                "output_format": "markdown"
            }

        返回:
            {
                "success": True/False,
                "template_id": "...",
                "template": {...},
                "message": "...",
                "mock": False
            }
        """
        if not template_data:
            return {
                "success": False,
                "message": "模板数据不能为空"
            }

        # 验证必填字段
        required_fields = ["name", "description", "sections", "prompt"]
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                return {
                    "success": False,
                    "message": f"缺少必填字段: {field}"
                }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：生成本地模板
            new_template = {
                "id": f"custom_{int(time.time())}",
                "name": template_data["name"],
                "description": template_data["description"],
                "category": "custom",
                "sections": template_data["sections"],
                "prompt": template_data["prompt"],
                "output_format": template_data.get("output_format", "markdown"),
                "is_builtin": False
            }
            # 添加到本地 Mock 模板列表
            MOCK_TEMPLATES.append(new_template)

            return {
                "success": True,
                "template_id": new_template["id"],
                "template": new_template,
                "message": "⚠️ Mock 模式：模板已创建（本地）",
                "mock": True
            }

        # 调用真实后端 API
        try:
            response = requests.post(
                f"{self.base_url}/api/templates",
                json=template_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "template_id": result.get("template_id", ""),
                    "template": result.get("template", {}),
                    "message": result.get("message", "创建成功"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"创建模板失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "创建模板超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"创建模板失败: {str(e)}"
            }

    def update_template(self, template_id, template_data):
        """
        更新模板

        参数:
            template_id: 模板 ID
            template_data: 更新的数据

        返回:
            {
                "success": True/False,
                "template": {...},
                "message": "...",
                "mock": False
            }
        """
        if not template_id:
            return {
                "success": False,
                "message": "模板 ID 不能为空"
            }

        if not template_data:
            return {
                "success": False,
                "message": "模板数据不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：更新本地模板
            template = next((t for t in MOCK_TEMPLATES if t["id"] == template_id), None)
            if template:
                # 不允许修改内置模板
                if template.get("is_builtin", False):
                    return {
                        "success": False,
                        "message": "不允许修改内置模板，请先复制为自定义模板"
                    }

                # 更新字段
                for key, value in template_data.items():
                    if value:  # 只更新非空字段
                        template[key] = value

                return {
                    "success": True,
                    "template": template,
                    "message": "⚠️ Mock 模式：模板已更新（本地）",
                    "mock": True
                }
            else:
                return {
                    "success": False,
                    "message": f"模板不存在: {template_id}"
                }

        # 调用真实后端 API
        try:
            response = requests.put(
                f"{self.base_url}/api/templates/{template_id}",
                json=template_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "template": result.get("template", {}),
                    "message": result.get("message", "更新成功"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"更新模板失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "更新模板超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"更新模板失败: {str(e)}"
            }

    def delete_template(self, template_id):
        """
        删除模板

        参数:
            template_id: 模板 ID

        返回:
            {
                "success": True/False,
                "message": "...",
                "mock": False
            }
        """
        if not template_id:
            return {
                "success": False,
                "message": "模板 ID 不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：删除本地模板
            template = next((t for t in MOCK_TEMPLATES if t["id"] == template_id), None)
            if template:
                # 不允许删除内置模板
                if template.get("is_builtin", False):
                    return {
                        "success": False,
                        "message": "不允许删除内置模板"
                    }

                # 从列表中删除
                MOCK_TEMPLATES.remove(template)

                return {
                    "success": True,
                    "message": "⚠️ Mock 模式：模板已删除（本地）",
                    "mock": True
                }
            else:
                return {
                    "success": False,
                    "message": f"模板不存在: {template_id}"
                }

        # 调用真实后端 API
        try:
            response = requests.delete(
                f"{self.base_url}/api/templates/{template_id}",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": result.get("message", "删除成功"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"删除模板失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "删除模板超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"删除模板失败: {str(e)}"
            }

    # ============================================================
    # 总结生成 API（v11 已实现）
    # ============================================================

    def generate_summary(self, meeting_id, template_id, template_detail=None, transcript=None):
        """
        启动 AI 总结生成任务

        参数:
            meeting_id: 会议 ID
            template_id: 模板 ID
            template_detail: 模板详情（可选，v12 新增）
            transcript: 可选的完整文字稿

        返回:
            {
                "success": True/False,
                "task_id": "...",
                "status": "processing",
                "message": "总结生成任务已启动",
                "mock": False
            }
        """
        if not meeting_id:
            return {
                "success": False,
                "message": "会议 ID 不能为空"
            }

        if not template_id:
            return {
                "success": False,
                "message": "模板 ID 不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式
            return {
                "success": True,
                "task_id": f"mock_summary_{int(time.time())}",
                "status": "processing",
                "message": "⚠️ Mock 模式：总结生成任务已启动（模拟）",
                "mock": True
            }

        # 调用真实后端 API
        try:
            data = {
                "template_id": template_id,
                "output_format": "markdown"
            }

            # v12 新增：传递模板详情
            if template_detail:
                data["template"] = template_detail

            if transcript:
                data["transcript"] = transcript

            response = requests.post(
                f"{self.base_url}/api/meetings/{meeting_id}/summarize",
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "task_id": result.get("task_id", ""),
                    "status": result.get("status", "processing"),
                    "message": result.get("message", "总结生成任务已启动"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"启动总结生成失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "启动总结生成超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"启动总结生成失败: {str(e)}"
            }

    def get_summary_status(self, meeting_id, start_time=None):
        """
        查询 AI 总结生成状态

        参数:
            meeting_id: 会议 ID
            start_time: 总结生成开始时间（用于 Mock 模式计算进度）

        返回:
            {
                "success": True/False,
                "status": "pending/processing/completed/failed",
                "progress": 60,
                "current_step": "正在提取关键讨论内容",
                "message": "...",
                "mock": False
            }
        """
        if not meeting_id:
            return {
                "success": False,
                "message": "会议 ID 不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：基于真实时间计算进度
            if start_time is None:
                start_time = int(time.time())

            elapsed = int(time.time()) - start_time
            progress = min(100, elapsed * 5)  # 每秒增加 5%，最多到 100%

            # 根据进度返回不同的状态文案
            if progress < 20:
                step = "正在分析会议主题"
            elif progress < 40:
                step = "正在提取关键讨论"
            elif progress < 60:
                step = "正在识别决策结论"
            elif progress < 80:
                step = "正在整理待办事项"
            elif progress < 100:
                step = "正在生成 Markdown 文件"
            else:
                step = "总结生成完成"

            # 进度到 100% 时，status 变为 completed
            status = "completed" if progress >= 100 else "processing"

            return {
                "success": True,
                "status": status,
                "progress": progress,
                "current_step": step,
                "message": f"⚠️ Mock 模式：总结生成进度 {progress}%",
                "mock": True
            }

        # 调用真实后端 API
        try:
            response = requests.get(
                f"{self.base_url}/api/meetings/{meeting_id}/summary-status",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "status": result.get("status", "processing"),
                    "progress": result.get("progress", 0),
                    "current_step": result.get("current_step", "处理中"),
                    "message": result.get("message", ""),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"查询总结状态失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "查询总结状态超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"查询总结状态失败: {str(e)}"
            }

    def get_summary(self, meeting_id):
        """
        获取生成的 AI 总结

        参数:
            meeting_id: 会议 ID

        返回:
            {
                "success": True/False,
                "summary": "# 会议总结\n\n...",
                "markdown": "# 会议总结\n\n...",
                "template_id": "...",
                "template_name": "...",
                "message": "...",
                "mock": False
            }
        """
        if not meeting_id:
            return {
                "success": False,
                "message": "会议 ID 不能为空"
            }

        # 检查后端是否可用
        backend_available = self._check_backend_available()

        if not backend_available:
            # Mock 模式：生成模拟总结
            mock_summary = """# 会议总结

## 一、会议摘要

本次会议主要围绕产品需求、开发计划与后续风险展开讨论。团队确认了第一版原型的交付目标，并明确了前后端分工。

## 二、关键讨论内容

- 产品第一版原型需要在下周前完成
- 前端与后端需要并行推进
- 后续需要持续同步开发进度

## 三、决策结论

- 确认下周前完成第一版原型
- 前端开发由 Speaker 2 负责
- 后端 API 由 Speaker 1 负责

## 四、待办事项

- Speaker 2：完成前端页面开发
- Speaker 1：完成后端 API 开发
- 全体：明天同步开发进度

## 五、风险与问题

- 开发时间较紧，需要控制需求范围
- 前后端接口需要尽早对齐

## 六、会议结论

团队已明确下一步开发目标与责任分工，后续将通过每日同步推进项目进展。
"""

            return {
                "success": True,
                "summary": mock_summary,
                "markdown": mock_summary,
                "template_id": "general_meeting",
                "template_name": "通用会议纪要",
                "message": "⚠️ Mock 模式：模拟 AI 总结",
                "mock": True
            }

        # 调用真实后端 API
        try:
            response = requests.get(
                f"{self.base_url}/api/meetings/{meeting_id}/summary",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "summary": result.get("summary", ""),
                    "markdown": result.get("markdown", result.get("summary", "")),
                    "template_id": result.get("template_id", ""),
                    "template_name": result.get("template_name", ""),
                    "message": result.get("message", "获取成功"),
                    "mock": False
                }
            else:
                return {
                    "success": False,
                    "message": f"获取总结失败，状态码: {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "获取总结超时"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "无法连接到后端服务"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取总结失败: {str(e)}"
            }

    @staticmethod
    def format_size(size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="Jinni | AI Meeting Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 最小化 CSS
# ============================================================

st.markdown("""
<style>
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    stAppHeader { display: none; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 状态管理（扩展版 - v12）
# ============================================================

def init_state():
    """初始化 session state"""
    # 原有状态（v9-v11）
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'file_meta' not in st.session_state:
        st.session_state.file_meta = None
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()
    if 'meeting_id' not in st.session_state:
        st.session_state.meeting_id = None
    if 'upload_status' not in st.session_state:
        st.session_state.upload_status = None
    if 'upload_message' not in st.session_state:
        st.session_state.upload_message = None

    # 转录状态（v10-v11）
    if 'transcription_task_id' not in st.session_state:
        st.session_state.transcription_task_id = None
    if 'transcription_status' not in st.session_state:
        st.session_state.transcription_status = None
    if 'transcription_progress' not in st.session_state:
        st.session_state.transcription_progress = 0
    if 'transcription_message' not in st.session_state:
        st.session_state.transcription_message = None
    if 'transcript' not in st.session_state:
        st.session_state.transcript = None
    if 'transcript_segments' not in st.session_state:
        st.session_state.transcript_segments = None
    if 'transcription_error' not in st.session_state:
        st.session_state.transcription_error = None
    if 'transcription_started' not in st.session_state:
        st.session_state.transcription_started = False
    if 'transcription_start_time' not in st.session_state:
        st.session_state.transcription_start_time = None

    # 总结生成状态（v11）
    if 'summary_task_id' not in st.session_state:
        st.session_state.summary_task_id = None
    if 'summary_status' not in st.session_state:
        st.session_state.summary_status = None
    if 'summary_progress' not in st.session_state:
        st.session_state.summary_progress = 0
    if 'summary_message' not in st.session_state:
        st.session_state.summary_message = None
    if 'summary_error' not in st.session_state:
        st.session_state.summary_error = None
    if 'summary_started' not in st.session_state:
        st.session_state.summary_started = False
    if 'summary_start_time' not in st.session_state:
        st.session_state.summary_start_time = None
    if 'ai_summary' not in st.session_state:
        st.session_state.ai_summary = None
    if 'markdown_result' not in st.session_state:
        st.session_state.markdown_result = None

    # 模板管理状态（v12 新增）
    if 'templates' not in st.session_state:
        st.session_state.templates = None
    if 'templates_loaded' not in st.session_state:
        st.session_state.templates_loaded = False
    if 'templates_error' not in st.session_state:
        st.session_state.templates_error = None
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = None
    if 'selected_template_id' not in st.session_state:
        st.session_state.selected_template_id = None
    if 'selected_template_detail' not in st.session_state:
        st.session_state.selected_template_detail = None
    if 'template_mock_mode' not in st.session_state:
        st.session_state.template_mock_mode = False

init_state()

# ============================================================
# 辅助函数
# ============================================================

def format_size(size_bytes):
    """格式化文件大小"""
    return APIClient.format_size(size_bytes)

# ============================================================
# 步骤 1: 上传文件（保持不变）
# ============================================================

def render_step_upload():
    # ===== 版本标识（Step 1 顶部） =====
    st.markdown(f"**🔷 版本: v12_templates_main_2026_05_12 | 当前步骤: Step 1**")
    st.markdown("")

    st.header("📁 上传会议文件")
    st.markdown("**步骤 1/5**")
    st.markdown("---")

    st.markdown("### 支持的格式")
    st.markdown("- MP3, WAV, MP4, M4A, WEBM")
    st.markdown("- 最大文件大小: 3GB")
    st.markdown("")

    # 文件上传
    uploaded_file = st.file_uploader(
        "选择会议文件",
        type=["mp3", "wav", "mp4", "m4a", "webm"],
        label_visibility="visible"
    )

    if uploaded_file:
        st.success(f"✅ 已选择文件: **{uploaded_file.name}** ({format_size(uploaded_file.size)})")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✨ 开始处理", type="primary", use_container_width=True):
                # 如果用户重新上传文件，清空所有状态
                if st.session_state.meeting_id and st.session_state.uploaded_file != uploaded_file:
                    # 清空所有状态（包括模板和总结）
                    for key in ['transcription_task_id', 'transcription_status',
                               'transcription_progress', 'transcription_message',
                               'transcript', 'transcript_segments', 'transcription_error',
                               'transcription_started', 'transcription_start_time',
                               'summary_task_id', 'summary_status', 'summary_progress',
                               'summary_message', 'summary_error', 'summary_started',
                               'summary_start_time', 'ai_summary', 'markdown_result',
                               'templates', 'templates_loaded', 'templates_error',
                               'selected_template', 'selected_template_id',
                               'selected_template_detail', 'template_mock_mode']:
                        if key in st.session_state:
                            del st.session_state[key]

                # 调用 API 上传
                with st.spinner("📤 正在上传文件..."):
                    result = st.session_state.api_client.upload_meeting_file(uploaded_file)

                # 保存上传结果
                st.session_state.upload_status = result["success"]
                st.session_state.upload_message = result["message"]

                if result["success"]:
                    st.session_state.uploaded_file = uploaded_file
                    st.session_state.meeting_id = result["meeting_id"]
                    st.session_state.file_meta = {
                        "name": result["file_name"],
                        "size": result["file_size"]
                    }

                    if result.get("mock"):
                        st.warning(result["message"])
                    else:
                        st.success(result["message"])

                    time.sleep(0.5)
                    st.session_state.current_step = 2
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")

        with col2:
            if st.button("重新选择", use_container_width=True):
                st.session_state.uploaded_file = None
                st.session_state.meeting_id = None
                st.session_state.upload_status = None
                st.session_state.upload_message = None
                st.rerun()

# ============================================================
# 步骤 2: 提取内容（保持不变）
# ============================================================

def render_step_extract():
    if DEBUG_MODE:
        st.caption("当前运行文件版本：MAIN_ENTRY_UI_FIX_001")
        st.caption("DEBUG: 正式 Step 2 渲染函数已进入")

    st.header("⚙️ 提取会议内容")
    st.markdown("**步骤 2/5**")
    st.markdown("---")

    # ========================================================
    # 转录逻辑
    # ========================================================

    meeting_id = st.session_state.meeting_id
    api_client = st.session_state.api_client

    # 如果已经有完整的 transcript，直接显示完成状态
    if st.session_state.transcript:
        with st.container():
            if st.session_state.uploaded_file:
                st.markdown(f"**文件**：{st.session_state.uploaded_file.name}")

            if DEBUG_MODE:
                if st.session_state.meeting_id:
                    st.caption(f"🆔 会议 ID: {st.session_state.meeting_id}")

            st.markdown("")
            st.markdown("✅ **会议内容已提取完成**")
            st.markdown("")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("➡️ 继续选择模板", type="primary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
            with col2:
                if st.button("⬅️ 返回上传", use_container_width=True):
                    st.session_state.current_step = 1
                    st.rerun()
        return

    # ========================================================
    # 自动转录流程
    # ========================================================

    with st.container():
        if st.session_state.uploaded_file:
            st.markdown(f"**文件**：{st.session_state.uploaded_file.name}")

        if DEBUG_MODE:
            if st.session_state.meeting_id:
                st.caption(f"🆔 会议 ID: {st.session_state.meeting_id}")

        st.markdown("")

        # 如果尚未启动转录任务
        if not st.session_state.transcription_started:
            st.markdown("**当前状态**：准备就绪")
            st.markdown("")

            if st.button("🎙️ 开始转录", type="primary", use_container_width=True):
                result = api_client.start_transcription(meeting_id)

                if result["success"]:
                    st.session_state.transcription_started = True
                    st.session_state.transcription_status = result.get("status", "processing")
                    st.session_state.transcription_start_time = int(time.time())

                    if DEBUG_MODE and result.get("message"):
                        st.caption(result["message"])

                    st.rerun()
                else:
                    st.markdown(f"**错误**：{result['message']}")
                    if st.button("⬅️ 返回上传", use_container_width=True):
                        st.session_state.current_step = 1
                        st.rerun()

        # 转录任务已启动，轮询状态
        elif st.session_state.transcription_status not in ["completed", "failed"]:
            result = api_client.get_transcription_status(
                meeting_id,
                start_time=st.session_state.transcription_start_time
            )

            if result["success"]:
                st.session_state.transcription_status = result.get("status", "processing")
                st.session_state.transcription_progress = result.get("progress", 0)
                st.session_state.transcription_message = result.get("current_step", "处理中")

                # 显示进度
                progress = st.session_state.transcription_progress / 100
                st.progress(progress)
                st.markdown(f"**当前步骤**：{st.session_state.transcription_message} ({st.session_state.transcription_progress}%)")

                if DEBUG_MODE:
                    if result.get("mock"):
                        st.caption("⚠️ Mock 模式")

                # 自动刷新
                if result["status"] == "completed":
                    transcript_result = api_client.get_transcript(meeting_id)
                    if transcript_result["success"]:
                        st.session_state.transcript = transcript_result.get("transcript", "")
                        st.session_state.transcript_segments = transcript_result.get("segments", [])

                        if DEBUG_MODE:
                            if transcript_result.get("message"):
                                st.caption(transcript_result["message"])

                        time.sleep(1)
                        st.session_state.current_step = 3
                        st.rerun()
                elif result["status"] == "failed":
                    st.markdown("**错误**：转录失败")
                    if st.button("🔄 重试", use_container_width=True):
                        st.session_state.transcription_started = False
                        st.session_state.transcription_status = None
                        st.rerun()
                else:
                    time.sleep(TRANSCRIPTION_POLL_INTERVAL)
                    st.rerun()

        # 转录失败
        elif st.session_state.transcription_status == "failed":
            st.markdown("**错误**：转录失败")
            if st.button("🔄 重试", use_container_width=True):
                st.session_state.transcription_started = False
                st.session_state.transcription_status = None
                st.rerun()

    # 底部返回按钮
    if st.button("⬅️ 返回上传", use_container_width=True):
        st.session_state.current_step = 1
        st.rerun()

# ============================================================
# 步骤 3: 选择模板（v12 重大更新：真实模板系统）
# ============================================================

def render_step_template():
    if DEBUG_MODE:
        st.caption("当前运行文件版本：MAIN_ENTRY_UI_FIX_001")
        st.caption("DEBUG: 正式 Step 3 渲染函数已进入")

    st.header("📋 选择总结模板")
    st.markdown("**步骤 3/5**")
    st.markdown("---")

    st.markdown("### 选择一个模板来定制化你的会议总结")
    if not DEBUG_MODE:
        st.caption("💡 提示：下拉到下方可以找到「🔧 模板管理」面板，支持新建、编辑、删除自定义模板")

    api_client = st.session_state.api_client

    # ========================================================
    # 加载模板列表
    # ========================================================

    if not st.session_state.templates_loaded:
        with st.spinner("📋 正在加载模板列表..."):
            result = api_client.get_templates()

        if result["success"]:
            st.session_state.templates = result.get("templates", [])
            st.session_state.templates_loaded = True
            st.session_state.template_mock_mode = result.get("mock", False)

            if DEBUG_MODE and result.get("mock"):
                st.caption("⚠️ Mock 模式：使用本地模板列表")
        else:
            st.error(f"❌ {result['message']}")
            st.session_state.templates_error = result["message"]

            # 显示重试按钮
            if st.button("🔄 重新加载模板", use_container_width=True):
                st.session_state.templates_loaded = False
                st.rerun()

            if st.button("⬅️ 返回上一步", use_container_width=True):
                st.session_state.current_step = 2
                st.rerun()

            return

    # ========================================================
    # 显示模板列表
    # ========================================================

    templates = st.session_state.templates

    if not templates:
        st.error("❌ 暂无可用模板")
        return

    # 按类别分组显示
    template_categories = {}
    for template in templates:
        category = template.get("category", "default")
        if category not in template_categories:
            template_categories[category] = []
        template_categories[category].append(template)

    # 选择模板
    template_options = {}
    for category, category_templates in template_categories.items():
        category_name = {
            "default": "默认模板",
            "team": "团队协作",
            "project": "项目管理",
            "product": "产品管理",
            "sales": "销售与客户",
            "hr": "人力资源",
            "custom": "自定义模板"
        }.get(category, category)

        for template in category_templates:
            display_name = f"{template['name']}"
            if not template.get("is_builtin", False):
                display_name += " (自定义)"
            template_options[display_name] = template

    selected_display = st.radio(
        "选择模板",
        list(template_options.keys()),
        label_visibility="collapsed"
    )

    selected_template_obj = template_options[selected_display]

    # 显示模板详情
    with st.expander(f"👀 查看模板详情: {selected_template_obj['name']}", expanded=False):
        st.markdown(f"**描述**: {selected_template_obj['description']}")

        st.markdown("**输出结构**:")
        for section in selected_template_obj.get("sections", []):
            st.markdown(f"- {section}")

        if selected_template_obj.get("prompt"):
            st.markdown(f"**提示词**: {selected_template_obj['prompt']}")

        # 显示是否为内置模板
        if selected_template_obj.get("is_builtin", False):
            st.caption("✅ 内置模板")
        else:
            st.caption("🔧 自定义模板")

    st.markdown("---")  # 添加分隔线
    st.markdown("")  # 添加间距

    # ============================================================
    # 模板管理（折叠面板）
    # ============================================================

    with st.expander("🔧 模板管理", expanded=False):
        st.markdown("新建、编辑、删除自定义模板")

        # 使用 tabs 来组织模板管理功能
        tab1, tab2 = st.tabs(["✨ 新建模板", "🔧 编辑模板"])

    with tab1:
        st.markdown("#### 新建自定义模板")

        with st.form("create_template_form"):
            new_template_name = st.text_input("模板名称", placeholder="例如：技术评审会议")
            new_template_desc = st.text_input("模板描述", placeholder="例如：适合技术团队评审会议场景")
            new_template_sections = st.text_area(
                "输出结构（每行一个）",
                placeholder="技术背景\n评审内容\n风险评估\n行动项",
                help="每行一个输出结构项"
            )
            new_template_prompt = st.text_area(
                "模板提示词",
                placeholder="请从技术视角总结会议，重点关注技术方案、风险和后续行动。",
                help="AI 将使用此提示词生成总结"
            )

            col1, col2 = st.columns(2)
            with col1:
                create_submit = st.form_submit_button("✨ 创建模板", type="primary", use_container_width=True)
            with col2:
                st.write("")  # 占位

            if create_submit:
                if not new_template_name or not new_template_desc:
                    st.error("❌ 模板名称和描述不能为空")
                elif not new_template_sections:
                    st.error("❌ 输出结构不能为空")
                elif not new_template_prompt:
                    st.error("❌ 模板提示词不能为空")
                else:
                    # 解析 sections
                    sections_list = [s.strip() for s in new_template_sections.split('\n') if s.strip()]

                    # 构建模板数据
                    template_data = {
                        "name": new_template_name,
                        "description": new_template_desc,
                        "sections": sections_list,
                        "prompt": new_template_prompt,
                        "output_format": "markdown"
                    }

                    # 调用 API 创建
                    with st.spinner("🔧 正在创建模板..."):
                        create_result = api_client.create_template(template_data)

                    if create_result["success"]:
                        st.success(f"✅ 模板已创建: {new_template_name}")

                        if DEBUG_MODE and create_result.get("mock"):
                            st.caption("⚠️ Mock 模式：模板已保存到本地")

                        # 刷新模板列表
                        st.session_state.templates_loaded = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {create_result['message']}")

    with tab2:
        st.markdown(f"#### 编辑当前选中的模板: {selected_template_obj['name']}")

        # 显示是否为内置模板
        if selected_template_obj.get("is_builtin", False):
            st.info("💡 内置模板不允许编辑或删除")
            st.caption("如需修改，建议复制后创建为自定义模板")
        else:
            st.markdown("**当前模板信息**:")
            st.write(f"- **ID**: {selected_template_obj['id']}")
            st.write(f"- **描述**: {selected_template_obj['description']}")
            st.write(f"- **输出结构**: {', '.join(selected_template_obj.get('sections', []))}")

            st.markdown("---")

            with st.form("edit_template_form"):
                st.markdown("##### 修改模板")

                edit_template_desc = st.text_input("模板描述", value=selected_template_obj.get("description", ""))
                edit_template_sections = st.text_area(
                    "输出结构（每行一个）",
                    value='\n'.join(selected_template_obj.get("sections", [])),
                    help="每行一个输出结构项"
                )
                edit_template_prompt = st.text_area(
                    "模板提示词",
                    value=selected_template_obj.get("prompt", ""),
                    help="AI 将使用此提示词生成总结"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    edit_submit = st.form_submit_button("💾 保存修改", use_container_width=True)
                with col2:
                    delete_submit = st.form_submit_button("🗑️ 删除模板", use_container_width=True)
                with col3:
                    st.write("")

                if edit_submit:
                    sections_list = [s.strip() for s in edit_template_sections.split('\n') if s.strip()]

                    template_data = {
                        "description": edit_template_desc,
                        "sections": sections_list,
                        "prompt": edit_template_prompt
                    }

                    with st.spinner("💾 正在保存模板..."):
                        edit_result = api_client.update_template(
                            selected_template_obj["id"],
                            template_data
                        )

                    if edit_result["success"]:
                        st.success("✅ 模板已更新")

                        if edit_result.get("mock"):
                            st.caption("⚠️ Mock 模式：模板已更新到本地")

                        # 刷新模板列表
                        st.session_state.templates_loaded = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {edit_result['message']}")

                if delete_submit:
                    # 确认删除
                    if st.session_state.get(f"confirm_delete_{selected_template_obj['id']}", False):
                        with st.spinner("🗑️ 正在删除模板..."):
                            delete_result = api_client.delete_template(selected_template_obj["id"])

                        if delete_result["success"]:
                            st.success("✅ 模板已删除")

                            if delete_result.get("mock"):
                                st.caption("⚠️ Mock 模式：模板已从本地删除")

                            # 清空选择
                            if st.session_state.selected_template_id == selected_template_obj["id"]:
                                st.session_state.selected_template_id = None
                                st.session_state.selected_template_detail = None

                            # 刷新模板列表
                            st.session_state.templates_loaded = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {delete_result['message']}")
                    else:
                        st.session_state[f"confirm_delete_{selected_template_obj['id']}"] = True
                        st.warning("⚠️ 请再次点击删除按钮确认删除")
                        st.rerun()

    # ========================================================
    # 底部按钮
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✨ 生成总结", type="primary", use_container_width=True):
            # v12 修改：保存完整的模板信息
            st.session_state.selected_template = selected_template_obj['name']
            st.session_state.selected_template_id = selected_template_obj['id']
            st.session_state.selected_template_detail = selected_template_obj

            # 如果用户重新选择模板，清空旧总结状态
            if st.session_state.ai_summary:
                for key in ['summary_task_id', 'summary_status', 'summary_progress',
                           'summary_message', 'summary_error', 'summary_started',
                           'summary_start_time', 'ai_summary', 'markdown_result']:
                    if key in st.session_state:
                        del st.session_state[key]

            st.session_state.current_step = 4
            st.rerun()

    with col2:
        if st.button("⬅️ 返回上一步", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()

# ============================================================
# 步骤 4: 生成总结（v12 修改：使用 selected_template_detail）
# ============================================================

def render_step_generate():
    # ===== 版本标识（Step 4 顶部） =====
    st.markdown(f"**🔷 版本: v12_templates_main_2026_05_12 | 当前步骤: Step 4**")
    st.markdown("")

    st.header("🤖 生成会议总结")
    st.markdown("**步骤 4/5**")
    st.markdown("---")

    # 检查必要状态
    if not st.session_state.meeting_id:
        st.error("❌ 会议 ID 不存在")
        if st.button("⬅️ 返回上传", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
        return

    if not st.session_state.transcript:
        st.error("❌ 尚未完成转录")
        if st.button("⬅️ 返回转录", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
        return

    if not st.session_state.selected_template_id:
        st.error("❌ 尚未选择模板")
        if st.button("⬅️ 选择模板", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
        return

    # 显示模板信息
    selected_template_name = st.session_state.selected_template
    selected_template_detail = st.session_state.selected_template_detail

    if selected_template_detail:
        st.info(f"📋 使用模板: **{selected_template_name}**")
        st.caption(f"📝 输出结构: {', '.join(selected_template_detail.get('sections', []))}")

    meeting_id = st.session_state.meeting_id
    api_client = st.session_state.api_client
    transcript = st.session_state.transcript

    # ========================================================
    # 如果已经有 ai_summary，直接显示完成状态
    # ========================================================
    if st.session_state.ai_summary:
        st.success("✅ 总结已生成完成")

        if st.button("➡️ 查看结果", type="primary", use_container_width=True):
            st.session_state.current_step = 5
            st.rerun()

        return

    # ========================================================
    # 总结生成失败
    # ========================================================
    if st.session_state.summary_status == "failed":
        st.error("❌ 总结生成失败")

        if st.session_state.summary_error:
            st.error(st.session_state.summary_error)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 重试生成", use_container_width=True):
                # 重置总结状态
                for key in ['summary_task_id', 'summary_status', 'summary_progress',
                           'summary_message', 'summary_error', 'summary_started',
                           'summary_start_time']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        with col2:
            if st.button("⬅️ 返回模板", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()

        return

    # ========================================================
    # 自动总结生成流程
    # ========================================================

    # 1. 如果尚未启动总结生成任务
    if not st.session_state.summary_started:
        st.subheader("✨ 正在生成会议总结")
        st.write(f"使用模板：{selected_template_name}")

        # v12 修改：传递 template_detail
        with st.spinner("🤖 正在启动总结生成任务..."):
            result = api_client.generate_summary(
                meeting_id,
                st.session_state.selected_template_id,
                template_detail=selected_template_detail,
                transcript=transcript
            )

        if result["success"]:
            st.session_state.summary_started = True
            st.session_state.summary_task_id = result.get("task_id")
            st.session_state.summary_status = result.get("status", "processing")
            # 记录总结生成开始时间，用于 Mock 进度计算
            st.session_state.summary_start_time = int(time.time())

            if result.get("mock"):
                st.warning(result["message"])
            else:
                st.success(result["message"])

            st.rerun()
        else:
            st.error(f"❌ {result['message']}")
            st.session_state.summary_error = result["message"]

            if st.button("🔄 重试", use_container_width=True):
                st.rerun()

            if st.button("⬅️ 返回模板", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()

        return

    # 2. 总结生成任务已启动，轮询状态
    if st.session_state.summary_status not in ["completed", "failed"]:
        st.subheader("✨ 正在生成会议总结")
        st.write(f"使用模板：{selected_template_name}")

        with st.spinner("🤖 AI 正在生成总结..."):
            # 传入开始时间，用于 Mock 进度计算
            result = api_client.get_summary_status(
                meeting_id,
                start_time=st.session_state.summary_start_time
            )

        if result["success"]:
            st.session_state.summary_status = result.get("status", "processing")
            st.session_state.summary_progress = result.get("progress", 0)
            st.session_state.summary_message = result.get("current_step", "处理中")

            # 显示进度
            progress = st.session_state.summary_progress / 100
            st.progress(progress)
            st.info(f"📊 {st.session_state.summary_message} ({st.session_state.summary_progress}%)")

            if result.get("mock"):
                st.caption("⚠️ Mock 模式：模拟总结生成进度")

            # 如果完成，获取总结并自动进入 Step 5
            if result["status"] == "completed":
                # 获取 AI 总结
                with st.spinner("📝 正在获取总结..."):
                    summary_result = api_client.get_summary(meeting_id)

                if summary_result["success"]:
                    st.session_state.ai_summary = summary_result.get("summary", "")
                    st.session_state.markdown_result = summary_result.get("markdown", "")

                    if summary_result.get("mock"):
                        st.warning(summary_result["message"])
                    else:
                        st.success("✅ 总结生成完成！")

                    time.sleep(1)
                    st.session_state.current_step = 5
                    st.rerun()
                else:
                    st.error(f"❌ {summary_result['message']}")
                    st.session_state.summary_error = summary_result["message"]

            # 如果失败
            elif result["status"] == "failed":
                st.error("❌ 总结生成失败")
                st.session_state.summary_error = "总结生成任务失败"

                if st.button("🔄 重试生成", use_container_width=True):
                    # 重置总结状态
                    for key in ['summary_task_id', 'summary_status', 'summary_progress',
                               'summary_message', 'summary_error', 'summary_started',
                               'summary_start_time']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            else:
                # 仍在处理中，2秒后自动刷新
                time.sleep(SUMMARY_POLL_INTERVAL)
                st.rerun()

        else:
            st.error(f"❌ {result['message']}")
            st.session_state.summary_error = result["message"]

            if st.button("🔄 重试", use_container_width=True):
                st.rerun()

# ============================================================
# 步骤 5: 查看结果（保持不变）
# ============================================================

def render_step_result():
    # ===== 版本标识（Step 5 顶部） =====
    st.markdown(f"**🔷 版本: v12_templates_main_2026_05_12 | 当前步骤: Step 5**")
    st.markdown("")

    st.header("✅ 会议总结")
    st.markdown("**步骤 5/5**")
    st.markdown("---")

    # Tab 切换
    tab1, tab2 = st.tabs(["🪄 AI 总结", "📝 完整文字稿"])

    with tab1:
        # 显示真实的 ai_summary（如果有）
        if st.session_state.ai_summary:
            st.markdown(st.session_state.ai_summary)
        else:
            # 友好提示，不崩溃
            st.info(f"""
            ### 📋 会议总结

            **会议时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

            ---

            #### 尚未生成 AI 总结

            请先完成转录和模板选择，AI 将自动生成定制化会议总结。

            ---
            """)

        col1, col2 = st.columns(2)
        with col1:
            st.button("📋 复制总结", use_container_width=True)
        with col2:
            st.button("📥 下载总结", use_container_width=True)

    with tab2:
        # 显示真实的 transcript（如果有）
        if st.session_state.transcript:
            st.markdown("### 📝 完整文字稿")
            st.markdown(st.session_state.transcript)

            # 显示 segments 信息（如果有）
            if st.session_state.transcript_segments:
                with st.expander("📊 查看分段详情", expanded=False):
                    for segment in st.session_state.transcript_segments:
                        st.markdown(f"""
**[{segment.get('start', '')}] {segment.get('speaker', 'Unknown')}**
{segment.get('text', '')}
                        """)
        else:
            st.markdown("""
### 📝 完整文字稿

暂无文字稿，请先完成转录。

---

*完整文字稿由 AI 转录生成*
            """)

        col1, col2 = st.columns(2)
        with col1:
            st.button("📋 复制文字稿", use_container_width=True)
        with col2:
            st.button("📥 下载文字稿", use_container_width=True)

    st.markdown("")

    # 底部按钮
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("⬅️ 返回模板", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

    with col2:
        if st.button("🆕 新会议", use_container_width=True):
            # 清除所有状态
            for key in ['current_step', 'uploaded_file', 'file_meta', 'selected_template',
                       'meeting_id', 'upload_status', 'upload_message',
                       'transcription_task_id', 'transcription_status', 'transcription_progress',
                       'transcription_message', 'transcript', 'transcript_segments',
                       'transcription_error', 'transcription_started', 'transcription_start_time',
                       'summary_task_id', 'summary_status', 'summary_progress',
                       'summary_message', 'summary_error', 'summary_started',
                       'summary_start_time', 'ai_summary', 'markdown_result',
                       'templates', 'templates_loaded', 'templates_error',
                       'selected_template_id', 'selected_template_detail', 'template_mock_mode']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# ============================================================
# 主程序
# ============================================================

def main():
    if DEBUG_MODE:
        st.caption(f"当前运行文件版本：MAIN_ENTRY_UI_FIX_001")
        st.success(f"🎯 当前运行: app_working_v12_templates.py | v12_templates_main_2026_05_12 | {datetime.now().strftime('%H:%M:%S')}")
        st.error(f"🔴 如果您看到这条红色消息，说明文件已正确加载！")

        # 强制重置按钮（用于调试）
        if st.button("🔄 强制重置到 Step 1（调试用）"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown("---")

        # 显示当前版本（页面顶部大标题）
        st.markdown(f"# ✨ v12_templates_main_2026_05_12")
        st.caption(f"🔧 调试模式: {'开启' if DEBUG_MODE else '关闭'}")

        st.markdown("---")

    # 显示当前步骤
    step = st.session_state.current_step

    # 渲染对应步骤
    if step == 1:
        render_step_upload()
    elif step == 2:
        render_step_extract()
    elif step == 3:
        render_step_template()
    elif step == 4:
        render_step_generate()
    elif step == 5:
        render_step_result()

if __name__ == "__main__":
    main()
