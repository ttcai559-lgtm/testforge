"""
配置文件：AI测试用例生成模块
"""
import os
from typing import Literal
from pathlib import Path

# 加载.env文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv未安装，跳过
    pass

# ========================
# AI模型配置
# ========================

# 支持的AI模型
AI_MODEL_TYPE = Literal["openai", "claude", "wenxin", "qianwen"]

# 默认使用的模型
DEFAULT_AI_MODEL: AI_MODEL_TYPE = "claude"  # 使用 Claude API

# OpenAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"  # 或 gpt-4-turbo
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Claude配置
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_AUTH_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN", "")  # 支持自定义token
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", None)  # 支持自定义API地址
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")  # 可通过环境变量自定义模型名

# 文心一言配置
WENXIN_API_KEY = os.getenv("WENXIN_API_KEY", "")
WENXIN_SECRET_KEY = os.getenv("WENXIN_SECRET_KEY", "")

# 通义千问配置
QIANWEN_API_KEY = os.getenv("QIANWEN_API_KEY", "")

# ========================
# 置信度阈值配置
# ========================

# 置信度评分阈值
CONFIDENCE_THRESHOLDS = {
    "high": 0.7,    # >= 0.7 为绿色（高置信度）
    "medium": 0.4,  # 0.4-0.7 为黄色（中置信度）
    # < 0.4 为红色（低置信度）
}

# ========================
# XMind配置
# ========================

# XMind颜色配置（RGB格式）
XMIND_COLORS = {
    "green": "#28A745",   # 高置信度
    "yellow": "#FFC107",  # 中置信度
    "red": "#DC3545",     # 低置信度
    "default": "#FFFFFF"  # 默认白色
}

# XMind标准结构层级
XMIND_STRUCTURE = {
    "level1": "功能模块",
    "level2": "测试类型",  # 功能测试/性能测试/安全测试/兼容性测试
    "level3": "测试场景",  # 正常场景/异常场景/边界场景
    "level4": "测试用例"
}

# 标准测试类型
TEST_TYPES = [
    "功能测试",
    "性能测试",
    "安全测试",
    "兼容性测试"
]

# 标准场景分类
SCENARIO_TYPES = [
    "正常场景",
    "异常场景",
    "边界场景"
]

# ========================
# 文档解析配置
# ========================

# 支持的文档格式
SUPPORTED_FORMATS = [".docx", ".pdf"]

# 文档解析最大大小（MB）
MAX_DOCUMENT_SIZE_MB = 50

# ========================
# 数据库配置
# ========================

# PostgreSQL配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://testforge:testforge@localhost:5432/testforge_ai"
)

# 向量数据库配置（Qdrant）
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = "test_case_library"

# ========================
# 缓存配置
# ========================

# Redis配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ========================
# 文件存储配置
# ========================

# 上传文件存储路径
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")

# 临时文件自动清理配置
FILE_RETENTION_DAYS = int(os.getenv("FILE_RETENTION_DAYS", "7"))  # 默认保留7天

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========================
# 日志配置
# ========================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join(os.getcwd(), "logs", "ai_testcase_gen.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
