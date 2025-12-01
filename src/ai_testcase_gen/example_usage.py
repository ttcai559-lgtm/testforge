"""
使用示例：演示如何使用AI测试用例生成器
"""
import logging
import os
from generator import TestCaseGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_basic_usage():
    """示例1：基础使用"""
    print("\n" + "="*60)
    print("示例1：基础使用")
    print("="*60)

    # 创建生成器（使用OpenAI）
    generator = TestCaseGenerator(ai_model="openai")

    # 生成测试用例
    # 注意：需要替换为实际的文档路径
    document_path = "path/to/your/requirement.docx"

    if not os.path.exists(document_path):
        print(f"⚠️ 文档不存在：{document_path}")
        print("请替换为实际的需求文档路径")
        return

    result = generator.generate(
        document_path=document_path,
        enable_defect_detection=True,
        enable_question_generation=True
    )

    if result['success']:
        print(f"\n✅ 生成成功！")
        print(f"XMind文件：{result['xmind_path']}")
        print(f"\n统计数据：")
        for key, value in result['statistics'].items():
            print(f"  {key}: {value}")
    else:
        print(f"\n❌ 生成失败：{result['error']}")


def example_2_custom_config():
    """示例2：自定义配置"""
    print("\n" + "="*60)
    print("示例2：自定义配置")
    print("="*60)

    from ai_service import OpenAIService

    # 自定义AI服务（使用代理或自定义模型）
    custom_service = OpenAIService(
        api_key="your-api-key",
        model="gpt-4-turbo",
        base_url="https://your-proxy.com/v1"  # 可选
    )

    # 使用自定义服务创建生成器
    generator = TestCaseGenerator(ai_service=custom_service)

    # 禁用缺陷检测和问题清单（加快速度）
    result = generator.generate(
        document_path="path/to/doc.pdf",
        output_filename="my_testcases.xmind",
        enable_defect_detection=False,
        enable_question_generation=False
    )

    print(f"结果：{result}")


def example_3_batch_processing():
    """示例3：批量处理多个文档"""
    print("\n" + "="*60)
    print("示例3：批量处理多个文档")
    print("="*60)

    generator = TestCaseGenerator(ai_model="openai")

    # 需求文档列表
    documents = [
        "需求文档1.docx",
        "需求文档2.pdf",
        "需求文档3.docx"
    ]

    results = []
    for doc in documents:
        if not os.path.exists(doc):
            print(f"⚠️ 跳过不存在的文档：{doc}")
            continue

        print(f"\n处理：{doc}")
        result = generator.generate(doc)

        if result['success']:
            print(f"  ✅ 成功 - {result['statistics']['total_cases']} 个用例")
            results.append(result)
        else:
            print(f"  ❌ 失败 - {result['error']}")

    # 汇总统计
    if results:
        total_cases = sum(r['statistics']['total_cases'] for r in results)
        print(f"\n汇总：共生成 {total_cases} 个测试用例")


def example_4_parse_document_only():
    """示例4：仅解析文档（不调用AI）"""
    print("\n" + "="*60)
    print("示例4：仅解析文档")
    print("="*60)

    from document_parser import DocumentParser

    parser = DocumentParser()

    document_path = "path/to/doc.docx"

    if not os.path.exists(document_path):
        print(f"⚠️ 文档不存在：{document_path}")
        return

    # 解析文档
    parsed = parser.parse(document_path)

    print(f"文档标题：{parsed['title']}")
    print(f"章节数量：{parsed['metadata']['section_count']}")
    print(f"\n章节结构：")
    for section in parsed['sections']:
        print(f"  - {section['heading']} (Level {section['level']})")


def example_5_build_xmind_from_json():
    """示例5：从JSON数据构建XMind"""
    print("\n" + "="*60)
    print("示例5：从JSON数据构建XMind")
    print("="*60)

    from xmind_builder import XMindBuilder

    builder = XMindBuilder()

    # 手动构建的测试数据
    test_data = {
        "modules": [
            {
                "module_name": "用户注册",
                "description": "用户注册功能",
                "test_types": [
                    {
                        "type_name": "功能测试",
                        "scenarios": [
                            {
                                "scenario_name": "正常场景",
                                "test_cases": [
                                    {
                                        "title": "新用户注册成功",
                                        "description": "验证新用户能够成功注册",
                                        "confidence": "high",
                                        "test_steps": [
                                            "打开注册页面",
                                            "输入用户名、邮箱、密码",
                                            "点击注册"
                                        ],
                                        "expected_result": "注册成功，收到验证邮件"
                                    }
                                ]
                            },
                            {
                                "scenario_name": "异常场景",
                                "test_cases": [
                                    {
                                        "title": "用户名已存在注册失败",
                                        "description": "验证用户名重复时无法注册",
                                        "confidence": "medium",
                                        "expected_result": "提示用户名已存在"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        "questions": [
            {
                "location": "注册功能",
                "question": "密码强度要求是什么？",
                "priority": "high",
                "reason": "需求未明确说明"
            }
        ],
        "defects": []
    }

    # 构建XMind
    output_path = builder.build(
        test_data,
        "example_output.xmind",
        "用户注册测试用例"
    )

    print(f"✅ XMind文件已生成：{output_path}")


# 主函数
if __name__ == "__main__":
    print("\n" + "="*60)
    print("AI测试用例生成器 - 使用示例")
    print("="*60)

    # 运行示例
    # example_1_basic_usage()
    # example_2_custom_config()
    # example_3_batch_processing()
    # example_4_parse_document_only()
    example_5_build_xmind_from_json()

    print("\n" + "="*60)
    print("示例运行完成")
    print("="*60)
