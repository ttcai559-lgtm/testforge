"""
测试用例生成器：核心业务逻辑
"""
import logging
import os
from typing import Dict, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .document_parser import DocumentParser
    from .ai_service import AIServiceFactory, AIServiceBase
    from .xmind_builder import XMindBuilder
    from .prompts import (
        MAIN_EXTRACTION_PROMPT,
        DEFECT_DETECTION_PROMPT,
        QUESTION_GENERATION_PROMPT
    )
    from .config import DEFAULT_AI_MODEL, OUTPUT_DIR
except ImportError:
    # 直接运行时的导入
    from document_parser import DocumentParser
    from ai_service import AIServiceFactory, AIServiceBase
    from xmind_builder import XMindBuilder
    from prompts import (
        MAIN_EXTRACTION_PROMPT,
        DEFECT_DETECTION_PROMPT,
        QUESTION_GENERATION_PROMPT
    )
    from config import DEFAULT_AI_MODEL, OUTPUT_DIR

logger = logging.getLogger(__name__)


class TestCaseGenerator:
    """测试用例生成器"""

    def __init__(
        self,
        ai_model: str = DEFAULT_AI_MODEL,
        ai_service: Optional[AIServiceBase] = None
    ):
        """
        初始化生成器

        Args:
            ai_model: AI模型类型（openai/claude/wenxin/qianwen）
            ai_service: 自定义AI服务实例（可选）
        """
        self.document_parser = DocumentParser()
        self.xmind_builder = XMindBuilder()

        # 初始化AI服务
        if ai_service:
            self.ai_service = ai_service
        else:
            self.ai_service = AIServiceFactory.create(ai_model)

        # 进度回调函数
        self.progress_callback: Optional[Callable[[str, int], None]] = None

        logger.info(f"测试用例生成器初始化完成，使用模型：{ai_model}")

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """设置进度回调函数

        Args:
            callback: 回调函数，接收(message: str, percent: int)参数
        """
        self.progress_callback = callback

    def _report_progress(self, message: str, percent: int):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, percent)
        logger.info(f"[{percent}%] {message}")

    def generate(
        self,
        document_path: str,
        output_filename: Optional[str] = None,
        enable_defect_detection: bool = True,
        enable_question_generation: bool = True
    ) -> Dict:
        """
        从需求文档生成测试用例XMind文件

        Args:
            document_path: 需求文档路径（Word或PDF）
            output_filename: 输出文件名（不指定则自动生成）
            enable_defect_detection: 是否启用需求缺陷检测
            enable_question_generation: 是否启用问题清单生成

        Returns:
            生成结果字典：
            {
                'success': True/False,
                'xmind_path': 'XMind文件路径',
                'test_data': {...},  # AI提取的结构化数据
                'statistics': {
                    'total_cases': 100,
                    'green_cases': 70,
                    'yellow_cases': 20,
                    'red_cases': 10,
                    'questions_count': 15,
                    'defects_count': 5
                },
                'error': '错误信息（如果失败）'
            }
        """
        try:
            logger.info(f"开始处理文档：{document_path}")

            # Step 1: 解析文档
            self._report_progress("正在解析文档...", 10)
            logger.info("Step 1: 解析文档...")
            parsed_doc = self.document_parser.parse(document_path)
            logger.info(f"文档解析完成，标题：{parsed_doc['title']}")
            self._report_progress(f"文档解析完成：{parsed_doc['title']}", 20)

            # Step 2-4: 并行执行AI任务
            self._report_progress("正在并行调用AI分析...", 30)
            logger.info("Step 2-4: 并行执行AI分析任务...")

            test_data = {}
            defects = []
            questions = []

            # 使用线程池并行执行AI调用
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 提交所有AI任务
                future_test_cases = executor.submit(self._extract_test_cases, parsed_doc)
                future_defects = executor.submit(self._detect_defects, parsed_doc) if enable_defect_detection else None
                future_questions = executor.submit(self._generate_questions, parsed_doc) if enable_question_generation else None

                # 收集结果并报告进度
                completed_tasks = 0
                total_tasks = 1 + (1 if enable_defect_detection else 0) + (1 if enable_question_generation else 0)

                for future in as_completed([f for f in [future_test_cases, future_defects, future_questions] if f is not None]):
                    completed_tasks += 1
                    progress = 30 + int(completed_tasks / total_tasks * 50)

                    if future == future_test_cases:
                        test_data = future.result()
                        self._report_progress(f"测试用例提取完成 ({completed_tasks}/{total_tasks})", progress)
                    elif future == future_defects:
                        defects = future.result()
                        self._report_progress(f"需求缺陷检测完成 ({completed_tasks}/{total_tasks})", progress)
                    elif future == future_questions:
                        questions = future.result()
                        self._report_progress(f"问题清单生成完成 ({completed_tasks}/{total_tasks})", progress)

            # 合并结果
            test_data['defects'] = defects
            test_data['questions'] = questions

            logger.info("AI分析任务全部完成")
            self._report_progress("AI分析完成，正在生成XMind文件...", 80)

            # Step 5: 生成XMind文件
            logger.info("Step 5: 生成XMind文件...")
            xmind_path = self._generate_xmind(
                test_data,
                parsed_doc['title'],
                output_filename
            )
            self._report_progress("XMind文件生成完成", 90)

            # Step 6: 统计数据
            statistics = self._calculate_statistics(test_data)
            self._report_progress("统计数据计算完成", 95)

            logger.info("测试用例生成完成！")
            self._report_progress("全部完成！", 100)

            return {
                'success': True,
                'xmind_path': xmind_path,
                'test_data': test_data,
                'statistics': statistics,
                'document_title': parsed_doc['title']
            }

        except Exception as e:
            logger.error(f"生成测试用例失败: {e}", exc_info=True)
            self._report_progress(f"生成失败: {str(e)}", 0)
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_test_cases(self, parsed_doc: Dict) -> Dict:
        """使用AI提取测试用例"""
        # 构建prompt
        prompt = MAIN_EXTRACTION_PROMPT.format(
            title=parsed_doc['title'],
            content=parsed_doc['raw_text']
        )

        # 调用AI
        logger.info("调用AI模型提取测试用例...")
        try:
            result = self.ai_service.generate_json(prompt)
            logger.info(f"AI提取完成，生成了 {len(result.get('modules', []))} 个模块")
            return result
        except Exception as e:
            logger.error(f"AI提取失败: {e}")
            # 返回空结构
            return {
                'modules': [],
                'questions': [],
                'defects': []
            }

    def _detect_defects(self, parsed_doc: Dict) -> list:
        """检测需求缺陷"""
        prompt = DEFECT_DETECTION_PROMPT.format(
            content=parsed_doc['raw_text']
        )

        try:
            result = self.ai_service.generate_json(prompt)
            defects = result.get('defects', [])
            logger.info(f"检测到 {len(defects)} 个需求缺陷")
            return defects
        except Exception as e:
            logger.error(f"缺陷检测失败: {e}")
            return []

    def _generate_questions(self, parsed_doc: Dict) -> list:
        """生成问题清单"""
        prompt = QUESTION_GENERATION_PROMPT.format(
            content=parsed_doc['raw_text']
        )

        try:
            result = self.ai_service.generate_json(prompt)
            questions = result.get('questions', [])
            logger.info(f"生成了 {len(questions)} 个待澄清问题")
            return questions
        except Exception as e:
            logger.error(f"问题清单生成失败: {e}")
            return []

    def _generate_xmind(
        self,
        test_data: Dict,
        document_title: str,
        output_filename: Optional[str]
    ) -> str:
        """生成XMind文件"""
        # 生成输出文件名
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"测试用例_{document_title}_{timestamp}.xmind"

        # 确保文件名以.xmind结尾
        if not output_filename.endswith('.xmind'):
            output_filename += '.xmind'

        # 生成完整路径
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # 构建XMind
        xmind_title = f"{document_title} - 测试用例"
        self.xmind_builder.build(test_data, output_path, xmind_title)

        return output_path

    def _calculate_statistics(self, test_data: Dict) -> Dict:
        """计算统计数据"""
        stats = {
            'total_cases': 0,
            'green_cases': 0,   # 高置信度
            'yellow_cases': 0,  # 中置信度
            'red_cases': 0,     # 低置信度
            'questions_count': len(test_data.get('questions', [])),
            'defects_count': len(test_data.get('defects', [])),
            'modules_count': len(test_data.get('modules', []))
        }

        # 统计测试用例
        for module in test_data.get('modules', []):
            for test_type in module.get('test_types', []):
                for scenario in test_type.get('scenarios', []):
                    for case in scenario.get('test_cases', []):
                        stats['total_cases'] += 1

                        confidence = case.get('confidence', 'medium')
                        if confidence == 'high':
                            stats['green_cases'] += 1
                        elif confidence == 'medium':
                            stats['yellow_cases'] += 1
                        elif confidence == 'low':
                            stats['red_cases'] += 1

        # 计算百分比
        if stats['total_cases'] > 0:
            stats['green_percentage'] = round(stats['green_cases'] / stats['total_cases'] * 100, 1)
            stats['yellow_percentage'] = round(stats['yellow_cases'] / stats['total_cases'] * 100, 1)
            stats['red_percentage'] = round(stats['red_cases'] / stats['total_cases'] * 100, 1)
        else:
            stats['green_percentage'] = 0
            stats['yellow_percentage'] = 0
            stats['red_percentage'] = 0

        return stats


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建生成器
    generator = TestCaseGenerator(ai_model="openai")

    # 生成测试用例
    # result = generator.generate("需求文档.docx")

    # if result['success']:
    #     print(f"✅ 生成成功！")
    #     print(f"XMind文件：{result['xmind_path']}")
    #     print(f"统计数据：{result['statistics']}")
    # else:
    #     print(f"❌ 生成失败：{result['error']}")
