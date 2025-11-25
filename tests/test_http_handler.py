"""
HTTP Handler 测试
"""

import pytest
from src.protocols import HTTPHandler, Request


def test_http_handler_build_request():
    """测试构建HTTP请求"""
    handler = HTTPHandler()

    config = {
        "method": "POST",
        "url": "https://httpbin.org/post",
        "headers": {"Content-Type": "application/json"},
        "body": {"test": "data"}
    }

    request = handler.build_request(config)

    assert request.method == "POST"
    assert request.url == "https://httpbin.org/post"
    assert request.headers["Content-Type"] == "application/json"
    assert request.body == {"test": "data"}


def test_http_handler_send_request():
    """测试发送HTTP请求"""
    handler = HTTPHandler()

    # 使用httpbin测试API
    config = {
        "method": "GET",
        "url": "https://httpbin.org/get",
        "params": {"test": "value"}
    }

    request = handler.build_request(config)
    response = handler.send_request(request)

    assert response.status_code == 200
    assert response.elapsed_ms > 0
    assert isinstance(response.body, dict)


def test_http_handler_validate_config():
    """测试配置验证"""
    handler = HTTPHandler()

    # 合法配置
    valid_config = {"url": "https://example.com", "method": "GET"}
    assert handler.validate_config(valid_config) is True

    # 缺少URL
    invalid_config = {"method": "GET"}
    assert handler.validate_config(invalid_config) is False

    # 非法method
    invalid_method = {"url": "https://example.com", "method": "INVALID"}
    assert handler.validate_config(invalid_method) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
