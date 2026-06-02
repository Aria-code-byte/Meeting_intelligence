"""
LLM 增强服务
使用 DeepSeek 等大语言模型优化会议转录文本
"""

import os
import json
from typing import List
from datetime import datetime
from fastapi import HTTPException

from .models import TranscriptTurn, EnhancedTranscriptTurn


class EnhancementService:
    """LLM 增强服务"""

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")

    async def enhance_transcript(
        self,
        transcript_turns: List[TranscriptTurn]
    ) -> List[EnhancedTranscriptTurn]:
        """
        使用 DeepSeek 优化转录文本

        Args:
            transcript_turns: 原始转录轮次列表

        Returns:
            增强后的转录轮次列表
        """
        if not self.api_key:
            raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置")

        # 导入 openai 客户端
        try:
            from openai import OpenAI
        except ImportError:
            raise HTTPException(status_code=500, detail="未安装 openai 包: pip install openai")

        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 构建提示词
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(transcript_turns)

        try:
            # 根据 turns 数量动态调整 max_tokens
            # 每个 turn 平均约 50-100 tokens，留出安全余量
            estimated_tokens = len(transcript_turns) * 150
            max_tokens = min(max(estimated_tokens, 2000), 16000)  # 最小 2000，最大 16000

            print(f"[Enhancement] 动态 max_tokens: {max_tokens} (turns: {len(transcript_turns)})")

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=max_tokens
            )

            # 解析响应
            enhanced_turns = self._parse_response(
                response.choices[0].message.content,
                transcript_turns
            )

            return enhanced_turns

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DeepSeek API 调用失败: {str(e)}")

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一位专业的会议纪要整理专家。你的任务是优化会议转录文本。

### 核心原则：
1. **保持原意**：不要添加原文中没有的内容
2. **修正错误**：修正同音错别字和 ASR 识别错误
3. **删除冗余**：删除"就是"、"那个"、"然后"、"呃"、"是吧"等冗余语气词
4. **保持口语风格**：不要过度书面化，保持自然的对话风格
5. **补全标点**：在合适的位置添加标点符号

### 同音错别字对照表：
| 错误 | 正确 |
|------|------|
| 蓝哥舞 | 蓝哥我 |
| 骗案 | 偏远 |
| 带/代/待 | 贷（贷款相关）|
| 车带 | 车贷 |
| 房带 | 房贷 |
| 消费带 | 消费贷 |
| 唱吃 | 偿债 |
| 平穷 | 贫穷 |
| 花杯 | 花呗 |

### 输出格式：
请按照以下 JSON 格式输出优化后的转录：

[
  {
    "speaker": "发言人名称",
    "start": 开始时间（秒）,
    "end": 结束时间（秒）,
    "text": "优化后的文本"
  }
]

注意：保持原有的说话人、时间戳结构，只优化 text 字段的内容。"""

    def _build_user_prompt(self, transcript_turns: List[TranscriptTurn]) -> str:
        """构建用户提示词"""
        turns_data = []
        for turn in transcript_turns:
            turns_data.append({
                "speaker": turn.speaker,
                "start": turn.start,
                "end": turn.end,
                "text": turn.text
            })

        return f"""请优化以下会议转录：

{json.dumps(turns_data, ensure_ascii=False, indent=2)}

要求：
1. 修正错别字和识别错误
2. 删除冗余语气词
3. 保持原意不变
4. 输出 JSON 格式"""

    def _parse_response(
        self,
        response_content: str,
        original_turns: List[TranscriptTurn]
    ) -> List[EnhancedTranscriptTurn]:
        """解析 LLM 响应"""
        print(f"[Enhancement] LLM 原始响应 (前500字): {response_content[:500]}...")

        # 尝试多种方式提取 JSON
        json_content = response_content.strip()

        # 方法1: 直接解析
        try:
            enhanced_data = json.loads(json_content)
            print(f"[Enhancement] JSON 解析成功（方法1: 直接解析）")
        except json.JSONDecodeError:
            # 方法2: 提取 JSON 数组部分（处理 ```json ... ``` 格式）
            print(f"[Enhancement] 直接解析失败，尝试提取 JSON 数组...")

            # 查找 JSON 数组的开始和结束
            array_start = json_content.find('[')
            array_end = json_content.rfind(']') + 1

            if array_start >= 0 and array_end > array_start:
                json_content = json_content[array_start:array_end]
                print(f"[Enhancement] 提取的 JSON 长度: {len(json_content)}")

                try:
                    enhanced_data = json.loads(json_content)
                    print(f"[Enhancement] JSON 解析成功（方法2: 提取数组）")
                except json.JSONDecodeError as e:
                    print(f"[Warning] JSON 解析仍然失败: {e}")
                    print(f"[Warning] 返回原始转录作为 fallback")
                    return [
                        EnhancedTranscriptTurn(
                            speaker=turn.speaker,
                            start=turn.start,
                            end=turn.end,
                            text=turn.text
                        )
                        for turn in original_turns
                    ]
            else:
                print(f"[Warning] 无法找到 JSON 数组")
                return [
                    EnhancedTranscriptTurn(
                        speaker=turn.speaker,
                        start=turn.start,
                        end=turn.end,
                        text=turn.text
                    )
                    for turn in original_turns
                ]

        print(f"[Enhancement] JSON 解析成功，数据类型: {type(enhanced_data)}, 长度: {len(enhanced_data)}")

        # 验证并构建结果
        enhanced_turns = []
        for i, item in enumerate(enhanced_data):
            if i < len(original_turns):
                enhanced_turns.append(EnhancedTranscriptTurn(
                    speaker=item.get("speaker", original_turns[i].speaker),
                    start=item.get("start", original_turns[i].start),
                    end=item.get("end", original_turns[i].end),
                    text=item.get("text", original_turns[i].text)
                ))

                # 打印前3个turn的对比
                if i < 3:
                    original_text = original_turns[i].text
                    enhanced_text = enhanced_turns[i].text
                    is_same = original_text == enhanced_text
                    print(f"[Enhancement] Turn {i} 对比:")
                    print(f"  原始: {original_text[:50]}...")
                    print(f"  增强: {enhanced_text[:50]}...")
                    print(f"  相同: {is_same}")
            else:
                enhanced_turns.append(EnhancedTranscriptTurn(**item))

        return enhanced_turns
