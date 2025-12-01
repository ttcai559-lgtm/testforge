"""
直接测试Anthropic SDK连接
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from anthropic import Anthropic

# 配置
AUTH_TOKEN = "cr_075a7d7c5c39be523c18da675acf2ac0ce6dbdd2129454370b17797eb43d20a0"
BASE_URL = "http://47.251.110.97:3000/api"
MODEL = "claude-sonnet-4-5-20250929"

print("="*60)
print("测试Anthropic SDK连接")
print("="*60)
print(f"BASE_URL: {BASE_URL}")
print(f"MODEL: {MODEL}")
print()

try:
    client = Anthropic(
        api_key=AUTH_TOKEN,
        base_url=BASE_URL
    )

    print("发送测试请求...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Say hi in Chinese"}
        ]
    )

    print("✅ 成功!")
    print(f"响应: {response.content[0].text}")

except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()
