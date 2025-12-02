"""
XMind文件生成器
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class XMindBuilder:
    """XMind思维导图构建器"""

    def __init__(self):
        try:
            import xmind
            self.xmind = xmind
        except ImportError:
            raise ImportError("请安装 xmind: pip install xmind")

        try:
            from .config import XMIND_COLORS
        except ImportError:
            from config import XMIND_COLORS
        self.colors = XMIND_COLORS

    def build(self, test_data: Dict, output_path: str, title: str = "测试用例") -> str:
        """
        构建XMind文件

        Args:
            test_data: 测试数据（从AI提取的结构化数据）
            output_path: 输出路径
            title: 思维导图标题

        Returns:
            生成的XMind文件路径
        """
        # 创建工作簿（直接使用输出路径，如果不存在会自动创建新的）
        workbook = self.xmind.load(output_path)
        sheet = workbook.getPrimarySheet()

        # 设置根节点
        root_topic = sheet.getRootTopic()
        root_topic.setTitle(title)

        # 构建模块节点
        modules = test_data.get("modules", [])
        for module in modules:
            self._add_module(root_topic, module)

        # 添加问题清单（作为独立的一级节点）
        questions = test_data.get("questions", [])
        if questions:
            self._add_questions_node(root_topic, questions)

        # 添加需求缺陷（作为独立的一级节点）
        defects = test_data.get("defects", [])
        if defects:
            self._add_defects_node(root_topic, defects)

        # 保存文件
        self.xmind.save(workbook, output_path)
        logger.info(f"XMind文件已生成: {output_path}")

        # 修复XMind文件（添加缺失的meta.xml和manifest.xml）
        self._fix_xmind_file(output_path)

        return output_path

    def _get_template_path(self) -> Optional[str]:
        """获取模板路径（如果有的话）"""
        # 如果有预定义模板，可以在这里返回路径
        # 否则返回None，使用空白模板
        return None

    def _add_module(self, parent_topic, module: Dict):
        """添加功能模块节点"""
        # 创建模块节点
        module_topic = parent_topic.addSubTopic()
        module_topic.setTitle(module.get("module_name", "未命名模块"))

        # 添加模块描述（作为备注）
        description = module.get("description")
        if description:
            module_topic.setPlainNotes(description)

        # 添加测试类型
        test_types = module.get("test_types", [])
        for test_type in test_types:
            self._add_test_type(module_topic, test_type)

    def _add_test_type(self, parent_topic, test_type: Dict):
        """添加测试类型节点"""
        type_topic = parent_topic.addSubTopic()
        type_topic.setTitle(test_type.get("type_name", "功能测试"))

        # 添加测试场景
        scenarios = test_type.get("scenarios", [])
        for scenario in scenarios:
            self._add_scenario(type_topic, scenario)

    def _add_scenario(self, parent_topic, scenario: Dict):
        """添加测试场景节点"""
        scenario_topic = parent_topic.addSubTopic()
        scenario_topic.setTitle(scenario.get("scenario_name", "正常场景"))

        # 添加测试用例
        test_cases = scenario.get("test_cases", [])
        for test_case in test_cases:
            self._add_test_case(scenario_topic, test_case)

    def _add_test_case(self, parent_topic, test_case: Dict):
        """添加测试用例节点 - 新版：支持 clear/assumed/clarify_needed"""
        case_topic = parent_topic.addSubTopic()

        # 获取置信度（兼容旧版和新版）
        confidence = test_case.get("confidence", "medium")

        # 兼容旧版本的 confidence 值
        confidence_map = {
            "high": "clear",
            "medium": "assumed",
            "low": "clarify_needed"
        }
        confidence = confidence_map.get(confidence, confidence)

        # 设置标题
        title = test_case.get("title", "未命名用例")

        # 新的置信度标记系统
        if confidence == "clear":
            # 绿色 - 需求明确
            icon = "✅"
            label = "需求明确"
        elif confidence == "assumed":
            # 蓝色 - 基于假设
            icon = "💡"
            label = "基于假设"
        elif confidence == "clarify_needed":
            # 黄色 - 需要澄清
            icon = "❓"
            label = "建议澄清"
        else:
            # 默认
            icon = "📝"
            label = "待确认"

        case_topic.setTitle(f"{icon} {title}")

        # 添加详细信息作为备注
        notes = self._build_case_notes_v2(test_case, confidence)
        if notes:
            case_topic.setPlainNotes(notes)

        # 添加标签
        case_topic.addLabel(label)

        # 如果有假设，添加假设节点（支持字符串或数组）
        assumptions = test_case.get("assumptions", [])
        if assumptions and confidence == "assumed":
            assumptions_topic = case_topic.addSubTopic()
            assumptions_topic.setTitle("📌 测试假设")
            if isinstance(assumptions, str):
                # 字符串格式，按分号分隔
                for assumption in assumptions.split(';'):
                    assumption = assumption.strip()
                    if assumption:
                        assumption_item = assumptions_topic.addSubTopic()
                        assumption_item.setTitle(f"▸ {assumption}")
            else:
                # 数组格式
                for assumption in assumptions:
                    assumption_item = assumptions_topic.addSubTopic()
                    assumption_item.setTitle(f"▸ {assumption}")

        # 如果需要澄清，添加缺失信息节点（支持字符串或数组）
        missing_info = test_case.get("missing_info", [])
        if missing_info and confidence == "clarify_needed":
            missing_topic = case_topic.addSubTopic()
            missing_topic.setTitle("❗ 需要澄清")
            if isinstance(missing_info, str):
                # 字符串格式，按分号分隔
                for info in missing_info.split(';'):
                    info = info.strip()
                    if info:
                        info_item = missing_topic.addSubTopic()
                        info_item.setTitle(f"? {info}")
            else:
                # 数组格式
                for info in missing_info:
                    info_item = missing_topic.addSubTopic()
                    info_item.setTitle(f"? {info}")

    def _get_color_by_confidence(self, confidence: str) -> Optional[str]:
        """根据置信度获取颜色"""
        color_map = {
            "high": self.colors.get("green"),
            "medium": self.colors.get("yellow"),
            "low": self.colors.get("red")
        }
        return color_map.get(confidence)

    def _build_case_notes(self, test_case: Dict) -> str:
        """构建测试用例备注信息（旧版，保留兼容性）"""
        notes_parts = []

        # 描述
        description = test_case.get("description")
        if description:
            notes_parts.append(f"描述：{description}")

        # 前置条件
        preconditions = test_case.get("preconditions")
        if preconditions:
            notes_parts.append(f"\n前置条件：{preconditions}")

        # 测试步骤（支持字符串或数组）
        test_steps = test_case.get("test_steps", [])
        if test_steps:
            if isinstance(test_steps, str):
                notes_parts.append(f"\n测试步骤：{test_steps}")
            else:
                steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(test_steps)])
                notes_parts.append(f"\n测试步骤：\n{steps_text}")

        # 预期结果
        expected_result = test_case.get("expected_result")
        if expected_result:
            notes_parts.append(f"\n预期结果：{expected_result}")

        # 置信度说明
        confidence_reason = test_case.get("confidence_reason")
        if confidence_reason:
            notes_parts.append(f"\n置信度说明：{confidence_reason}")

        return "\n".join(notes_parts)

    def _build_case_notes_v2(self, test_case: Dict, confidence: str) -> str:
        """构建测试用例备注信息（新版，支持假设和缺失信息）"""
        notes_parts = []

        # 描述
        description = test_case.get("description")
        if description:
            notes_parts.append(f"📝 描述：{description}")

        # 前置条件
        preconditions = test_case.get("preconditions")
        if preconditions:
            notes_parts.append(f"\n🔧 前置条件：{preconditions}")

        # 测试步骤（支持字符串或数组）
        test_steps = test_case.get("test_steps", [])
        if test_steps:
            if isinstance(test_steps, str):
                notes_parts.append(f"\n👣 测试步骤：{test_steps}")
            else:
                steps_text = "\n".join([f"  {i+1}. {step}" for i, step in enumerate(test_steps)])
                notes_parts.append(f"\n👣 测试步骤：\n{steps_text}")

        # 预期结果
        expected_result = test_case.get("expected_result")
        if expected_result:
            notes_parts.append(f"\n✔️ 预期结果：{expected_result}")

        # 置信度说明
        confidence_reason = test_case.get("confidence_reason")
        if confidence_reason:
            notes_parts.append(f"\n💭 置信度说明：{confidence_reason}")

        # 如果基于假设，显示假设内容（支持字符串或数组）
        if confidence == "assumed":
            assumptions = test_case.get("assumptions", [])
            if assumptions:
                if isinstance(assumptions, str):
                    notes_parts.append(f"\n💡 测试假设：{assumptions}")
                else:
                    assumptions_text = "\n".join([f"  ▸ {a}" for a in assumptions])
                    notes_parts.append(f"\n💡 测试假设：\n{assumptions_text}")

        # 如果需要澄清，显示缺失信息（支持字符串或数组）
        if confidence == "clarify_needed":
            missing_info = test_case.get("missing_info", [])
            if missing_info:
                if isinstance(missing_info, str):
                    notes_parts.append(f"\n❓ 需要澄清：{missing_info}")
                else:
                    missing_text = "\n".join([f"  ? {m}" for m in missing_info])
                    notes_parts.append(f"\n❓ 需要澄清：\n{missing_text}")

        # 参考的行业惯例
        reference_practice = test_case.get("reference_practice")
        if reference_practice:
            notes_parts.append(f"\n📚 参考惯例：{reference_practice}")

        return "\n".join(notes_parts)

    def _add_questions_node(self, parent_topic, questions: List[Dict]):
        """添加问题清单节点"""
        questions_topic = parent_topic.addSubTopic()
        questions_topic.setTitle("🤔 问题清单（需澄清）")

        # 按优先级分组
        high_priority = [q for q in questions if q.get("priority") == "high"]
        medium_priority = [q for q in questions if q.get("priority") == "medium"]
        low_priority = [q for q in questions if q.get("priority") == "low"]

        # 添加高优先级问题
        if high_priority:
            high_topic = questions_topic.addSubTopic()
            high_topic.setTitle("🔴 高优先级（阻塞性）")
            for q in high_priority:
                self._add_question_item(high_topic, q)

        # 添加中优先级问题
        if medium_priority:
            medium_topic = questions_topic.addSubTopic()
            medium_topic.setTitle("🟡 中优先级（重要）")
            for q in medium_priority:
                self._add_question_item(medium_topic, q)

        # 添加低优先级问题
        if low_priority:
            low_topic = questions_topic.addSubTopic()
            low_topic.setTitle("🟢 低优先级（优化）")
            for q in low_priority:
                self._add_question_item(low_topic, q)

    def _add_question_item(self, parent_topic, question: Dict):
        """添加单个问题项"""
        q_topic = parent_topic.addSubTopic()
        q_topic.setTitle(question.get("question", ""))

        # 添加详细信息
        notes = []
        location = question.get("location")
        if location:
            notes.append(f"位置：{location}")

        reason = question.get("reason")
        if reason:
            notes.append(f"原因：{reason}")

        if notes:
            q_topic.setPlainNotes("\n".join(notes))

    def _add_defects_node(self, parent_topic, defects: List[Dict]):
        """添加需求缺陷节点"""
        defects_topic = parent_topic.addSubTopic()
        defects_topic.setTitle("🐛 需求缺陷")

        # 按严重程度分组
        high_severity = [d for d in defects if d.get("severity") == "high"]
        medium_severity = [d for d in defects if d.get("severity") == "medium"]
        low_severity = [d for d in defects if d.get("severity") == "low"]

        # 添加高严重度缺陷
        if high_severity:
            high_topic = defects_topic.addSubTopic()
            high_topic.setTitle("🔴 高严重度")
            for d in high_severity:
                self._add_defect_item(high_topic, d)

        # 添加中严重度缺陷
        if medium_severity:
            medium_topic = defects_topic.addSubTopic()
            medium_topic.setTitle("🟡 中严重度")
            for d in medium_severity:
                self._add_defect_item(medium_topic, d)

        # 添加低严重度缺陷
        if low_severity:
            low_topic = defects_topic.addSubTopic()
            low_topic.setTitle("🟢 低严重度")
            for d in low_severity:
                self._add_defect_item(low_topic, d)

    def _add_defect_item(self, parent_topic, defect: Dict):
        """添加单个缺陷项"""
        d_topic = parent_topic.addSubTopic()

        defect_type = defect.get("defect_type", "")
        description = defect.get("description", "")
        d_topic.setTitle(f"[{defect_type}] {description}")

        # 添加详细信息
        notes = []
        location = defect.get("location")
        if location:
            notes.append(f"位置：{location}")

        suggestion = defect.get("suggestion")
        if suggestion:
            notes.append(f"修改建议：{suggestion}")

        if notes:
            d_topic.setPlainNotes("\n".join(notes))

    def _fix_xmind_file(self, xmind_path: str):
        """
        修复XMind文件，添加缺失的meta.xml和manifest.xml

        Args:
            xmind_path: XMind文件路径
        """
        import zipfile
        import re

        # 读取现有文件
        with zipfile.ZipFile(xmind_path, 'r') as zin:
            existing_files = zin.namelist()

            # 检查是否需要修复
            if 'meta.xml' in existing_files and 'META-INF/manifest.xml' in existing_files:
                return  # 文件完整，无需修复

            # 读取content.xml
            content_xml = zin.read('content.xml').decode('utf-8')

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
                    from datetime import datetime
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
        logger.debug(f"XMind文件已修复: {xmind_path}")


# 使用示例
if __name__ == "__main__":
    builder = XMindBuilder()

    # 测试数据
    test_data = {
        "modules": [
            {
                "module_name": "用户登录",
                "description": "用户登录功能模块",
                "test_types": [
                    {
                        "type_name": "功能测试",
                        "scenarios": [
                            {
                                "scenario_name": "正常场景",
                                "test_cases": [
                                    {
                                        "title": "正确用户名密码登录成功",
                                        "description": "验证使用正确的用户名和密码能够成功登录",
                                        "confidence": "high",
                                        "test_steps": ["打开登录页面", "输入正确用户名", "输入正确密码", "点击登录"],
                                        "expected_result": "登录成功，跳转到首页"
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
                "location": "第2章 登录功能",
                "question": "密码最大长度是多少？",
                "priority": "high",
                "reason": "需求未明确说明"
            }
        ],
        "defects": [
            {
                "location": "第2.3节",
                "defect_type": "矛盾",
                "description": "登录失败次数限制前后不一致",
                "severity": "high",
                "suggestion": "统一为5次"
            }
        ]
    }

    # 生成XMind
    # builder.build(test_data, "test_output.xmind", "测试用例思维导图")
