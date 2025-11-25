"""
Test Storage Layer
"""

import sys
sys.path.insert(0, '.')

from src.storage import YAMLStorage
import os

print("Testing YAML Storage...")
print("=" * 50)

# Create storage
storage = YAMLStorage("./test_storage_temp")

# Test 1: Save testcase
print("\n[Test 1] Save testcase")
testcase = {
    "name": "test_api",
    "description": "Test API endpoint",
    "request": {
        "method": "GET",
        "url": "https://api.example.com/users",
        "headers": {"Authorization": "Bearer token"}
    },
    "assertions": [
        "status == 200",
        "response['users'] != None"
    ]
}

filepath = storage.save_testcase(testcase, "test_api.yaml")
print(f"[OK] Saved to: {filepath}")

# Test 2: Load testcase
print("\n[Test 2] Load testcase")
loaded = storage.load_testcase("test_api.yaml")
print(f"[OK] Loaded testcase: {loaded['name']}")
print(f"[OK] Description: {loaded['description']}")

# Test 3: List testcases
print("\n[Test 3] List testcases")
testcases = storage.list_testcases()
print(f"[OK] Found {len(testcases)} testcase(s): {testcases}")

# Test 4: Export/Import
print("\n[Test 4] Export/Import")
yaml_str = storage.export_testcase(testcase)
print(f"[OK] Exported to YAML string ({len(yaml_str)} chars)")
imported = storage.import_testcase(yaml_str)
print(f"[OK] Imported testcase: {imported['name']}")

# Cleanup
print("\n[Cleanup] Removing test files...")
import shutil
if os.path.exists("./test_storage_temp"):
    shutil.rmtree("./test_storage_temp")
print("[OK] Cleanup completed")

print("\n" + "=" * 50)
print("[SUCCESS] Storage layer is working!")
