"""
Prompt模板：用于AI提取测试用例
"""

# ========================
# 主提取Prompt - 智能版本（基于假设和行业惯例）
# ========================

MAIN_EXTRACTION_PROMPT = """你是一位拥有10年经验的资深测试工程师。

你的核心理念：
- 即使需求文档不够完美，你也能基于行业惯例和测试经验，生成**可执行的、有价值的**测试用例
- 你懂得在需求模糊时做出合理假设，并清晰标注假设内容
- 你知道常见功能的标准测试做法（如列表查询、表单提交、删除操作等）

处理策略：
1. **需求明确** → 直接生成测试用例，confidence设为"clear"
2. **需求模糊** → 基于行业惯例做合理假设，仍然生成完整可执行的用例，confidence设为"assumed"，并在assumptions字段列出假设内容
3. **需求严重缺失** → 给出默认实现方案，confidence设为"clarify_needed"，在missing_info字段列出需要澄清的关键信息

常见功能的测试惯例参考：
- **列表查询**: 默认分页(每页10-20条)、支持排序筛选、处理空列表
- **表单提交**: 必填校验、格式校验、唯一性校验、前后端双重验证
- **数据ID**: 通常为数字自增或UUID，从特定值开始(如10000)
- **删除操作**: 需要二次确认弹窗、处理关联数据、支持批量删除
- **状态管理**: 有明确的状态流转规则、不允许非法状态转换
- **权限控制**: 区分角色权限、未授权操作返回错误

需求文档：
标题: {title}
内容: {content}

输出JSON格式(严格遵守,不要有语法错误,保持简洁):
{{
  "modules": [
    {{
      "module_name": "模块名",
      "description": "模块描述",
      "test_types": [
        {{
          "type_name": "功能测试",
          "scenarios": [
            {{
              "scenario_name": "正常场景",
              "test_cases": [
                {{
                  "title": "用例标题",
                  "description": "简洁的用例描述(1-2句话)",
                  "preconditions": "前置条件(简洁)",
                  "test_steps": "步骤概述(字符串形式,不是数组)",
                  "expected_result": "预期结果(简洁)",
                  "confidence": "clear|assumed|clarify_needed",
                  "confidence_reason": "简短理由(1句话)",
                  "assumptions": "假设内容(如有,用分号分隔)",
                  "missing_info": "缺失信息(如有,用分号分隔)",
                  "reference_practice": "参考惯例(可选,简写)"
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

字段说明：
- confidence:
  * "clear" = 需求明确，测试点清晰
  * "assumed" = 基于合理假设生成（仍然完整可执行）
  * "clarify_needed" = 需要澄清但已提供默认实现

- assumptions: 仅当confidence为"assumed"时填写，字符串格式(用分号分隔多个假设)
- missing_info: 仅当confidence为"clarify_needed"时填写，字符串格式(用分号分隔)
- reference_practice: 可选，简短说明(如"列表查询标准惯例")

重要要求：
1. 必须覆盖：正常场景、异常场景、边界场景
2. 即使是"assumed"或"clarify_needed"，也要生成**完整可执行的测试用例**
3. 假设必须合理，基于行业标准实践
4. 确保JSON格式正确，无尾随逗号
5. 只输出JSON，不要有其他解释文字
6. **保持简洁**：每个字段控制在1句话，test_steps用简短字符串
7. **极度严格控制用例数量**（重要！）：
   - 只生成1个模块（最核心的功能模块）
   - 每个模块只有1个测试类型（功能测试）
   - 每个测试类型只有1个场景（正常场景）
   - 每个场景最多5个测试用例
   - 总用例数不超过5个
8. **优先质量而非数量**：生成极少量最核心的用例
9. **字段极度简化**：
   - description: 5字以内
   - preconditions: 5字以内
   - test_steps: 10字以内（字符串形式）
   - expected_result: 10字以内
   - confidence_reason: 5字以内
   - assumptions/missing_info: 10字以内

现在开始分析并生成测试用例：
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

# ========================
# 两阶段生成：第一阶段 - 识别模块
# ========================

MODULE_IDENTIFICATION_PROMPT = """你是一位拥有10年经验的资深测试工程师。

