"""
协议抽象基类

定义所有协议处理器的统一接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class Request:
    """统一的请求数据模型"""

    method: str  # HTTP: GET/POST/etc, gRPC: method_name
    url: str  # 请求地址
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)  # Query参数
    body: Optional[Any] = None  # 请求体（JSON/Protobuf等）
    timeout: int = 30  # 超时时间（秒）

    # 协议特定配置（扩展点）
    protocol_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """统一的响应数据模型"""

    status_code: int  # HTTP状态码或协议状态
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None  # 响应体（JSON/Protobuf等）
    elapsed_ms: float = 0  # 响应时间（毫秒）
    timestamp: datetime = field(default_factory=datetime.now)

    # 原始响应对象（用于特殊处理）
    raw_response: Optional[Any] = None

    # 协议特定数据（扩展点）
    protocol_data: Dict[str, Any] = field(default_factory=dict)


class ProtocolHandler(ABC):
    """
    协议处理器抽象基类

    所有协议处理器必须实现此接口：
    - HTTPHandler
    - ProtobufHandler（未来）
    - gRPCHandler（未来）
    """

    @abstractmethod
    def build_request(self, config: Dict[str, Any]) -> Request:
        """
        从配置构建请求对象

        Args:
            config: 请求配置字典（来自UI或配置文件）

        Returns:
            Request: 统一的请求对象
        """
        pass

    @abstractmethod
    def send_request(self, request: Request) -> Response:
        """
        发送请求并获取响应

        Args:
            request: 统一的请求对象

        Returns:
            Response: 统一的响应对象
        """
        pass

    @abstractmethod
    def parse_response(self, response: Response) -> Dict[str, Any]:
        """
        解析响应为可读的字典格式

        Args:
            response: 统一的响应对象

        Returns:
            Dict: 解析后的响应数据
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证请求配置是否合法（可选实现）

        Args:
            config: 请求配置字典

        Returns:
            bool: 配置是否合法
        """
        return True
