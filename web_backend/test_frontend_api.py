"""
测试前端 API 客户端是否能正确调用后端
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"
meeting_id = "meeting_d126c5406f5c"  # 使用刚才生成的会议 ID

print("=" * 60)
print("测试前端 API 调用")
print("=" * 60)

# 测试 1：健康检查
print("\n[测试 1] 后端健康检查")
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    backend_available = response.status_code == 200
    print(f"后端可用: {backend_available}")
except Exception as e:
    print(f"后端不可用: {e}")
    backend_available = False

if not backend_available:
    print("\n[错误] 后端不可用，无法继续测试")
    exit(1)

# 测试 2：获取总结
print(f"\n[测试 2] 获取总结")
print(f"会议 ID: {meeting_id}")
print(f"API URL: {API_BASE_URL}/api/meetings/{meeting_id}/summary")

try:
    response = requests.get(
        f"{API_BASE_URL}/api/meetings/{meeting_id}/summary",
        timeout=30
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        success = result.get("success", False)
        summary = result.get("summary", "")
        template_id = result.get("template_id", "")

        print(f"成功: {success}")
        print(f"总结长度: {len(summary)}")
        print(f"模板 ID: {template_id}")

        if len(summary) > 0:
            print(f"\n[SUCCESS] 获取到真实总结！")
            print(f"\n总结预览:")
            print("=" * 60)
            print(summary[:300] + "...")
            print("=" * 60)

            # 检查是否是示例内容
            mock_indicators = [
                "本次会议主要围绕产品需求、开发计划与后续风险展开讨论",
                "Speaker 2：完成前端页面开发",
                "Speaker 1：完成后端 API 开发"
            ]

            is_mock = any(indicator in summary for indicator in mock_indicators)
            if is_mock:
                print(f"\n[WARNING] 这看起来像是示例内容！")
            else:
                print(f"\n[CONFIRMED] 这是真实的 DeepSeek 总结！")
        else:
            print(f"\n[ERROR] 总结为空！")
    else:
        print(f"[ERROR] API 调用失败")
        print(f"响应: {response.text}")

except Exception as e:
    print(f"[ERROR] 请求异常: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)