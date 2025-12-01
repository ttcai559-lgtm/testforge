"""
直接测试用例生成(绕过Streamlit)
"""
import sys
import os
import glob

# 设置UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from generator import TestCaseGenerator

# 查找最新上传的文档,检查两个可能的目录
upload_dirs = [
    r"D:\Python_file\tool_project\uploads",
    r"D:\Python_file\tool_project\testforge\src\ai_testcase_gen\uploads",
]

docs = []
for upload_dir in upload_dirs:
    if os.path.exists(upload_dir):
        # 查找.docx和.pdf文件
        for pattern in ["*.docx", "*.pdf", "*.doc"]:
            for file_path in glob.glob(os.path.join(upload_dir, pattern)):
                # 过滤临时文件和空文件
                filename = os.path.basename(file_path)
                if filename.startswith("~$"):  # Word临时文件
                    continue
                if os.path.getsize(file_path) == 0:  # 空文件
                    continue
                docs.append(file_path)

if not docs:
    print(f"Error: No .docx files found in:")
    for d in upload_dirs:
        print(f"  - {d}")
    sys.exit(1)

# 使用最新的文档
doc_path = max(docs, key=os.path.getmtime)

# 确保路径使用正确的编码
if isinstance(doc_path, bytes):
    doc_path = doc_path.decode('utf-8')

# 规范化路径
doc_path = os.path.normpath(doc_path)

print(f"Using document: {os.path.basename(doc_path)}")
print(f"Full path: {doc_path}")

print("="*60)
print("开始生成测试用例...")
print(f"文档: {doc_path}")
print("模型: claude (Sonnet 4.5)")
print("="*60)
print()

try:
    # 创建生成器
    generator = TestCaseGenerator(ai_model="claude")

    # 生成测试用例 (暂时禁用缺陷检测和问题生成，避免502错误)
    result = generator.generate(
        document_path=doc_path,
        enable_defect_detection=False,
        enable_question_generation=False
    )

    print("\n" + "="*60)
    print("生成成功!")
    print("="*60)
    print(f"XMind文件: {result.get('xmind_path', 'N/A')}")

    # 检查是否有statistics字段(旧版本)或summary字段
    stats = result.get('statistics') or result.get('summary', {})

    print(f"测试用例数: {stats.get('total_cases', stats.get('total_test_cases', 0))}")
    print(f"问题清单数: {stats.get('questions_count', stats.get('total_questions', 0))}")
    print(f"需求缺陷数: {stats.get('defects_count', stats.get('total_defects', 0))}")
    print()

    total_cases = stats.get('total_cases', stats.get('total_test_cases', 0))
    if total_cases > 0:
        print("✅ 测试用例生成成功!")
    else:
        print("⚠️ 警告: 没有生成测试用例")

except Exception as e:
    print("\n" + "="*60)
    print("生成失败!")
    print("="*60)
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
