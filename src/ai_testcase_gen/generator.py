"""
测试用例生成器：核心业务逻辑
"""
import logging
import os
from typing import Dict, List, Optional, Callable
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
    from .test_conventions import find_relevant_conventions, format_conventions_for_prompt
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
    from test_conventions import find_relevant_conventions, format_conventions_for_prompt

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
        enable_question_generation: bool = True,
        enable_image_analysis: bool = True,
        max_images: int = 10
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

            # Step 1.5: 分析文档图片 (如果启用)
            if enable_image_analysis and parsed_doc.get('images'):
                image_count = len(parsed_doc['images'])
                logger.info(f"发现 {image_count} 张图片，开始分析...")
                self._report_progress(f"正在分析文档图片 (共{image_count}张)...", 25)

                image_descriptions = self._analyze_images(parsed_doc['images'], max_images)

                # 将图片描述整合到文档文本中
                if image_descriptions:
                    parsed_doc['raw_text'] += "\n\n=== 文档中的图片内容 ===\n"
                    for desc in image_descriptions:
                        parsed_doc['raw_text'] += f"\n[图片{desc['index']+1}] 位置:{desc['position']}\n{desc['description']}\n"
                    logger.info(f"成功分析 {len(image_descriptions)} 张图片")

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
        """使用AI提取测试用例（两阶段分批生成）"""
        try:
            # 第一阶段：识别功能模块
            logger.info("【第1阶段】识别功能模块...")
            try:
                from .prompts import MODULE_IDENTIFICATION_PROMPT, SINGLE_MODULE_TESTCASE_PROMPT
            except ImportError:
                from prompts import MODULE_IDENTIFICATION_PROMPT, SINGLE_MODULE_TESTCASE_PROMPT

            module_prompt = MODULE_IDENTIFICATION_PROMPT.format(
                title=parsed_doc['title'],
                content=parsed_doc['raw_text'][:8000]  # 限制输入长度
            )

            module_result = self.ai_service.generate_json(module_prompt, max_tokens=4000)
            identified_modules = module_result.get('modules', [])
            logger.info(f"识别到 {len(identified_modules)} 个功能模块")

            if not identified_modules:
                logger.warning("未识别到任何功能模块，返回空结构")
                return {'modules': [], 'questions': [], 'defects': []}

            # 第二阶段：并发生成每个模块的测试用例
            logger.info("【第2阶段】为每个模块生成测试用例(并发处理)...")

            all_modules = self._generate_modules_concurrent(
                identified_modules,
                parsed_doc['raw_text'],
                SINGLE_MODULE_TESTCASE_PROMPT
            )

            logger.info(f"测试用例生成完成,共 {len(all_modules)} 个模块")

            return {
                'modules': all_modules,
                'questions': [],
                'defects': []
            }

        except Exception as e:
            logger.error(f"测试用例提取失败: {e}", exc_info=True)
            return {
                'modules': [],
                'questions': [],
                'defects': []
            }

    def _generate_modules_concurrent(self, identified_modules: list, full_text: str, prompt_template: str) -> list:
        """并发生成多个模块的测试用例"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        all_modules = []
        total_modules = len(identified_modules)

        # Phase 2: 5个并发worker (优化到2分钟目标)
        max_workers = 5
        logger.info(f"使用 {max_workers} 个并发worker处理 {total_modules} 个模块")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_module = {}
            for idx, module_info in enumerate(identified_modules, 1):
                module_name = module_info.get('module_name', f'模块{idx}')
                future = executor.submit(
                    self._generate_single_module,
                    module_info,
                    full_text,
                    prompt_template,
                    idx,
                    total_modules
                )
                future_to_module[future] = (module_name, idx)

            # 收集结果
            completed_count = 0
            for future in as_completed(future_to_module):
                module_name, idx = future_to_module[future]
                completed_count += 1

                try:
                    result = future.result(timeout=120)  # 2分钟超时
                    if result:
                        all_modules.append(result)
                        logger.info(f"  ✓ [{completed_count}/{total_modules}] {module_name} 完成")
                    else:
                        logger.warning(f"  ✗ [{completed_count}/{total_modules}] {module_name} 返回空结果")
                except TimeoutError:
                    logger.error(f"  ✗ [{completed_count}/{total_modules}] {module_name} 超时(>120秒)")
                except Exception as e:
                    logger.error(f"  ✗ [{completed_count}/{total_modules}] {module_name} 失败: {e}")

        return all_modules

    def _generate_single_module(self, module_info: dict, full_text: str, prompt_template: str, idx: int, total: int) -> dict:
        """生成单个模块的测试用例"""
        module_name = module_info.get('module_name', f'模块{idx}')

        try:
            # 提取相关内容
            keywords = module_info.get('related_keywords', [module_name])
            related_content = self._extract_related_content(full_text, keywords)

            # 构建prompt
            single_module_prompt = prompt_template.format(
                module_name=module_name,
                module_description=module_info.get('description', ''),
                related_content=related_content[:4000]
            )

            # 调用AI生成
            module_testcases = self.ai_service.generate_json(
                single_module_prompt,
                max_tokens=16000
            )

            # 验证结果
            if isinstance(module_testcases, dict) and 'module_name' in module_testcases:
                case_count = sum(
                    len(sc.get('test_cases', []))
                    for tt in module_testcases.get('test_types', [])
                    for sc in tt.get('scenarios', [])
                )
                logger.info(f"    [{idx}/{total}] {module_name}: 生成 {case_count} 个用例")
                return module_testcases
            else:
                logger.warning(f"    [{idx}/{total}] {module_name}: JSON格式不正确")
                return None

        except Exception as e:
            logger.error(f"    [{idx}/{total}] {module_name} 生成异常: {e}")
            return None

    def _extract_related_content(self, full_text: str, keywords: list) -> str:
        """从完整文档中提取与关键词相关的内容"""
        if not keywords:
            return full_text[:4000]

        # 简单实现：查找包含关键词的段落
        paragraphs = full_text.split('\n')
        related_paragraphs = []

        for para in paragraphs:
            for keyword in keywords:
                if keyword in para:
                    related_paragraphs.append(para)
                    break

        related_text = '\n'.join(related_paragraphs)

        # 如果提取的内容太少，补充原文
        if len(related_text) < 500:
            related_text = full_text[:4000]

        return related_text

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

    def _analyze_images(self, images: List[Dict], max_images: int = 10) -> List[Dict]:
        """
        批量分析图片内容

        Args:
            images: 图片列表
            max_images: 最多分析的图片数量

        Returns:
            图片描述列表
        """
        descriptions = []

        # 图片分析提示词
        prompt = """请详细描述这张图片的内容,重点关注:

