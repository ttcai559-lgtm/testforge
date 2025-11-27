#!/usr/bin/env python3
"""
修复proto文件中的枚举命名冲突
将 IAB11, IAB12 等改为 IAB_CAT_11, IAB_CAT_12 等
"""
import re

def fix_proto_enums(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 需要替换的模式：单独的IAB后跟2位数字（不是后跟下划线和数字）
    # IAB11 = 191; -> IAB_CAT_11 = 191;
    # 但不替换 IAB11_1 = 192;

    # 匹配 IAB + 两位数字 + 空格或等号，但前后不是下划线或数字
    pattern = r'\b(IAB)(\d{2})(?=\s*=)'

    def replacer(match):
        return f'IAB_CAT_{match.group(2)}'

    fixed_content = re.sub(pattern, replacer, content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"Fixed proto file saved to: {output_file}")

if __name__ == '__main__':
    fix_proto_enums(
        'proto_files/努比亚/努比亚.proto',
        'proto_files/努比亚/努比亚.proto'
    )
