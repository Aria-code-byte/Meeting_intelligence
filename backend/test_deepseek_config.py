"""
测试 DeepSeek 配置
"""
import os
from dotenv import load_dotenv
from llm_client import LLMClient

# 加载环境变量
load_dotenv()

print("=" * 60)
print("DeepSeek Configuration Check")
print("=" * 60)

# 显示当前配置
print(f"\n[Environment Variables]")
print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")
print(f"OPENAI_MODEL: {os.getenv('OPENAI_MODEL')}")

api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    if api_key.startswith('sk-your') or api_key.startswith('sk-your-deepseek-key-here'):
        print(f"OPENAI_API_KEY: [NOT CONFIGURED] Still placeholder")
    else:
        print(f"OPENAI_API_KEY: [CONFIGURED] {api_key[:20]}...")
else:
    print(f"OPENAI_API_KEY: [NOT SET]")

# 创建 LLMClient 并检查
print(f"\n[LLMClient Status]")
client = LLMClient()
print(f"Provider: {client.provider}")
print(f"Base URL: {client.base_url}")
print(f"Model: {client.model}")
print(f"Is Configured: {client.is_configured()}")

# 验证配置
print(f"\n[Configuration Validation]")
errors = []

if client.provider != "openai":
    errors.append("[ERROR] LLM_PROVIDER should be 'openai'")

if "deepseek.com" not in client.base_url:
    errors.append("[ERROR] OPENAI_BASE_URL should point to DeepSeek")

if client.model != "deepseek-chat":
    errors.append("[ERROR] OPENAI_MODEL should be 'deepseek-chat'")

if not client.is_configured():
    errors.append("[ERROR] OPENAI_API_KEY not configured or invalid")

if errors:
    print("\n".join(errors))
    print("\n[WARNING] Configuration has issues, please check backend/.env")
else:
    print("[OK] All configuration items are correct")
    print("\n[Next Steps]")
    print("1. If API Key is still placeholder, please fill in real DeepSeek API Key")
    print("2. If API Key is configured, you can start backend:")
    print("   cd backend")
    print("   python -m uvicorn main:app --reload --port 8000")
    print("3. Run full workflow, backend log should show:")
    print("   [BACKEND] using REAL LLM for summary generation")
    print("   [BACKEND] llm_provider: openai")
    print("   [BACKEND] OpenAI URL: https://api.deepseek.com/v1")

print("\n" + "=" * 60)
