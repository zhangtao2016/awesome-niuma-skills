---
name: code-review-agent
description: 提供自动化代码审核能力，包括静态分析、安全漏洞检测、复杂度分析、测试覆盖率检查和代码重复检测。当用户需要进行代码审核、PR审查、代码质量评估、安全扫描、或检查代码复杂度与测试覆盖率时触发。
---

# 代码审核智能体

## 概述

代码审核智能体（CodeReviewAgent）协调多个专业审核技能，对代码进行全面质量评估，输出评分、问题列表和改进建议。

## 触发场景

- 代码审核、代码审查、code review
- PR审查、pull request review
- 代码质量检查、质量评估
- 安全漏洞扫描、安全检查
- 复杂度分析、圈复杂度检查
- 测试覆盖率分析
- 代码重复检测

## 核心技能

| 技能标识 | 技能名称 | 功能描述 |
|----------|----------|----------|
| static_analysis | 代码静态分析 | 检测语法错误、代码异味、调试输出、TODO标记 |
| security_scan | 安全漏洞检测 | 检测SQL注入、XSS、硬编码密钥等安全风险 |
| complexity_analysis | 代码复杂度分析 | 计算圈复杂度、认知复杂度、嵌套深度 |
| test_coverage | 测试覆盖率检查 | 分析行/分支覆盖率、测试文件质量 |
| duplication_detection | 代码重复检测 | 跨文件检测重复代码块 |

## 使用流程

### 1. 初始化智能体

```python
from code_review_agent import CodeReviewAgent

agent = CodeReviewAgent(name="CodeGuardian", version="2.0")
```

### 2. 准备代码数据

```python
code_data = {
    "code": source_code,           # 必需：源代码字符串
    "language": "python",          # 必需：编程语言
    "file_path": "module.py",      # 可选：文件路径
    "has_tests": True,             # 可选：是否有测试数据
    "coverage_report": {           # 可选：覆盖率数据
        "line_coverage": 85.0,
        "branch_coverage": 72.0
    },
    "test_files": [                # 可选：测试文件列表
        {"name": "test_module.py", "test_cases": ["test_a", "test_b"]}
    ],
    "file_count": 3,               # 可选：相关文件数量（>1时触发重复检测）
    "related_files": ["a.py", "b.py"],           # 可选：相关文件路径
    "related_file_contents": {"a.py": "..."}     # 可选：相关文件内容
}
```

### 3. 执行审核

```python
result = agent.review_code(code_data, context={
    "author": "developer",
    "pr_id": "PR-123",
    "repository": "project"
})
```

### 4. 解析审核结果

```python
results = result["review_results"]

# 总体评分 (0-100)
score = results["overall_score"]

# 审核结论
conclusion = results["conclusion"]
# conclusion["status"]    -> "通过" / "有条件通过" / "需要修改" / "拒绝"
# conclusion["level"]     -> "优秀" / "良好" / "一般" / "较差"
# conclusion["message"]   -> 人类可读结论
# conclusion["requires_changes"] -> bool

# 代码问题列表
issues = results["issues"]

# 安全漏洞列表
vulnerabilities = results["vulnerabilities"]

# 改进建议
recommendations = results["recommendations"]

# 各技能详细结果
static_result = results["static_analysis"]
security_result = results["security_scan"]
complexity_result = results["complexity_analysis"]
test_result = results.get("test_coverage")
dup_result = results.get("duplication_detection")

# 文本报告
report = result["report"]
```

## 评分标准

| 分数 | 状态 | 级别 | 说明 |
|------|------|------|------|
| ≥90 | 通过 | 优秀 | 代码质量优秀，可以直接合并 |
| 80-89 | 有条件通过 | 良好 | 无安全漏洞时可合并，建议修复小问题 |
| 60-79 | 需要修改 | 一般 | 存在需修复的问题 |
| <60 | 拒绝 | 较差 | 存在严重问题，需要重构 |

## 扣分规则

- **静态分析问题**：critical -10, warning -5, info -1
- **安全漏洞未通过**：-20
- **复杂度过高**（high级别）：-15
- **测试覆盖率不足**（overall_score < 80）：-10
- **代码重复率过高**（>10%）：-5

## 单技能调用

如需单独使用某个技能：

```python
# 获取技能实例
skill = agent.skills["static_analysis"]

# 执行
result = skill.execute({
    "code": source_code,
    "language": "python",
    "file_path": "test.py"
})
```

## 智能体统计

```python
stats = agent.get_stats()
# stats["total_reviews"]     -> 总审核次数
# stats["average_score"]     -> 平均评分
# stats["skills_available"]  -> 可用技能数量
```

## 参考文档

- 完整类定义与实现细节见 [reference.md](reference.md)
- 详细使用示例见 [examples.md](examples.md)