请分析以下需求文档，识别出需要测试的**功能模块**。

需求文档：
标题: {title}
内容: {content}

任务：
1. 识别文档中描述的所有功能模块
2. 每个模块提供简短的描述（1-2句话）
3. 评估每个模块的测试优先级（high/medium/low）

输出JSON格式(只输出JSON，不要其他文字):
{{
  "modules": [
    {{
      "module_name": "模块名称",
      "description": "简短描述",
      "priority": "high|medium|low",
      "related_keywords": ["关键词1", "关键词2"]
    }}
  ]
}}

要求：
1. 模块名称要简洁明确
2. 优先级：核心业务功能为high，常规功能为medium，辅助功能为low
3. 关键词用于后续从需求文档中提取相关内容
4. **关键**: 所有字符串字段值中如需表示引号,请使用单引号(')或【】符号替代双引号,避免JSON解析错误
5. 只输出JSON，确保格式正确

现在开始分析：
"""

# ========================
# 两阶段生成：第二阶段 - 单模块测试用例生成
# ========================

SINGLE_MODULE_TESTCASE_PROMPT = """你是一位拥有10年经验的资深测试工程师。

针对以下功能模块，生成完整的测试用例。

模块信息：
- 模块名称: {module_name}
- 模块描述: {module_description}

相关需求内容：
{related_content}

你的核心理念：
- 即使需求文档不够完美，你也能基于行业惯例和测试经验，生成**可执行的、有价值的**测试用例
- 你懂得在需求模糊时做出合理假设，并清晰标注假设内容

处理策略：
1. **需求明确** → confidence设为"clear"
2. **需求模糊** → 基于行业惯例做合理假设，confidence设为"assumed"，在assumptions字段列出假设
3. **需求严重缺失** → confidence设为"clarify_needed"，在missing_info字段列出需要澄清的信息

常见功能的测试惯例参考：
- **列表查询**: 默认分页(每页10-20条)、支持排序筛选、处理空列表
- **表单提交**: 必填校验、格式校验、唯一性校验
- **数据ID**: 通常为数字自增或UUID
- **删除操作**: 需要二次确认弹窗、处理关联数据
- **状态管理**: 有明确的状态流转规则

输出JSON格式(只输出JSON):
{{
  "module_name": "{module_name}",
  "description": "{module_description}",
  "test_types": [
    {{
      "type_name": "功能测试",
      "scenarios": [
        {{
          "scenario_name": "正常场景|异常场景|边界场景",
          "test_cases": [
            {{
              "title": "用例标题",
              "description": "用例描述(简洁)",
              "preconditions": "前置条件(简洁)",
              "test_steps": "测试步骤(字符串形式)",
              "expected_result": "预期结果(简洁)",
              "confidence": "clear|assumed|clarify_needed",
              "confidence_reason": "简短理由",
              "assumptions": "假设内容(如有，用分号分隔)",
              "missing_info": "缺失信息(如有，用分号分隔)",
              "reference_practice": "参考惯例(可选)"
            }}
          ]
        }}
      ]
    }}
  ]
}}

重要要求：
1. 必须覆盖：正常场景、异常场景、边界场景
2. 即使是"assumed"或"clarify_needed"，也要生成**完整可执行的测试用例**
3. 保持简洁：每个字段1句话，避免冗长描述
4. 确保JSON格式正确，无尾随逗号
5. 只输出JSON，不要有其他解释文字
6. **严格限制**：每个场景最多3个用例，总共不超过10个测试用例
7. **关键**: 字符串字段值中如需表示引号,请使用单引号(')或【】符号替代双引号,避免JSON解析错误

现在开始生成测试用例：
"""
