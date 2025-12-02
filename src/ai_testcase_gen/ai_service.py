"""
AI服务：封装大模型调用
"""
import json
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIServiceBase(ABC):
    """AI服务基类"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass

    @abstractmethod
    def generate_json(self, prompt: str, **kwargs) -> Dict:
        """生成JSON格式输出"""
        pass

    def analyze_image(self, image_data: str, prompt: str, media_type: str = "image/jpeg", **kwargs) -> str:
        """
        分析图片内容(可选实现,不是所有AI服务都支持视觉)

        Args:
            image_data: base64编码的图片数据
            prompt: 分析提示词
            media_type: 图片MIME类型

        Returns:
            AI对图片的描述
        """
        return f"[此AI服务不支持图片分析]"


class OpenAIService(AIServiceBase):
    """OpenAI服务"""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 8000, max_retries: int = 3, timeout: float = 180.0) -> str:
        """
        生成文本（带重试机制）

        Args:
            prompt: 提示词
            temperature: 温度参数（0-1），越低越确定
            max_tokens: 最大token数
            max_retries: 最大重试次数
            timeout: API 调用超时时间（秒），默认 180 秒

        Returns:
            生成的文本
        """
        import time

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一位资深软件测试工程师。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout  # 添加超时设置
                )
                return response.choices[0].message.content
            except Exception as e:
                error_msg = str(e)
                # 检查是否是网络错误或502错误
                if ("502" in error_msg or "timeout" in error_msg.lower()) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间
                    logger.warning(f"OpenAI API调用失败，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"OpenAI API调用失败: {e}")
                    raise

    def generate_json(self, prompt: str, **kwargs) -> Dict:
        """生成JSON格式输出"""
        response_text = self.generate(prompt, **kwargs)

        # 提取JSON部分
        json_text = self._extract_json(response_text)

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"错误位置: line {e.lineno}, column {e.colno}")
            logger.error(f"提取的JSON (前500字符): {json_text[:500]}")
            logger.error(f"提取的JSON (后500字符): {json_text[-500:]}")

            # 保存原始响应到文件用于调试
            import os
            import time
            timestamp = int(time.time())
            debug_file = os.path.join(os.getcwd(), f"debug_ai_response_{timestamp}.txt")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write("=== 原始AI响应 ===\n")
                f.write(response_text)
                f.write("\n\n=== 提取的JSON ===\n")
                f.write(json_text)
            logger.error(f"原始响应已保存到: {debug_file}")

            # 也保存一份到固定文件名（向后兼容）
            debug_file_fixed = os.path.join(os.getcwd(), "debug_ai_response.txt")
            with open(debug_file_fixed, "w", encoding="utf-8") as f:
                f.write("=== 原始AI响应 ===\n")
                f.write(response_text)
                f.write("\n\n=== 提取的JSON ===\n")
                f.write(json_text)

            raise ValueError(f"AI返回的JSON格式有误: {e}")

    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON部分并清理常见错误"""
        # 移除markdown代码块标记
        text = text.strip()

        # 移除开头的 "```json" 标记
        if text.startswith("```json"):
            text = text[7:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()

        # 移除结尾的 "```" 标记
        if text.endswith("```"):
            text = text[:-3].strip()

        # 如果仍然有代码块标记，尝试提取
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()

        # 最后尝试提取 JSON 对象
        if not text.startswith("{"):
            start = text.find("{")
            if start != -1:
                end = text.rfind("}") + 1
                if end > start:
                    text = text[start:end]

        # 清理JSON格式错误
        text = self._cleanup_json(text)
        return text

    def _cleanup_json(self, json_str: str) -> str:
        """清理JSON字符串中的常见错误"""
        import re

        # 1. 移除数组或对象最后一个元素后的多余逗号
        json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)

        # 2. 修复中文引号为英文引号
        json_str = json_str.replace('"', '"').replace('"', '"')
        json_str = json_str.replace(''', "'").replace(''', "'")

        # 3. 修复JSON字符串值内部的转义引号
        # AI经常在字符串值中使用 \" 来表示引号,这会破坏JSON结构
        # 简单策略: 直接替换所有 \" 为单引号
        json_str = json_str.replace('\\"', "'")

        # 4. 移除多余的控制字符
        json_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', json_str)

        return json_str


