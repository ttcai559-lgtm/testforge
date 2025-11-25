"""
HTTP协议处理器

实现HTTP/HTTPS协议的请求发送和响应解析
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime

from .base import ProtocolHandler, Request, Response


class HTTPHandler(ProtocolHandler):
    """HTTP协议处理器"""

    def __init__(self):
        self.session = requests.Session()

    def build_request(self, config: Dict[str, Any]) -> Request:
        """
        从配置构建HTTP请求

        Config格式:
        {
            "method": "GET|POST|PUT|DELETE|PATCH",
            "url": "https://api.example.com/endpoint",
            "headers": {"Content-Type": "application/json"},
            "params": {"key": "value"},
            "body": {"data": "value"} 或 字符串,
            "timeout": 30
        }
        """
        return Request(
            method=config.get("method", "GET").upper(),
            url=config["url"],
            headers=config.get("headers", {}),
            params=config.get("params", {}),
            body=config.get("body"),
            timeout=config.get("timeout", 30)
        )

    def send_request(self, request: Request) -> Response:
        """发送HTTP请求"""
        start_time = datetime.now()

        try:
            # 准备请求体
            data = None
            json_data = None

            if request.body is not None:
                if isinstance(request.body, dict):
                    json_data = request.body
                else:
                    data = request.body

            # 发送请求
            raw_response = self.session.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.params,
                json=json_data,
                data=data,
                timeout=request.timeout
            )

            # 计算耗时
            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            # 解析响应体
            body = self._parse_response_body(raw_response)

            return Response(
                status_code=raw_response.status_code,
                headers=dict(raw_response.headers),
                body=body,
                elapsed_ms=elapsed,
                timestamp=datetime.now(),
                raw_response=raw_response
            )

        except requests.exceptions.Timeout:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            return Response(
                status_code=408,  # Request Timeout
                headers={},
                body={"error": "Request timeout"},
                elapsed_ms=elapsed,
                timestamp=datetime.now()
            )

        except requests.exceptions.RequestException as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            return Response(
                status_code=0,  # Network error
                headers={},
                body={"error": str(e)},
                elapsed_ms=elapsed,
                timestamp=datetime.now()
            )

    def parse_response(self, response: Response) -> Dict[str, Any]:
        """解析响应为可读格式"""
        return {
            "status_code": response.status_code,
            "headers": response.headers,
            "body": response.body,
            "elapsed_ms": round(response.elapsed_ms, 2),
            "timestamp": response.timestamp.isoformat()
        }

    def _parse_response_body(self, raw_response: requests.Response) -> Any:
        """解析响应体"""
        content_type = raw_response.headers.get("Content-Type", "")

        # JSON响应
        if "application/json" in content_type:
            try:
                return raw_response.json()
            except json.JSONDecodeError:
                return raw_response.text

        # 文本响应
        if "text/" in content_type or "application/xml" in content_type:
            return raw_response.text

        # 二进制响应
        return f"<Binary data, {len(raw_response.content)} bytes>"

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证HTTP请求配置"""
        # 必须有URL
        if "url" not in config:
            return False

        # method必须是合法的HTTP方法
        method = config.get("method", "GET").upper()
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
            return False

        return True
