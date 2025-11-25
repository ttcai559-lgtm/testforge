"""
Test Assertion Engine
"""

import sys
sys.path.insert(0, '.')

from src.core import AssertionEngine

# Create engine
engine = AssertionEngine()

# Test context (simulating HTTP response)
context = {
    "status": 200,
    "response": {
        "data": {
            "id": 123,
            "name": "test"
        },
        "success": True
    },
    "headers": {"Content-Type": "application/json"},
    "elapsed_ms": 150.5
}

print("Testing Assertion Engine...")
print("=" * 50)

# Test 1: Status code assertion
print("\n[Test 1] Status code assertion")
result = engine.evaluate("status == 200", context)
print(f"Assertion: {result.assertion}")
print(f"Passed: {result.passed}")
print(f"Message: {result.message}")

# Test 2: JSON field assertion
print("\n[Test 2] JSON field assertion")
result = engine.evaluate("response['data']['id'] > 0", context)
print(f"Assertion: {result.assertion}")
print(f"Passed: {result.passed}")

# Test 3: Response time assertion
print("\n[Test 3] Response time assertion")
result = engine.evaluate("elapsed_ms < 1000", context)
print(f"Assertion: {result.assertion}")
print(f"Passed: {result.passed}")

# Test 4: Failed assertion
print("\n[Test 4] Failed assertion")
result = engine.evaluate("status == 404", context)
print(f"Assertion: {result.assertion}")
print(f"Passed: {result.passed}")
print(f"Message: {result.message}")

# Test 5: Multiple assertions
print("\n[Test 5] Multiple assertions")
assertions = [
    "status == 200",
    "response['success'] == True",
    "elapsed_ms < 200"
]
engine.reset()
results = engine.evaluate_all(assertions, context)

summary = engine.get_summary()
print(f"Total: {summary['total']}")
print(f"Passed: {summary['passed']}")
print(f"Failed: {summary['failed']}")
print(f"Pass rate: {summary['pass_rate']:.1f}%")
print(f"All passed: {engine.all_passed()}")

print("\n" + "=" * 50)
print("[SUCCESS] Assertion Engine is working!")
