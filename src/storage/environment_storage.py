"""
Environment Storage

管理测试环境（媒体）的存储
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class EnvironmentStorage:
    """环境（媒体）存储管理类"""

    def __init__(self, storage_dir: str = "./environments"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_environment(self, env_data: Dict[str, Any]) -> str:
        """
        保存环境配置

        Args:
            env_data: 环境数据，包含name, base_url, default_params, default_headers等

        Returns:
            保存的文件名
        """
        name = env_data.get("name", "untitled")
        filename = f"{name}.yaml"
        filepath = self.storage_dir / filename

        # 添加元数据
        env_data["metadata"] = {
            "created_at": env_data.get("metadata", {}).get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
            "version": "1.0"
        }

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(env_data, f, allow_unicode=True, default_flow_style=False)

        return filename

    def load_environment(self, name: str) -> Optional[Dict[str, Any]]:
        """
        加载环境配置

        Args:
            name: 环境名称

        Returns:
            环境数据字典，如果不存在返回None
        """
        # First try direct filename match
        filename = f"{name}.yaml"
        filepath = self.storage_dir / filename

        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)

        # If not found, search all files for matching name field
        for file in self.storage_dir.glob("*.yaml"):
            if file.stem == ".gitkeep":
                continue
            try:
                with open(file, "r", encoding="utf-8") as f:
                    env_data = yaml.safe_load(f)
                    if env_data and env_data.get("name") == name:
                        return env_data
            except Exception as e:
                print(f"Error reading environment file {file}: {e}")
                continue

        return None

    def list_environments(self) -> List[str]:
        """
        列出所有环境

        Returns:
            环境名称列表
        """
        environments = []
        for file in self.storage_dir.glob("*.yaml"):
            if file.stem != ".gitkeep":
                environments.append(file.stem)
        return sorted(environments)

    def delete_environment(self, name: str) -> bool:
        """
        删除环境

        Args:
            name: 环境名称

        Returns:
            是否删除成功
        """
        # First try direct filename match
        filename = f"{name}.yaml"
        filepath = self.storage_dir / filename

        if filepath.exists():
            filepath.unlink()
            return True

        # If not found, search all files for matching name field
        for file in self.storage_dir.glob("*.yaml"):
            if file.stem == ".gitkeep":
                continue
            try:
                with open(file, "r", encoding="utf-8") as f:
                    env_data = yaml.safe_load(f)
                    if env_data and env_data.get("name") == name:
                        file.unlink()
                        return True
            except Exception as e:
                print(f"Error reading environment file {file}: {e}")
                continue

        return False

    def get_all_environments(self) -> List[Dict[str, Any]]:
        """
        获取所有环境的完整数据

        Returns:
            环境数据列表
        """
        environments = []
        for name in self.list_environments():
            env_data = self.load_environment(name)
            if env_data:
                environments.append(env_data)
        return environments
