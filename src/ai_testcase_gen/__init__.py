"""
AI测试用例生成模块
功能：从需求文档自动提取测试点并生成XMind思维导图
"""

__version__ = "1.0.0"
__author__ = "TestForge Team"

from .generator import TestCaseGenerator
from .document_parser import DocumentParser
from .xmind_builder import XMindBuilder

__all__ = [
    'TestCaseGenerator',
    'DocumentParser',
    'XMindBuilder'
]
