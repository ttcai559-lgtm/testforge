# AI测试用例生成模块

从需求文档自动提取测试点并生成XMind思维导图

## 🎯 核心功能

1. **AI智能提取** - 自动从Word/PDF需求文档提取测试用例
2. **分级标注系统** - 绿/黄/红三色标注，快速识别需要review的用例
3. **需求缺陷检测** - 自动发现需求中的模糊、矛盾、缺失等问题
4. **问题清单生成** - 自动生成待澄清问题，发给产品经理确认
5. **XMind导出** - 生成标准的测试用例思维导图
6. **持续学习** - 反馈式学习 + 案例库积累

## 📦 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# OpenAI配置（推荐）
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，使用代理时修改

# Claude配置（可选）
ANTHROPIC_API_KEY=your-api-key-here

# 数据库配置（可选，用于案例库）
DATABASE_URL=postgresql://user:password@localhost:5432/testforge

# Redis配置（可选，用于任务队列）
REDIS_URL=redis://localhost:6379/0
```

## 🚀 快速开始

### 方式1：使用Streamlit界面（推荐）

```bash
streamlit run streamlit_app.py
```

然后访问：http://localhost:8501

### 方式2：使用FastAPI服务

```bash
python api.py
```

然后访问：
- API文档：http://localhost:8001/docs
- 健康检查：http://localhost:8001/api/health

### 方式3：直接使用Python代码

```python
from src.ai_testcase_gen import TestCaseGenerator

# 创建生成器
generator = TestCaseGenerator(ai_model="openai")

# 生成测试用例
result = generator.generate(
    document_path="需求文档.docx",
    enable_defect_detection=True,
    enable_question_generation=True
)

if result['success']:
    print(f"✅ 生成成功！")
    print(f"XMind文件：{result['xmind_path']}")
    print(f"统计数据：{result['statistics']}")
else:
    print(f"❌ 生成失败：{result['error']}")
```

## 📊 输出示例

### XMind结构

```
TestForge - API测试工具
├─ 用户登录模块
│  ├─ 功能测试
│  │  ├─ 正常场景
│  │  │  └─ ✅ 正确用户名密码登录成功
│  │  ├─ 异常场景
│  │  │  ├─ ⚠️ 错误密码登录失败
│  │  │  └─ ⚠️ 用户名不存在
│  │  └─ 边界场景
│  │     └─ ❌ 密码长度边界测试（需人工补充）
│  ├─ 性能测试
│  └─ 安全测试
├─ 🤔 问题清单
│  ├─ 🔴 高优先级
│  │  └─ 密码最大长度是多少？
│  └─ 🟡 中优先级
└─ 🐛 需求缺陷
   └─ 🔴 高严重度
      └─ [矛盾] 登录失败次数限制前后不一致
```

### 统计数据

```json
{
  "total_cases": 100,
  "green_cases": 70,
  "yellow_cases": 20,
  "red_cases": 10,
  "green_percentage": 70.0,
  "yellow_percentage": 20.0,
  "red_percentage": 10.0,
  "questions_count": 15,
  "defects_count": 5
}
```

## 🎨 分级标注说明

| 标记 | 置信度 | 含义 | 操作建议 |
|------|--------|------|----------|
| ✅ 绿色 | 高 (≥70%) | AI确信理解，可直接使用 | 快速扫一眼即可 |
| ⚠️ 黄色 | 中 (40-70%) | 部分理解，建议review | 重点关注，补充完善 |
| ❌ 红色 | 低 (<40%) | 无法理解，必须人工补充 | 必须人工编写 |

## 📝 API使用示例

### 1. 上传文档

```bash
curl -X POST "http://localhost:8001/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@需求文档.docx"
```

### 2. 生成测试用例

```bash
curl -X POST "http://localhost:8001/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "document_path": "/uploads/xxx.docx",
    "enable_defect_detection": true,
    "enable_question_generation": true
  }'
```

### 3. 查询进度

```bash
curl "http://localhost:8001/api/status/{task_id}"
```

### 4. 下载XMind

```bash
curl "http://localhost:8001/api/download/{filename}" -O
```

## 🏗️ 项目结构

```
ai_testcase_gen/
├── __init__.py           # 模块入口
├── config.py             # 配置文件
├── document_parser.py    # 文档解析器
├── ai_service.py         # AI服务封装
├── prompts.py            # Prompt模板
├── generator.py          # 核心生成器
├── xmind_builder.py      # XMind构建器
├── api.py                # FastAPI服务
├── streamlit_app.py      # Streamlit界面
├── requirements.txt      # 依赖列表
└── README.md             # 本文件
```

## 🔧 高级配置

### 自定义Prompt

编辑 `prompts.py` 文件，修改 `MAIN_EXTRACTION_PROMPT` 等模板。

### 切换AI模型

```python
# 使用Claude
generator = TestCaseGenerator(ai_model="claude")

# 使用自定义模型
from src.ai_testcase_gen.ai_service import OpenAIService

custom_service = OpenAIService(
    api_key="your-key",
    model="gpt-4-turbo",
    base_url="https://your-proxy.com/v1"
)

generator = TestCaseGenerator(ai_service=custom_service)
```

### 自定义XMind颜色

编辑 `config.py` 中的 `XMIND_COLORS`。

## ⚠️ 注意事项

1. **API成本** - AI调用会产生费用，建议使用GPT-4o或Claude 3.5 Sonnet
2. **文档质量** - 需求文档越清晰，AI生成质量越高
3. **人工Review** - AI生成的用例必须经过人工审核
4. **API限流** - 注意AI服务的API调用频率限制

## 🐛 常见问题

### Q: 生成的用例不准确怎么办？
A: 1) 检查需求文档是否清晰；2) 尝试调整Prompt模板；3) 使用更强的AI模型（如GPT-4o）

### Q: 能否支持离线运行？
A: 第一版需要调用在线AI API，后续可以考虑集成本地大模型

### Q: 如何提高生成速度？
A: 1) 使用更快的模型（如GPT-3.5）；2) 禁用缺陷检测和问题清单生成；3) 使用异步处理

### Q: 生成的XMind能否直接导入测试管理系统？
A: 后续版本会支持导出为TestLink、禅道等格式

## 📄 License

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request！

---

**TestForge AI测试用例生成器** - 让测试工程师从"打字员"变成"审核员"
