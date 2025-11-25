"""
断言引擎

支持多种断言类型和安全的Python表达式断言
"""

from dataclasses import dataclass
from typing import Any, Dict, List
from datetime import datetime


@dataclass
class AssertionResult:
    """断言结果"""
    passed: bool  # 是否通过
    assertion: str  # 断言表达式
    message: str  # 结果消息
    actual_value: Any = None  # 实际值
    expected_value: Any = None  # 期望值
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AssertionEngine:
    """
    断言引擎

    支持的断言类型：
    1. 状态码断言：status == 200
    2. JSON字段断言：response['data']['id'] > 0
    3. 响应时间断言：elapsed_ms < 1000
    4. 自定义Python表达式
    """

    def __init__(self):
        self.results: List[AssertionResult] = []

    def evaluate(self, assertion: str, context: Dict[str, Any]) -> AssertionResult:
        """
        执行单个断言

        Args:
            assertion: 断言表达式（Python表达式）
            context: 上下文变量字典
                - status: HTTP状态码
                - response: 响应体（dict）
                - headers: 响应头（dict）
                - elapsed_ms: 响应时间（float）

        Returns:
            AssertionResult: 断言结果
        """
        try:
            # 创建安全的执行环境（限制可用函数和模块）
            safe_builtins = {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'any': any,
                'all': all,
            }

            # 执行断言
            result = eval(assertion, {"__builtins__": safe_builtins}, context)

            if result is True:
                assertion_result = AssertionResult(
                    passed=True,
                    assertion=assertion,
                    message=f"Assertion passed: {assertion}"
                )
            else:
                assertion_result = AssertionResult(
                    passed=False,
                    assertion=assertion,
                    message=f"Assertion failed: {assertion} evaluated to {result}"
                )

        except KeyError as e:
            assertion_result = AssertionResult(
                passed=False,
                assertion=assertion,
                message=f"KeyError: {e} not found in response"
            )

        except Exception as e:
            assertion_result = AssertionResult(
                passed=False,
                assertion=assertion,
                message=f"Error: {type(e).__name__}: {str(e)}"
            )

        self.results.append(assertion_result)
        return assertion_result

    def evaluate_all(self, assertions: List[str], context: Dict[str, Any]) -> List[AssertionResult]:
        """
        执行多个断言

        Args:
            assertions: 断言表达式列表
            context: 上下文变量

        Returns:
            List[AssertionResult]: 所有断言结果
        """
        results = []
        for assertion in assertions:
            result = self.evaluate(assertion, context)
            results.append(result)
        return results

    def all_passed(self) -> bool:
        """检查所有断言是否全部通过"""
        return all(result.passed for result in self.results)

    def get_summary(self) -> Dict[str, Any]:
        """获取断言摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0
        }

    def reset(self):
        """重置断言结果"""
        self.results = []
