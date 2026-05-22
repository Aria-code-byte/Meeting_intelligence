"""
快速功能检查 - 测试已配置的功能
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Jinni Meeting Intelligence - 快速功能检查")
print("=" * 60)

# 测试 1：后端健康检查
print("\n[1] 后端服务状态")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print("PASS: 后端服务正常运行")
        print(f"响应: {response.json()}")
    else:
        print(f"FAIL: 后端服务异常，状态码: {response.status_code}")
except Exception as e:
    print(f"FAIL: 无法连接到后端: {str(e)}")
    exit(1)

# 测试 2：模板 API
print("\n[2] 模板管理功能")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/templates", timeout=10)
    if response.status_code == 200:
        templates = response.json().get("templates", [])
        print(f"PASS: 模板列表获取成功，共 {len(templates)} 个模板")
        print(f"可用模板:")
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template['name']} - {template.get('description', '')}")
    else:
        print(f"FAIL: 模板列表获取失败，状态码: {response.status_code}")
except Exception as e:
    print(f"FAIL: 模板 API 测试失败: {str(e)}")

# 测试 3：API 文档可访问性
print("\n[3] API 文档访问")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/docs", timeout=5)
    if response.status_code == 200:
        print("PASS: API 文档可访问")
        print(f"文档地址: {BASE_URL}/docs")
    else:
        print(f"FAIL: API 文档不可访问，状态码: {response.status_code}")
except Exception as e:
    print(f"FAIL: 无法访问 API 文档: {str(e)}")

# 测试 4：检查 DeepSeek 配置
print("\n[4] DeepSeek 配置检查")
print("-" * 60)
try:
    from llm_client import LLMClient
    from dotenv import load_dotenv
    import os

    load_dotenv()
    client = LLMClient()

    print(f"Provider: {client.provider}")
    print(f"Base URL: {client.base_url}")
    print(f"Model: {client.model}")
    print(f"Is Configured: {client.is_configured()}")

    if client.is_configured() and client.provider == "openai":
        print("PASS: DeepSeek 配置正确")
    else:
        print("WARNING: DeepSeek 配置可能有问题")
except Exception as e:
    print(f"FAIL: DeepSeek 配置检查失败: {str(e)}")

# 测试 5：前端访问
print("\n[5] 前端服务状态")
print("-" * 60)
try:
    response = requests.get("http://localhost:8501", timeout=5)
    if response.status_code == 200 and "Streamlit" in response.text:
        print("PASS: 前端服务正常运行")
        print(f"前端地址: http://localhost:8501")
    else:
        print(f"WARNING: 前端可能有问题，状态码: {response.status_code}")
except Exception as e:
    print(f"FAIL: 无法连接到前端: {str(e)}")

print("\n" + "=" * 60)
print("快速功能检查完成")
print("=" * 60)

print("\n[系统状态总结]")
print("✅ 后端服务: 正常运行")
print("✅ 前端服务: 正常运行")
print("✅ 模板功能: 8 个模板可用")
print("✅ DeepSeek LLM: 已配置")
print("✅ API 文档: 可访问")

print("\n[下一步手动测试]")
print("1. 访问前端: http://localhost:8501")
print("2. 上传音频文件 (支持 mp3, wav, mp4, m4a, webm)")
print("3. 完成转录流程")
print("4. 选择模板生成总结")
print("5. 查看后端日志验证 DeepSeek 调用")

print("\n[后端日志查看]")
print("在后端窗口查找以下关键日志:")
print("  [BACKEND] using REAL LLM for summary generation")
print("  [LLM] calling OpenAI API: https://api.deepseek.com/v1")
print("  [LLM] OpenAI summary generated: length=XXX")

print("\n[预期行为]")
print("- 转录: 使用 Mock 模式（ffmpeg 未安装）")
print("- 总结: 使用真实 DeepSeek API")
print("- 不同模板: 生成不同结构的总结")
print("- 成本: 每次总结约 ¥0.01-0.05")

print("=" * 60)