class ClaudeService(AIServiceBase):
    """Claude服务"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", base_url: Optional[str] = None):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("请安装 anthropic: pip install anthropic")

        # 支持自定义base_url和auth_token
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        if base_url:
            kwargs['base_url'] = base_url

        # 如果使用自定义认证token（而非API key）
        import os
        auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
        if auth_token and not api_key:
            kwargs['api_key'] = auth_token  # Anthropic客户端使用api_key参数

        self.client = Anthropic(**kwargs)
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 8000, max_retries: int = 3) -> str:
        """生成文本（带重试机制）"""
        import time

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                # 检查是否因为token限制被截断
                if hasattr(response, 'stop_reason') and response.stop_reason == 'max_tokens':
                    logger.warning(f"Claude响应因达到max_tokens({max_tokens})而被截断，建议增加max_tokens或简化prompt")
                return response.content[0].text
            except Exception as e:
                error_msg = str(e)
                # 检查是否是502错误（代理服务器问题）
                if "502" in error_msg and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间: 2s, 4s, 6s
                    logger.warning(f"Claude API调用失败(502错误)，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Claude API调用失败: {e}")
                    raise

    def generate_json(self, prompt: str, **kwargs) -> Dict:
        """生成JSON格式输出"""
        response_text = self.generate(prompt, **kwargs)

        # 提取JSON部分
        json_text = self._extract_json(response_text)

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"错误位置: line {e.lineno}, column {e.colno}")
            logger.error(f"提取的JSON (前500字符): {json_text[:500]}")
            logger.error(f"提取的JSON (后500字符): {json_text[-500:]}")

            # 保存原始响应到文件用于调试
            import os
            import time
            timestamp = int(time.time())
            debug_file = os.path.join(os.getcwd(), f"debug_ai_response_{timestamp}.txt")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write("=== 原始AI响应 ===\n")
                f.write(response_text)
                f.write("\n\n=== 提取的JSON ===\n")
                f.write(json_text)
            logger.error(f"原始响应已保存到: {debug_file}")

            # 也保存一份到固定文件名（向后兼容）
            debug_file_fixed = os.path.join(os.getcwd(), "debug_ai_response.txt")
            with open(debug_file_fixed, "w", encoding="utf-8") as f:
                f.write("=== 原始AI响应 ===\n")
                f.write(response_text)
                f.write("\n\n=== 提取的JSON ===\n")
                f.write(json_text)

            raise ValueError(f"AI返回的JSON格式有误: {e}")

    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON部分并清理常见错误"""
        text = text.strip()

        # 移除开头的 "```json" 标记
        if text.startswith("```json"):
            text = text[7:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()

        # 移除结尾的 "```" 标记
        if text.endswith("```"):
            text = text[:-3].strip()

        # 如果仍然有代码块标记，尝试提取
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()

        # 最后尝试提取 JSON 对象
        if not text.startswith("{"):
            start = text.find("{")
            if start != -1:
                end = text.rfind("}") + 1
                if end > start:
                    text = text[start:end]

        # 清理JSON格式错误
        text = self._cleanup_json(text)
        return text

    def _cleanup_json(self, json_str: str) -> str:
        """清理JSON字符串中的常见错误"""
        import re

        # 1. 移除数组或对象最后一个元素后的多余逗号
        json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)

        # 2. 修复中文引号为英文引号
        json_str = json_str.replace('"', '"').replace('"', '"')
        json_str = json_str.replace(''', "'").replace(''', "'")

        # 3. 修复JSON字符串值内部的转义引号
        # AI经常在字符串值中使用 \" 来表示引号,这会破坏JSON结构
        # 简单策略: 直接替换所有 \" 为单引号
        json_str = json_str.replace('\\"', "'")

        # 4. 移除多余的控制字符
        json_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', json_str)

        return json_str

    def analyze_image(self, image_data: str, prompt: str, media_type: str = "image/jpeg", **kwargs) -> str:
        """
        使用Claude Vision API分析图片

        Args:
            image_data: base64编码的图片数据
            prompt: 分析提示词
            media_type: 图片MIME类型

        Returns:
            AI对图片的描述
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude图片分析失败: {e}")
            return f"[图片分析失败: {str(e)}]"


class AIServiceFactory:
    """AI服务工厂"""

    @staticmethod
    def create(model_type: str, **config) -> AIServiceBase:
        """
        创建AI服务实例

        Args:
            model_type: 模型类型（openai/claude/wenxin/qianwen）
            **config: 配置参数

        Returns:
            AI服务实例
        """
        if model_type == "openai":
            try:
                from .config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
            except ImportError:
                from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
            return OpenAIService(
                api_key=config.get("api_key", OPENAI_API_KEY),
                model=config.get("model", OPENAI_MODEL),
                base_url=config.get("base_url", OPENAI_BASE_URL)
            )

        elif model_type == "claude":
            try:
                from .config import ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL, CLAUDE_MODEL
            except ImportError:
                from config import ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL, CLAUDE_MODEL
            # 优先使用AUTH_TOKEN，其次使用API_KEY
            api_key = config.get("api_key", ANTHROPIC_AUTH_TOKEN or ANTHROPIC_API_KEY)
            return ClaudeService(
                api_key=api_key,
                model=config.get("model", CLAUDE_MODEL),
                base_url=config.get("base_url", ANTHROPIC_BASE_URL)
            )

        # TODO: 实现文心一言和通义千问
        elif model_type == "wenxin":
            raise NotImplementedError("文心一言服务待实现")

        elif model_type == "qianwen":
            raise NotImplementedError("通义千问服务待实现")

        else:
            raise ValueError(f"不支持的模型类型：{model_type}")


# 使用示例
if __name__ == "__main__":
    # 测试OpenAI
    service = AIServiceFactory.create("openai")

    prompt = """请生成一个简单的测试用例，格式如下：
    {
        "title": "测试用例标题",
        "description": "描述"
    }
    """

    result = service.generate_json(prompt)
    print(result)
