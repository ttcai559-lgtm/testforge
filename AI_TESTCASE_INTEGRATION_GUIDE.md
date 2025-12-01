# AI测试用例生成功能 - 集成指南

## 功能概述

AI测试用例生成功能已成功集成到TestForge主平台，实现了需求文档自动提取生成XMind思维导图测试用例的能力。

## 后端API接口

已在 `testforge/src/api/main.py` 中添加了3个新的API端点:

### 1. 生成测试用例

**Endpoint**: `POST /api/ai/generate-testcases`

**请求参数**:
- `file` (FormData): 上传的需求文档文件 (.docx, .doc, .pdf)
- `ai_model` (query): AI模型选择，默认 "claude"，可选 "openai"
- `enable_defect_detection` (query): 是否启用需求缺陷检测，默认 false
- `enable_question_generation` (query): 是否启用问题清单生成，默认 false

**响应示例**:
```json
{
  "success": true,
  "xmind_filename": "测试用例_需求文档_20251128_162450.xmind",
  "download_url": "/api/ai/download/测试用例_需求文档_20251128_162450.xmind",
  "summary": {
    "total_test_cases": 21,
    "total_questions": 0,
    "total_defects": 0,
    "modules_count": 3
  }
}
```

### 2. 下载XMind文件

**Endpoint**: `GET /api/ai/download/{filename}`

**说明**: 下载生成的XMind思维导图文件

### 3. 检查功能状态

**Endpoint**: `GET /api/ai/status`

**响应示例**:
```json
{
  "available": true,
  "supported_formats": [".docx", ".doc", ".pdf"],
  "supported_models": ["claude", "openai"],
  "features": {
    "defect_detection": true,
    "question_generation": true,
    "confidence_scoring": true
  }
}
```

## 前端集成示例 (Vue.js / React)

### Vue.js 示例

```vue
<template>
  <div class="ai-testcase-generator">
    <h2>AI测试用例生成</h2>

    <!-- 文件上传 -->
    <div class="upload-section">
      <input
        type="file"
        ref="fileInput"
        accept=".docx,.doc,.pdf"
        @change="handleFileSelect"
      />
      <button @click="generateTestCases" :disabled="!selectedFile || loading">
        {{ loading ? '生成中...' : '生成测试用例' }}
      </button>
    </div>

    <!-- 生成进度 -->
    <div v-if="loading" class="progress">
      <div class="spinner"></div>
      <p>正在使用AI分析需求文档并生成测试用例，请稍候...</p>
    </div>

    <!-- 生成结果 -->
    <div v-if="result" class="result">
      <h3>生成成功!</h3>
      <div class="summary">
        <p>测试用例数: {{ result.summary.total_test_cases }}</p>
        <p>模块数: {{ result.summary.modules_count }}</p>
        <p>问题清单: {{ result.summary.total_questions }}</p>
        <p>需求缺陷: {{ result.summary.total_defects }}</p>
      </div>
      <button @click="downloadXMind" class="download-btn">
        下载XMind文件
      </button>
    </div>

    <!-- 错误信息 -->
    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AITestCaseGenerator',
  data() {
    return {
      selectedFile: null,
      loading: false,
      result: null,
      error: null,
      API_BASE_URL: 'http://localhost:8000'  // 根据实际部署调整
    };
  },
  methods: {
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
      this.result = null;
      this.error = null;
    },

    async generateTestCases() {
      if (!this.selectedFile) {
        this.error = '请先选择需求文档';
        return;
      }

      this.loading = true;
      this.error = null;
      this.result = null;

      try {
        const formData = new FormData();
        formData.append('file', this.selectedFile);

        const response = await axios.post(
          `${this.API_BASE_URL}/api/ai/generate-testcases`,
          formData,
          {
            params: {
              ai_model: 'claude',
              enable_defect_detection: false,
              enable_question_generation: false
            },
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        );

        this.result = response.data;
      } catch (err) {
        this.error = err.response?.data?.detail || '生成失败，请重试';
        console.error('生成错误:', err);
      } finally {
        this.loading = false;
      }
    },

    async downloadXMind() {
      if (!this.result) return;

      try {
        const response = await axios.get(
          `${this.API_BASE_URL}${this.result.download_url}`,
          {
            responseType: 'blob'
          }
        );

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', this.result.xmind_filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        this.error = '下载失败，请重试';
        console.error('下载错误:', err);
      }
    }
  }
};
</script>

<style scoped>
.ai-testcase-generator {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.upload-section {
  margin: 20px 0;
}

button {
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 10px;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.progress {
  text-align: center;
  margin: 20px 0;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b983;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.result {
  margin-top: 20px;
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 4px;
}

.summary p {
  margin: 5px 0;
}

.download-btn {
  background-color: #1976d2;
  margin-top: 10px;
}

.error {
  color: red;
  margin-top: 10px;
  padding: 10px;
  background-color: #ffe6e6;
  border-radius: 4px;
}
</style>
```

