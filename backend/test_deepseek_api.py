"""
测试 DeepSeek API 连通性
"""
import os
import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("DeepSeek API Connectivity Test")
print("=" * 60)

# 获取配置
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
model = os.getenv("OPENAI_MODEL", "deepseek-chat")

# 显示配置
print(f"\n[Configuration]")
print(f"API Key: {api_key[:20]}...{api_key[-10:] if api_key else 'NOT_SET'}")
print(f"Base URL: {base_url}")
print(f"Model: {model}")

# 检查配置
if not api_key:
    print("\n[ERROR] API Key not configured")
    print("Please set OPENAI_API_KEY in backend/.env")
    exit(1)

if api_key.startswith('sk-your') or 'your' in api_key.lower():
    print("\n[ERROR] API Key appears to be a placeholder")
    print("Please set a real DeepSeek API Key in backend/.env")
    exit(1)

print("\n[Test 1] Basic API Health Check")
print("-" * 60)

try:
    # 测试 1：调用 chat completions API
    print("Sending test request to DeepSeek API...")

    test_prompt = "请用一句话介绍你自己。"

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": test_prompt
                    }
                ],
                "max_tokens": 100
            }
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            print(f"\n[SUCCESS] API connection successful!")
            print(f"\nResponse:")
            print(f"  Content: {content}")
            print(f"\nToken Usage:")
            print(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")

            # 计算成本
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

            # DeepSeek 定价: 输入 ¥1/1M tokens, 输出 ¥2/1M tokens
            cost = (prompt_tokens * 0.000001 + completion_tokens * 0.000002)
            print(f"\nEstimated Cost: ¥{cost:.6f}")

        elif response.status_code == 401:
            print(f"\n[ERROR] Authentication failed")
            print("Reason: Invalid API Key")
            print("\nPlease check:")
            print("  1. API Key is correct")
            print("  2. API Key is not expired")
            print("  3. Account has sufficient balance")

        elif response.status_code == 429:
            print(f"\n[ERROR] Rate limit exceeded")
            print("Reason: Too many requests")
            print("Please wait a moment and try again")

        else:
            print(f"\n[ERROR] API request failed")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

except httpx.ConnectError as e:
    print(f"\n[ERROR] Connection failed")
    print(f"Reason: Cannot connect to {base_url}")
    print("\nPossible causes:")
    print("  1. Network connection issue")
    print("  2. DeepSeek API service is down")
    print("  3. Firewall blocking the connection")
    print(f"\nError details: {str(e)}")

except httpx.TimeoutException:
    print(f"\n[ERROR] Request timeout")
    print("Reason: API request took too long")
    print("\nPossible causes:")
    print("  1. Network latency")
    print("  2. DeepSeek API is slow")
    print("  3. Request was too complex")

except Exception as e:
    print(f"\n[ERROR] Unexpected error")
    print(f"Error type: {type(e).__name__}")
    print(f"Error details: {str(e)}")

print("\n" + "=" * 60)

if response.status_code == 200:
    print("\n[CONCLUSION] DeepSeek API is working correctly!")
    print("\nYou can now:")
    print("  1. Start the backend: python -m uvicorn main:app --reload --port 8000")
    print("  2. Start the frontend: start_jinni.bat")
    print("  3. Run full workflow to test real LLM summary")
else:
    print("\n[CONCLUSION] DeepSeek API connection failed")
    print("\nPlease fix the issues above before using the system")

print("\n" + "=" * 60)
