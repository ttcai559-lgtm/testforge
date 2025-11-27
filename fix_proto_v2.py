#!/usr/bin/env python3
"""
彻底修复proto枚举冲突 - 为所有子类别添加父类前缀
IAB21_1 -> IAB_21_SUB_1
IAB2_11 -> IAB_2_SUB_11
"""
import re

def fix_enums_thoroughly(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    for line in lines:
        # 匹配 IAB + 数字 + _ + 数字 的模式
        # IAB21_1 = 197; -> IAB_21_SUB_1 = 197;
        new_line = re.sub(
            r'\b(IAB)(\d+)_(\d+)(?=\s*=)',
            r'IAB_\2_SUB_\3',
            line
        )
        fixed_lines.append(new_line)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    print(f"Fixed proto file saved")

if __name__ == '__main__':
    fix_enums_thoroughly(
        'proto_files/努比亚/努比亚.proto.bak',
        'proto_files/努比亚/努比亚_fixed.proto'
    )
