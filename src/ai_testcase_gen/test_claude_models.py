"""
测试Claude API和可用模型
"""
import os
from anthropic import Anthropic

# 配置
AUTH_TOKEN = "cr_075a7d7c5c39be523c18da675acf2ac0ce6dbdd2129454370b17797eb43d20a0"
BASE_URL = "http://47.251.110.97:3000/api"

# 常见的Claude模型名称
MODELS_TO_TEST = [
    "claude-3-5-sonnet-20241022",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
    "claude-2.1",
    "claude-2",
    "claude-instant-1.2",
]

print("=" * 60)
print("测试Claude API和可用模型")
print("=" * 60)
print(f"API地址: {BASE_URL}")
print()

client = Anthropic(
    api_key=AUTH_TOKEN,
    base_url=BASE_URL
)

working_models = []

for model in MODELS_TO_TEST:
    print(f"Testing model: {model} ... ", end="", flush=True)
    try:
        # 测试英文
        response = client.messages.create(
            model=model,
            max_tokens=20,
            messages=[
                {"role": "user", "content": "Say hi in Chinese"}
            ]
        )
        chinese_response = response.content[0].text
        print(f"[OK] Available!")
        print(f"  中文响应: {chinese_response}")
        working_models.append(model)
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not_found" in error_msg:
            print("[FAIL] Not supported")
        elif "401" in error_msg or "unauthorized" in error_msg:
            print("[FAIL] Auth error")
        else:
            print(f"[FAIL] Error: {error_msg[:50]}")

print()
if working_models:
    print("可用的模型列表:")
    for m in working_models:
        print(f"  - {m}")
else:
    print("没有找到可用的模型!")

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
