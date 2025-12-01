"""
检查XMind文件缺失的必要文件
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import zipfile
import os

outputs_dir = r"D:\Python_file\tool_project\testforge\src\ai_testcase_gen\outputs"
xmind_files = [f for f in os.listdir(outputs_dir) if f.endswith('.xmind')]

if xmind_files:
    latest_file = max([os.path.join(outputs_dir, f) for f in xmind_files], key=os.path.getmtime)

    print(f"检查文件: {os.path.basename(latest_file)}")
    print()

    z = zipfile.ZipFile(latest_file)
    files = z.namelist()

    print("当前包含的文件:")
    for f in files:
        print(f"  ✓ {f}")
    print()

    # XMind标准格式需要的文件
    required_files = {
        'content.xml': '测试用例内容',
        'META-INF/manifest.xml': '文件清单(必需)',
        'meta.xml': '元数据(必需)',
        'styles.xml': '样式定义',
    }

    print("缺失的文件:")
    missing = []
    for file, desc in required_files.items():
        if file not in files:
            print(f"  X {file} - {desc}")
            missing.append(file)

    if not missing:
        print("  (无)")
    else:
        print()
        print(f"检测结果: 缺少 {len(missing)} 个关键文件")
        print("这可能导致XMind桌面应用无法打开文件")
