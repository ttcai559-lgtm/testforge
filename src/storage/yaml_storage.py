"""
YAML格式用例存储

用例保存为YAML文件，易于版本管理和人工编辑
"""

import yaml
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class YAMLStorage:
    """YAML格式的用例存储"""

    def __init__(self, storage_dir: str = "./testcases"):
        """
        初始化存储

        Args:
            storage_dir: 用例存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_testcase(self, testcase: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        保存测试用例

        Args:
            testcase: 测试用例字典
            filename: 文件名（可选，不指定则自动生成）

        Returns:
            str: 保存的文件路径
        """
        # 添加元数据
        testcase["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }

        # 生成文件名
        if filename is None:
            name = testcase.get("name", "testcase")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.yaml"

        # 确保文件名以.yaml结尾
        if not filename.endswith((".yaml", ".yml")):
            filename += ".yaml"

        filepath = self.storage_dir / filename

        # 保存为YAML
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(testcase, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # 只返回文件名,不包含路径
        return filename

    def load_testcase(self, filename: str) -> Dict[str, Any]:
        """
        加载测试用例

        Args:
            filename: 文件名或完整路径

        Returns:
            Dict: 测试用例字典
        """
        # 如果是相对路径，补充storage_dir
        filepath = Path(filename)
        if not filepath.is_absolute():
            filepath = self.storage_dir / filename

        with open(filepath, "r", encoding="utf-8") as f:
            testcase = yaml.safe_load(f)

        return testcase

    def list_testcases(self) -> List[str]:
        """
        列出所有测试用例

        Returns:
            List[str]: 用例文件名列表
        """
        yaml_files = list(self.storage_dir.glob("*.yaml")) + list(self.storage_dir.glob("*.yml"))
        return [f.name for f in sorted(yaml_files, key=lambda x: x.stat().st_mtime, reverse=True)]

    def delete_testcase(self, filename: str) -> bool:
        """
        删除测试用例

        Args:
            filename: 文件名

        Returns:
            bool: 是否删除成功
        """
        filepath = self.storage_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def export_testcase(self, testcase: Dict[str, Any]) -> str:
        """
        导出测试用例为YAML字符串

        Args:
            testcase: 测试用例字典

        Returns:
            str: YAML格式字符串
        """
        return yaml.dump(testcase, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def import_testcase(self, yaml_string: str) -> Dict[str, Any]:
        """
        从YAML字符串导入测试用例

        Args:
            yaml_string: YAML格式字符串

        Returns:
            Dict: 测试用例字典
        """
        return yaml.safe_load(yaml_string)