1. **如果是流程图、架构图**: 描述流程步骤、组件关系、数据流向
2. **如果是UI界面**: 描述界面元素、按钮功能、输入字段、交互逻辑
3. **如果是数据表格**: 描述表格结构、字段含义、数据关系
4. **如果是UML图**: 描述类关系、序列流程、状态转换
5. **如果是原型图**: 描述页面布局、功能区域、用户操作路径

请用**软件测试人员的视角**,关注可测试的功能点、边界条件和异常场景。
输出应简洁明了,重点突出测试相关信息。"""

        # 限制图片数量
        images_to_analyze = images[:max_images]

        for img in images_to_analyze:
            try:
                self._report_progress(
                    f"正在分析图片 #{img['index']+1}/{len(images_to_analyze)}...",
                    25 + int((img['index'] + 1) / len(images_to_analyze) * 5)
                )

                description = self.ai_service.analyze_image(
                    image_data=img['data'],
                    prompt=prompt,
                    media_type=img.get('media_type', 'image/jpeg')
                )

                descriptions.append({
                    'index': img['index'],
                    'position': img['position'],
                    'description': description
                })

                logger.info(f"图片#{img['index']+1}分析完成: {description[:100]}...")

            except Exception as e:
                logger.warning(f"图片#{img['index']+1}分析失败: {e}")
                # 继续处理下一张图片

        if len(images) > max_images:
            logger.info(f"图片总数({len(images)})超过限制({max_images}),已跳过 {len(images) - max_images} 张")

        return descriptions


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