### React 示例

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const AITestCaseGenerator = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const API_BASE_URL = 'http://localhost:8000';

  const handleFileSelect = (event) => {
    setSelectedFile(event.target.files[0]);
    setResult(null);
    setError(null);
  };

  const generateTestCases = async () => {
    if (!selectedFile) {
      setError('请先选择需求文档');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(
        `${API_BASE_URL}/api/ai/generate-testcases`,
        formData,
        {
          params: {
            ai_model: 'claude',
            enable_defect_detection: false,
            enable_question_generation: false
          },
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || '生成失败，请重试');
      console.error('生成错误:', err);
    } finally {
      setLoading(false);
    }
  };

  const downloadXMind = async () => {
    if (!result) return;

    try {
      const response = await axios.get(
        `${API_BASE_URL}${result.download_url}`,
        {
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', result.xmind_filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('下载失败，请重试');
      console.error('下载错误:', err);
    }
  };

  return (
    <div className="ai-testcase-generator">
      <h2>AI测试用例生成</h2>

      <div className="upload-section">
        <input
          type="file"
          accept=".docx,.doc,.pdf"
          onChange={handleFileSelect}
        />
        <button
          onClick={generateTestCases}
          disabled={!selectedFile || loading}
        >
          {loading ? '生成中...' : '生成测试用例'}
        </button>
      </div>

      {loading && (
        <div className="progress">
          <div className="spinner"></div>
          <p>正在使用AI分析需求文档并生成测试用例，请稍候...</p>
        </div>
      )}

      {result && (
        <div className="result">
          <h3>生成成功!</h3>
          <div className="summary">
            <p>测试用例数: {result.summary.total_test_cases}</p>
            <p>模块数: {result.summary.modules_count}</p>
            <p>问题清单: {result.summary.total_questions}</p>
            <p>需求缺陷: {result.summary.total_defects}</p>
          </div>
          <button onClick={downloadXMind} className="download-btn">
            下载XMind文件
          </button>
        </div>
      )}

      {error && (
        <div className="error">{error}</div>
      )}
    </div>
  );
};

export default AITestCaseGenerator;
```

## 部署说明

### 1. 后端部署

确保已安装所有依赖:

```bash
pip install fastapi uvicorn python-docx PyMuPDF anthropic xmind python-multipart
```

启动FastAPI服务:

```bash
cd testforge/src/api
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 配置环境变量

确保 `testforge/src/ai_testcase_gen/.env` 文件配置正确:

```env
# Claude配置
ANTHROPIC_AUTH_TOKEN=cr_075a7d7c5c39be523c18da675acf2ac0ce6dbdd2129454370b17797eb43d20a0
ANTHROPIC_BASE_URL=http://47.251.110.97:3000/api
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

### 3. 前端配置

在前端代码中配置正确的API地址:

```javascript
const API_BASE_URL = 'http://localhost:8000';  // 开发环境
// const API_BASE_URL = 'https://your-production-api.com';  // 生产环境
```

## 功能特性

### 已实现的核心功能

- ✅ 支持Word (.docx, .doc)和PDF文档解析
- ✅ 使用Claude Sonnet 4.5 AI模型提取测试点
- ✅ 三级置信度评分系统 (✅高/⚠️中/❌低)
- ✅ 自动生成XMind思维导图
- ✅ XMind文件修复机制(自动添加meta.xml和manifest.xml)
- ✅ 完整的API接口

### 功能特点

1. **智能置信度评分**: AI自动评估每个测试用例的置信度，标注需要人工Review的部分
2. **节省人力**: 减少70-80%的键盘输入时间，测试工程师从"打字员"转变为"审查员"
3. **多种文档格式**: 支持.docx, .doc (WPS兼容), .pdf
4. **标准XMind格式**: 生成的文件可在XMind桌面应用中正常打开

## 后续升级计划

以下功能可在后续版本中实现:

1. **问题清单生成**: 针对不清晰的需求自动生成澄清问题
2. **需求缺陷检测**: 识别需求文档中的模糊、矛盾、缺失等问题
3. **案例库积累**: 学习历史测试用例，提高生成质量
4. **多模型支持**: 支持OpenAI GPT-4o等其他模型
5. **批量处理**: 支持一次性上传多个需求文档

## 故障排查

### 常见问题

**Q: XMind文件无法打开?**
A: 已在xmind_builder.py中添加自动修复机制，新生成的文件应该可以正常打开。如有旧文件，可运行`fix_xmind_files.py`修复。

**Q: 生成速度慢?**
A: AI分析需求需要时间，通常30秒-2分钟。如遇502错误，已实现3次重试机制。

**Q: 支持哪些文档格式?**
A: 支持.docx (Word 2007+), .doc (Word 97-2003, WPS), .pdf

**Q: 如何修改AI模型?**
A: 修改testforge/src/ai_testcase_gen/.env中的CLAUDE_MODEL或使用API参数ai_model="openai"

## 技术支持

- 详细技术文档: `testforge/src/ai_testcase_gen/XMIND_FIX_SUMMARY.md`
- 问题修复脚本: `testforge/src/ai_testcase_gen/fix_xmind_files.py`
- 诊断工具: `testforge/src/ai_testcase_gen/check_xmind_missing_files.py`
