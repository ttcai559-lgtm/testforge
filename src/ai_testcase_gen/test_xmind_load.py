"""
测试XMind文件加载
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import xmind
import os

# 获取最新的XMind文件
outputs_dir = r"D:\Python_file\tool_project\testforge\src\ai_testcase_gen\outputs"
xmind_files = [f for f in os.listdir(outputs_dir) if f.endswith('.xmind')]

if xmind_files:
    # 使用最新的文件
    latest_file = max([os.path.join(outputs_dir, f) for f in xmind_files], key=os.path.getmtime)
    print(f"测试文件: {os.path.basename(latest_file)}")
    print(f"文件大小: {os.path.getsize(latest_file)} 字节")
    print()

    try:
        print("正在加载XMind文件...")
        wb = xmind.load(latest_file)
        print("✅ 加载成功!")
        print()

        sheet = wb.getPrimarySheet()
        root = sheet.getRootTopic()

        print(f"根主题: {root.getTitle()}")

        topics = root.getSubTopics()
        print(f"模块数量: {len(topics)}")
        print()

        # 统计测试用例数量
        def count_cases(topic, level=0):
            count = 0
            indent = "  " * level
            title = topic.getTitle()

            # 检查是否是测试用例节点（带emoji标记）
            if any(emoji in title for emoji in ["✅", "⚠️", "❌"]):
                count = 1
                print(f"{indent}- {title[:50]}...")

            # 递归统计子节点
            for sub in topic.getSubTopics():
                count += count_cases(sub, level + 1)

            return count

        print("前5个测试用例:")
        case_count = 0
        for module in topics:
            if case_count >= 5:
                break
            case_count += count_cases(module)

        print()
        print(f"✅ XMind文件完全正常，可以被Python加载和解析！")

    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ 没有找到XMind文件")
