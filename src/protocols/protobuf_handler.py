"""
Protobuf Handler

处理Protobuf协议的编译、序列化和反序列化
"""

import os
import sys
import shutil
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from google.protobuf import json_format
from google.protobuf.message import Message
from google.protobuf.descriptor import Descriptor


class ProtobufHandler:
    """Protobuf处理器"""

    def __init__(self, proto_dir: str = "./proto_files", compiled_dir: str = "./compiled_protos"):
        """
        初始化Protobuf处理器

        Args:
            proto_dir: proto文件存储目录
            compiled_dir: 编译后的Python文件存储目录
        """
        self.proto_dir = Path(proto_dir)
        self.compiled_dir = Path(compiled_dir)
        self.proto_dir.mkdir(exist_ok=True)
        self.compiled_dir.mkdir(exist_ok=True)

        # 将编译目录添加到Python路径
        if str(self.compiled_dir) not in sys.path:
            sys.path.insert(0, str(self.compiled_dir))

        # 缓存已加载的proto模块
        self._loaded_modules: Dict[str, Any] = {}

    def save_proto_file(self, environment_name: str, proto_content: bytes) -> str:
        """
        保存proto文件

        Args:
            environment_name: 环境名称
            proto_content: proto文件内容

        Returns:
            保存的文件路径
        """
        env_proto_dir = self.proto_dir / environment_name
        env_proto_dir.mkdir(exist_ok=True)

        # 保存proto文件
        proto_file_path = env_proto_dir / f"{environment_name}.proto"
        with open(proto_file_path, "wb") as f:
            f.write(proto_content)

        return str(proto_file_path)

    def compile_proto(self, environment_name: str) -> Tuple[bool, str]:
        """
        编译proto文件

        Args:
            environment_name: 环境名称

        Returns:
            (是否成功, 错误信息或成功消息)
        """
        proto_file_path = self.proto_dir / environment_name / f"{environment_name}.proto"

        if not proto_file_path.exists():
            return False, f"Proto file not found: {proto_file_path}"

        # 创建环境专属的编译目录
        env_compiled_dir = self.compiled_dir / environment_name
        env_compiled_dir.mkdir(exist_ok=True)

        # 创建 __init__.py 文件
        init_file = env_compiled_dir / "__init__.py"
        init_file.touch()

        try:
            # 使用protoc编译proto文件
            cmd = [
                sys.executable, "-m", "grpc_tools.protoc",
                f"-I{self.proto_dir / environment_name}",
                f"--python_out={env_compiled_dir}",
                f"--grpc_python_out={env_compiled_dir}",
                str(proto_file_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # 清除之前加载的模块缓存
            if environment_name in self._loaded_modules:
                del self._loaded_modules[environment_name]

            return True, f"Proto file compiled successfully: {proto_file_path.name}"

        except subprocess.CalledProcessError as e:
            error_msg = f"Compilation failed: {e.stderr}"
            return False, error_msg
        except Exception as e:
            return False, f"Unexpected error during compilation: {str(e)}"

    def get_message_types(self, environment_name: str) -> List[str]:
        """
        获取proto文件中定义的所有message类型

        Args:
            environment_name: 环境名称

        Returns:
            message类型名称列表
        """
        try:
            module = self._load_proto_module(environment_name)
            if not module:
                return []

            # 获取所有Message子类
            message_types = []
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, Message) and obj is not Message:
                    message_types.append(name)

            return sorted(message_types)

        except Exception as e:
            print(f"Error getting message types: {e}")
            return []

    def json_to_protobuf(
        self,
        environment_name: str,
        message_name: str,
        json_data: Dict[str, Any]
    ) -> Optional[bytes]:
        """
        将JSON转换为Protobuf二进制数据

        Args:
            environment_name: 环境名称
            message_name: Message类型名称
            json_data: JSON数据

        Returns:
            Protobuf二进制数据，失败返回None
        """
        try:
            module = self._load_proto_module(environment_name)
            if not module:
                raise ValueError(f"Failed to load proto module for {environment_name}")

            # 获取Message类
            if not hasattr(module, message_name):
                raise ValueError(f"Message type '{message_name}' not found in proto file")

            message_class = getattr(module, message_name)

            # 创建Message实例
            message = message_class()

            # 从JSON填充
            json_format.ParseDict(json_data, message)

            # 序列化为二进制
            return message.SerializeToString()

        except Exception as e:
            print(f"Error converting JSON to Protobuf: {e}")
            return None

    def protobuf_to_json(
        self,
        environment_name: str,
        message_name: str,
        binary_data: bytes
    ) -> Optional[Dict[str, Any]]:
        """
        将Protobuf二进制数据转换为JSON

        Args:
            environment_name: 环境名称
            message_name: Message类型名称
            binary_data: Protobuf二进制数据

        Returns:
            JSON数据，失败返回None
        """
        try:
            module = self._load_proto_module(environment_name)
            if not module:
                raise ValueError(f"Failed to load proto module for {environment_name}")

            # 获取Message类
            if not hasattr(module, message_name):
                raise ValueError(f"Message type '{message_name}' not found in proto file")

            message_class = getattr(module, message_name)

            # 创建Message实例
            message = message_class()

            # 从二进制解析
            message.ParseFromString(binary_data)

            # 转换为JSON
            # 注意: including_default_value_fields 参数在某些版本的protobuf中不支持
            try:
                json_data = json_format.MessageToDict(
                    message,
                    preserving_proto_field_name=True,
                    including_default_value_fields=True
                )
            except TypeError:
                # 如果不支持 including_default_value_fields 参数，使用默认配置
                json_data = json_format.MessageToDict(
                    message,
                    preserving_proto_field_name=True
                )

            return json_data

        except Exception as e:
            print(f"Error converting Protobuf to JSON: {e}")
            return None

    def _load_proto_module(self, environment_name: str) -> Optional[Any]:
        """
        加载编译后的proto模块

        Args:
            environment_name: 环境名称

        Returns:
            加载的模块，失败返回None
        """
        # 检查缓存
        if environment_name in self._loaded_modules:
            return self._loaded_modules[environment_name]

        try:
            # 查找编译后的Python文件
            pb2_file = self.compiled_dir / environment_name / f"{environment_name}_pb2.py"

            if not pb2_file.exists():
                print(f"Compiled proto file not found: {pb2_file}")
                return None

            # 动态加载模块
            module_name = f"{environment_name}_pb2"
            spec = importlib.util.spec_from_file_location(module_name, pb2_file)

            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 缓存模块
            self._loaded_modules[environment_name] = module

            return module

        except Exception as e:
            print(f"Error loading proto module: {e}")
            return None

    def delete_proto_files(self, environment_name: str) -> bool:
        """
        删除指定环境的proto文件和编译文件

        Args:
            environment_name: 环境名称

        Returns:
            是否删除成功
        """
        try:
            # 删除proto文件
            env_proto_dir = self.proto_dir / environment_name
            if env_proto_dir.exists():
                shutil.rmtree(env_proto_dir)

            # 删除编译文件
            env_compiled_dir = self.compiled_dir / environment_name
            if env_compiled_dir.exists():
                shutil.rmtree(env_compiled_dir)

            # 清除缓存
            if environment_name in self._loaded_modules:
                del self._loaded_modules[environment_name]

            return True

        except Exception as e:
            print(f"Error deleting proto files: {e}")
            return False

    def has_proto_file(self, environment_name: str) -> bool:
        """
        检查指定环境是否有proto文件

        Args:
            environment_name: 环境名称

        Returns:
            是否存在proto文件
        """
        proto_file_path = self.proto_dir / environment_name / f"{environment_name}.proto"
        return proto_file_path.exists()
