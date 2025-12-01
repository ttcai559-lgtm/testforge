"""
修复XMind文件缺失的必要文件
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import zipfile
import os
from datetime import datetime

def fix_xmind_file(xmind_path):
    """
    为XMind文件添加缺失的必要文件

    Args:
        xmind_path: XMind文件路径
    """
    print(f"修复文件: {os.path.basename(xmind_path)}")

    # 读取现有文件
    with zipfile.ZipFile(xmind_path, 'r') as zin:
        existing_files = zin.namelist()
        print(f"当前包含 {len(existing_files)} 个文件")

        # 读取content.xml来提取root topic ID
        content_xml = zin.read('content.xml').decode('utf-8')

        # 提取root topic ID (简单正则匹配)
        import re
        root_id_match = re.search(r'<sheet id="([^"]+)"', content_xml)
        sheet_id = root_id_match.group(1) if root_id_match else "sheet1"

    # 创建临时文件
    temp_path = xmind_path + ".tmp"

    # 创建新的zip文件，包含所有原始文件 + 缺失文件
    with zipfile.ZipFile(xmind_path, 'r') as zin:
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            # 复制所有现有文件
            for item in zin.namelist():
                zout.writestr(item, zin.read(item))

            # 添加meta.xml（如果缺失）
            if 'meta.xml' not in existing_files:
                print("  添加 meta.xml")
                meta_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">
    <Author>
        <Name>TestForge AI</Name>
    </Author>
    <Create>
        <Time>{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}Z</Time>
    </Create>
    <Creator>
        <Name>TestForge</Name>
        <Version>1.0</Version>
    </Creator>
</meta>'''
                zout.writestr('meta.xml', meta_xml.encode('utf-8'))

            # 添加manifest.xml（如果缺失）
            if 'META-INF/manifest.xml' not in existing_files:
                print("  添加 META-INF/manifest.xml")
                # 获取所有文件列表
                all_files = existing_files.copy()
                if 'meta.xml' not in all_files:
                    all_files.append('meta.xml')

                # 生成manifest
                file_entries = []
                for f in all_files:
                    if f != 'META-INF/manifest.xml':
                        media_type = 'text/xml' if f.endswith('.xml') else 'application/octet-stream'
                        file_entries.append(f'    <file-entry full-path="{f}" media-type="{media_type}"/>')

                manifest_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">
{chr(10).join(file_entries)}
</manifest>'''
                zout.writestr('META-INF/manifest.xml', manifest_xml.encode('utf-8'))

    # 替换原文件
    os.replace(temp_path, xmind_path)
    print("✅ 修复完成!")

    # 验证
    with zipfile.ZipFile(xmind_path, 'r') as z:
        final_files = z.namelist()
        print(f"修复后包含 {len(final_files)} 个文件:")
        for f in final_files:
            print(f"  ✓ {f}")

if __name__ == "__main__":
    # 修复所有XMind文件
    outputs_dir = r"D:\Python_file\tool_project\testforge\src\ai_testcase_gen\outputs"
    xmind_files = [f for f in os.listdir(outputs_dir) if f.endswith('.xmind')]

    if xmind_files:
        print(f"找到 {len(xmind_files)} 个XMind文件")
        print("="*60)
        print()

        for xmind_file in xmind_files:
            xmind_path = os.path.join(outputs_dir, xmind_file)
            fix_xmind_file(xmind_path)
            print()

        print("="*60)
        print("✅ 所有文件修复完成!")
    else:
        print("❌ 没有找到XMind文件")
