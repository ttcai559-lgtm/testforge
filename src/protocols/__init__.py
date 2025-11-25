"""
协议层 - 插件化协议处理

支持多种协议的统一接口抽象
"""

from .base import ProtocolHandler, Request, Response
from .http_handler import HTTPHandler

__all__ = ["ProtocolHandler", "Request", "Response", "HTTPHandler"]
