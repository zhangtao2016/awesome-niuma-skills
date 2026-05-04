# 代码审核智能体 - 使用示例

## 示例1：简单代码审核

```python
from code_review_agent import CodeReviewAgent

# 创建智能体
agent = CodeReviewAgent(name="CodeGuardian", version="2.0")

# 准备代码
sample_code = '''
def calculate_total(items, discount=0):
    total = 0
    for item in items:
        if item['price'] > 100:
            total += item['price'] * 0.9
        else:
            total += item['price']

    # TODO: 这里需要处理折扣逻辑
    if discount > 0:
        total = total * (1 - discount/100)

    print(f"总计: {total}")
    return total

# 硬编码的API密钥
api_key = "sk_1234567890abcdef"
'''

# 准备审核数据
code_data = {
    "code": sample_code,
    "language": "python",
    "file_path": "calculator.py",
    "has_tests": False,
    "file_count": 1
}

# 执行审核
result = agent.review_code(code_data, context={
    "author": "developer123",
    "pr_id": "PR-456",
    "repository": "example-project"
})

# 输出摘要
print(f"总体评分: {result['review_results']['overall_score']}/100")
print(f"结论: {result['review_results']['conclusion']['status']}")
print(f"问题数量: {len(result['review_results']['issues'])}")
print("\n详细报告:")
print(result["report"])

# 输出统计
stats = agent.get_stats()
print(f"已执行 {stats['total_reviews']} 次审核，平均评分 {stats['average_score']}")
```

**预期输出要点：**
- 检测到 `TODO` 标记（info级别）
- 检测到 `print()` 调试输出（warning级别）
- 检测到硬编码密钥（critical级别安全漏洞）
- 总体评分被安全漏洞大幅扣减

---

## 示例2：复杂多文件审核（含测试和重复检测）

```python
agent = CodeReviewAgent()

complex_code = '''
def process_user_input(user_input):
    # 潜在SQL注入风险
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    result = db.execute(query)

    # 多重嵌套，复杂度高
    if result:
        for row in result:
            if row['status'] == 'active':
                if row['balance'] > 1000:
                    if row['level'] == 'premium':
                        return "高级用户"
                    else:
                        return "普通用户"
    return "未找到"
'''

code_data = {
    "code": complex_code,
    "language": "python",
    "file_path": "user_processor.py",
    "has_tests": True,
    "coverage_report": {"line_coverage": 65, "branch_coverage": 50},
    "test_files": [
        {"name": "test_user.py", "test_cases": ["test_basic"]}
    ],
    "file_count": 3,
    "related_files": ["user_processor.py", "auth.py", "utils.py"],
    "related_file_contents": {
        "user_processor.py": "def process(): pass",
        "auth.py": "def auth(): pass",
        "utils.py": "def process(): pass"
    }
}

result = agent.review_code(code_data)

# 查看各技能结果
for key, value in result["review_results"].items():
    if isinstance(value, dict) and "skill_name" in value:
        skill_name = value["skill_name"]
        if "score" in value:
            print(f"{skill_name}: {value['score']}/100")
        elif "security_score" in value:
            print(f"{skill_name}: {value['security_score']}/100")
        elif "complexity_level" in value:
            print(f"{skill_name}: {value['complexity_level']}")
        elif "duplicate_rate" in value:
            print(f"{skill_name}: {value['duplicate_rate']:.2%}")
```

**预期输出要点：**
- 安全扫描：检测到SQL注入（critical），安全评分大幅下降
- 复杂度分析：嵌套层次深，复杂度级别为 high
- 测试覆盖：行覆盖率65%不足，测试用例过少
- 重复检测：`user_processor.py` 和 `utils.py` 存在重复函数
- 总体评分较低，结论为"拒绝"或"需要修改"

---

## 示例3：测试单个技能

```python
agent = CodeReviewAgent()

# 单独测试静态分析
static_skill = agent.skills["static_analysis"]
static_result = static_skill.execute({
    "code": "def test(): print('hello')",
    "language": "python",
    "file_path": "test.py"
})
print(f"静态分析: 发现 {len(static_result.get('issues', []))} 个问题")

# 单独测试安全扫描
security_skill = agent.skills["security_scan"]
security_result = security_skill.execute({
    "code": "api_key = 'secret123'",
    "language": "python",
    "file_path": "config.py"
})
print(f"安全扫描: {'通过' if security_result['passed'] else '未通过'}")
print(f"漏洞数: {len(security_result['vulnerabilities'])}")

# 单独测试复杂度分析
complexity_skill = agent.skills["complexity_analysis"]
complexity_result = complexity_skill.execute({
    "code": "def foo():\n    if True:\n        for i in range(10):\n            if i > 5:\n                return i"
})
print(f"圈复杂度: {complexity_result['cyclomatic_complexity']}")
print(f"认知复杂度: {complexity_result['cognitive_complexity']}")
print(f"复杂度级别: {complexity_result['complexity_level']}")
```

---

## 示例4：批量审核多个文件

```python
agent = CodeReviewAgent(name="BatchReviewer")

files_to_review = [
    {"path": "models.py", "code": "...", "lang": "python"},
    {"path": "views.py", "code": "...", "lang": "python"},
    {"path": "utils.py", "code": "...", "lang": "python"},
]

for file_info in files_to_review:
    result = agent.review_code({
        "code": file_info["code"],
        "language": file_info["lang"],
        "file_path": file_info["path"],
        "file_count": len(files_to_review)
    })
    print(f"{file_info['path']}: {result['review_results']['overall_score']}分 - "
          f"{result['review_results']['conclusion']['status']}")

# 最终统计
stats = agent.get_stats()
print(f"\n批量审核完成: {stats['total_reviews']} 个文件, 平均 {stats['average_score']} 分")
```
