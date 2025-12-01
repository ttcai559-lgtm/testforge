"""
Prompt模板：用于AI提取测试用例
"""

# ========================
# 主提取Prompt
# ========================

MAIN_EXTRACTION_PROMPT = """分析需求文档,生成测试用例JSON。

需求: {title}
{content}

输出JSON格式(严格遵守,不要有语法错误):
{{
  "modules": [
    {{
      "module_name": "模块名",
      "description": "描述",
      "test_types": [
        {{
          "type_name": "功能测试",
          "scenarios": [
            {{
              "scenario_name": "正常场景",
              "test_cases": [
                {{
                  "title": "用例标题",
                  "description": "描述",
                  "preconditions": "前置条件",
                  "test_steps": ["步骤1","步骤2"],
                  "expected_result": "预期结果",
                  "confidence": "high",
                  "confidence_reason": "原因"
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  ],
  "questions": [],
  "defects": []
}}

要求:
1. 覆盖正常/异常/边界场景
2. confidence: high(清晰)/medium(部分清晰)/low(模糊)
3. 确保JSON格式正确,无尾随逗号
4. 只输出JSON,不要解释

开始:
"""

# ========================
# 置信度评估Prompt
# ========================

CONFIDENCE_EVALUATION_PROMPT = """请评估以下测试用例的置信度。

# 测试用例
标题：{case_title}
描述：{case_description}

# 对应的需求描述
{requirement_text}

# 评估标准
- **high**：需求清晰，测试点明确，有具体验收标准
- **medium**：需求有描述但细节不清晰
- **low**：需求模糊或缺失关键信息

请输出JSON格式：
```json
{{
  "confidence": "high|medium|low",
  "reason": "评估理由",
  "missing_info": ["缺失的信息1", "缺失的信息2"]
}}
```
"""

# ========================
# 需求缺陷检测Prompt
# ========================

DEFECT_DETECTION_PROMPT = """请检查以下需求文档中的潜在缺陷。

# 需求文档
{content}

# 检测维度
1. **模糊性**：描述不清晰、有歧义的地方
2. **矛盾性**：前后逻辑冲突、不一致的地方
3. **完整性**：缺少验收标准、边界条件、异常处理等
4. **合理性**：业务逻辑不合理或技术上不可行

请输出JSON格式：
```json
{{
  "defects": [
    {{
      "location": "具体位置（章节/段落）",
      "type": "模糊/矛盾/缺失/不合理",
      "description": "缺陷描述",
      "severity": "high|medium|low",
      "suggestion": "修改建议"
    }}
  ]
}}
```
"""

# ========================
# 问题清单生成Prompt
# ========================

QUESTION_GENERATION_PROMPT = """请针对以下需求文档生成需要澄清的问题清单。

# 需求文档
{content}

# 问题类型
1. **模糊点澄清**：需要明确具体数值、范围、标准的地方
2. **缺失信息**：需要补充的必要信息
3. **矛盾确认**：需要确认哪个描述是正确的
4. **业务逻辑确认**：需要确认业务流程或规则

请输出JSON格式：
```json
{{
  "questions": [
    {{
      "location": "需求位置",
      "question": "具体问题",
      "type": "模糊点澄清|缺失信息|矛盾确认|业务逻辑确认",
      "priority": "high|medium|low",
      "reason": "为什么需要澄清"
    }}
  ]
}}
```

优先级判断：
- **high**：阻塞性问题，不澄清无法进行测试
- **medium**：重要但可以暂时假设的问题
- **low**：优化性问题，不影响基本测试
"""

# ========================
# 案例库匹配Prompt
# ========================

CASE_MATCHING_PROMPT = """请判断以下新需求是否与历史测试用例相似。

# 新需求
{new_requirement}

# 历史测试用例
模块：{historical_module}
场景：{historical_scenario}
用例：{historical_cases}

# 判断标准
1. 功能相似度：是否同类型功能
2. 业务逻辑相似度：业务流程是否相似
3. 可复用程度：历史用例是否可直接复用或稍作修改

请输出JSON格式：
```json
{{
  "is_similar": true|false,
  "similarity_score": 0.0-1.0,
  "reason": "判断理由",
  "reusable_cases": ["可复用的用例ID"],
  "modification_suggestions": "如需修改，如何修改"
}}
```
"""

# ========================
# XMind结构优化Prompt
# ========================

XMIND_STRUCTURE_PROMPT = """请优化以下测试用例的思维导图结构。

# 当前测试用例
{test_cases}

# 优化目标
1. 合理分组：相似的测试用例归为一类
2. 层次清晰：功能模块 → 测试类型 → 场景 → 用例
3. 覆盖完整：确保正常、异常、边界场景都有覆盖

请输出优化后的JSON结构（与主提取Prompt相同格式）。
"""
