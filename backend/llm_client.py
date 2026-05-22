"""
LLM 客户端 - 支持多种 LLM 提供商
"""
import os
import httpx
from typing import Optional, Dict, Any


class LLMClient:
    """LLM 客户端"""

    def __init__(self):
        # 从环境变量读取配置
        self.provider = os.getenv("LLM_PROVIDER", "ollama")  # 默认使用 ollama

        # OpenAI 兼容配置
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Ollama 配置
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2:7b")

        # 检查配置
        if self.provider == "ollama":
            print(f"[LLM] Using Ollama: {self.ollama_base_url}, model={self.ollama_model}")
        elif self.provider == "openai":
            if not self.api_key:
                print("[LLM] WARNING: OPENAI_API_KEY not set, will use mock mode")
            else:
                print(f"[LLM] Using OpenAI: {self.base_url}, model={self.model}")

    def is_configured(self) -> bool:
        """检查是否已配置"""
        if self.provider == "ollama":
            # Ollama 不需要 API key，直接返回 True
            # 注意：Ollama 服务需要单独启动
            return True
        elif self.provider == "openai":
            # OpenAI 需要 API key
            if not self.api_key:
                return False
            # 检查是否是占位符
            if self.api_key.startswith('sk-your') or 'your' in self.api_key.lower():
                print(f"[LLM] WARNING: API key appears to be a placeholder, not configured")
                return False
            return bool(self.api_key)
        return False

    def generate_summary(
        self,
        transcript: str,
        template_name: str,
        template_description: str,
        template_sections: list,
        template_prompt: str
    ) -> str:
        """
        使用 LLM 生成会议总结

        Args:
            transcript: 会议文字稿
            template_name: 模板名称
            template_description: 模板描述
            template_sections: 模板输出结构
            template_prompt: 模板提示词

        Returns:
            markdown 格式的总结
        """
        if not self.is_configured():
            raise ValueError("LLM not configured")

        # 构建提示词
        sections_text = "\n".join([f"- {section}" for section in template_sections])

        system_prompt = f"""你是一个专业会议总结助手。

请根据以下会议文字稿，按照用户选择的总结模板生成 Markdown 会议总结。

模板名称：
{template_name}

模板说明：
{template_description}

模板输出结构：
{sections_text}

模板要求：
{template_prompt}

会议文字稿：
{{transcript}}

要求：
1. 必须严格按照模板结构输出
2. 不要编造会议中没有的信息
3. 待办事项要包含负责人、事项、截止时间，如果没有则写"未明确"
4. 输出 Markdown 格式
5. 不要输出无关解释
"""

        try:
            if self.provider == "ollama":
                # 使用 Ollama API
                print(f"[LLM] calling Ollama API: {self.ollama_base_url}")
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(
                        f"{self.ollama_base_url}/api/chat",
                        json={
                            "model": self.ollama_model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": system_prompt
                                },
                                {
                                    "role": "user",
                                    "content": transcript
                                }
                            ],
                            "stream": False
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        content = result["message"]["content"]
                        print(f"[LLM] Ollama summary generated: length={len(content)}")
                        return content
                    else:
                        error_msg = f"Ollama API error: status={response.status_code}, body={response.text}"
                        print(f"[LLM] {error_msg}")
                        raise Exception(error_msg)

            elif self.provider == "openai":
                # 使用 OpenAI 兼容 API
                print(f"[LLM] calling OpenAI API: {self.base_url}")
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": system_prompt
                                },
                                {
                                    "role": "user",
                                    "content": transcript
                                }
                            ],
                            "temperature": 0.7,
                            "max_tokens": 2000
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        content = result["choices"][0]["message"]["content"]
                        print(f"[LLM] OpenAI summary generated: length={len(content)}")
                        return content
                    else:
                        error_msg = f"OpenAI API error: status={response.status_code}, body={response.text}"
                        print(f"[LLM] {error_msg}")
                        raise Exception(error_msg)

            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

        except Exception as e:
            print(f"[LLM] generate_summary failed: {str(e)}")
            raise
