"""
快速测试 HTTP Handler
"""

import sys
sys.path.insert(0, '.')

from src.protocols import HTTPHandler

# 测试1: 构建请求
print("测试1: 构建HTTP请求...")
handler = HTTPHandler()

config = {
    "method": "GET",
    "url": "https://httpbin.org/get",
    "params": {"test": "value"}
}

request = handler.build_request(config)
print(f"[OK] Request built: {request.method} {request.url}")

# Test 2: Send request
print("\nTest 2: Sending HTTP request...")
response = handler.send_request(request)
print(f"[OK] Status code: {response.status_code}")
print(f"[OK] Response time: {response.elapsed_ms:.2f}ms")
print(f"[OK] Response body type: {type(response.body)}")

# Test 3: Parse response
print("\nTest 3: Parse response...")
parsed = handler.parse_response(response)
print(f"[OK] Parsed successfully, fields: {list(parsed.keys())}")

print("\n[SUCCESS] All tests passed! HTTP Handler is working.")
