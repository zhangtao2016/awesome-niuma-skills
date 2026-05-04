# 代码审核智能体 - 完整参考

## Skill 基类

```python
class Skill:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def execute(self, input_data):
        raise NotImplementedError("子类必须实现execute方法")

    def validate_input(self, input_data):
        return isinstance(input_data, dict)
```

---

## 1. StaticAnalysisSkill（代码静态分析）

```python
class StaticAnalysisSkill(Skill):
    def __init__(self):
        super().__init__(
            name="代码静态分析",
            description="对代码进行静态分析，检测语法错误、潜在问题和代码异味"
        )
        self.rules = {
            "complexity": {"max_cyclomatic": 10, "max_nesting": 4},
            "style": {"max_line_length": 120, "naming_convention": "snake_case"},
            "security": ["sql_injection", "xss", "hardcoded_secrets"]
        }

    def execute(self, code_data):
        if not self.validate_input(code_data):
            return {"error": "输入格式不正确"}

        code = code_data.get("code", "")
        language = code_data.get("language", "python")
        file_path = code_data.get("file_path", "")

        analysis_results = {
            "file": file_path,
            "language": language,
            "issues": [],
            "metrics": {},
            "score": 100
        }

        issues = self._analyze_code(code, language)
        metrics = self._calculate_metrics(code, language)

        for issue in issues:
            if issue["severity"] == "critical":
                analysis_results["score"] -= 10
            elif issue["severity"] == "warning":
                analysis_results["score"] -= 5
            else:
                analysis_results["score"] -= 1

        analysis_results["issues"] = issues
        analysis_results["metrics"] = metrics
        return analysis_results

    def _analyze_code(self, code, language):
        issues = []

        if "TODO" in code or "FIXME" in code:
            issues.append({
                "type": "todo_found",
                "severity": "info",
                "message": "代码中包含待办事项标记",
                "line": self._find_line_number(code, "TODO")
            })

        if "print(" in code and language == "python":
            issues.append({
                "type": "debug_print",
                "severity": "warning",
                "message": "生产代码中可能存在调试输出",
                "suggestion": "使用日志库替代print语句"
            })

        lines = code.split('\n')
        if len(lines) > 100:
            issues.append({
                "type": "function_too_long",
                "severity": "warning",
                "message": f"函数过长 ({len(lines)} 行)",
                "suggestion": "考虑将函数拆分为更小的单一职责函数"
            })

        return issues

    def _calculate_metrics(self, code, language):
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        return {
            "line_count": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "comment_ratio": self._calculate_comment_ratio(code, language),
            "complexity": "medium"
        }

    def _calculate_comment_ratio(self, code, language):
        lines = code.split('\n')
        comment_lines = sum(
            1 for line in lines
            if line.strip().startswith('#') or line.strip().startswith('//')
        )
        return comment_lines / len(lines) if lines else 0

    def _find_line_number(self, code, text):
        for i, line in enumerate(code.split('\n'), 1):
            if text in line:
                return i
        return 0
```

---

## 2. SecurityScanSkill（安全漏洞检测）

```python
class SecurityScanSkill(Skill):
    def __init__(self):
        super().__init__(
            name="安全漏洞检测",
            description="检测代码中的安全漏洞和潜在风险"
        )
        self.vulnerability_patterns = {
            "sql_injection": [r"execute\(.*\+.*\)", r"query\(.*\+.*\)"],
            "xss": [r"innerHTML.*=.*\+", r"document\.write\("],
            "hardcoded_secret": [
                r"password\s*=\s*['\"].*['\"]",
                r"api_key\s*=\s*['\"].*['\"]"
            ]
        }

    def execute(self, code_data):
        code = code_data.get("code", "")
        language = code_data.get("language", "python")
        vulnerabilities = []

        if self._check_pattern(code, "sql_injection"):
            vulnerabilities.append({
                "type": "sql_injection",
                "severity": "critical",
                "description": "检测到可能的SQL注入漏洞",
                "recommendation": "使用参数化查询或ORM的安全方法"
            })

        if self._check_pattern(code, "hardcoded_secret"):
            vulnerabilities.append({
                "type": "hardcoded_secret",
                "severity": "high",
                "description": "检测到硬编码的敏感信息",
                "recommendation": "将密钥移至环境变量或配置管理服务"
            })

        if language in ["javascript", "typescript"] and self._check_pattern(code, "xss"):
            vulnerabilities.append({
                "type": "xss",
                "severity": "high",
                "description": "检测到可能的跨站脚本攻击漏洞",
                "recommendation": "对用户输入进行转义或使用安全的DOM操作API"
            })

        return {
            "file": code_data.get("file_path", ""),
            "vulnerabilities": vulnerabilities,
            "security_score": 100 - len(vulnerabilities) * 20,
            "passed": len(vulnerabilities) == 0
        }

    def _check_pattern(self, code, pattern_type):
        import re
        patterns = self.vulnerability_patterns.get(pattern_type, [])
        return any(re.search(p, code, re.IGNORECASE) for p in patterns)
```

---

## 3. ComplexityAnalysisSkill（代码复杂度分析）

```python
class ComplexityAnalysisSkill(Skill):
    def __init__(self):
        super().__init__(
            name="代码复杂度分析",
            description="分析代码的圈复杂度和认知复杂度"
        )

    def execute(self, code_data):
        code = code_data.get("code", "")
        cyclomatic = self._calculate_cyclomatic_complexity(code)
        cognitive = self._estimate_cognitive_complexity(code)

        complexity_level = "low"
        if cyclomatic > 20 or cognitive > 30:
            complexity_level = "high"
        elif cyclomatic > 10 or cognitive > 15:
            complexity_level = "medium"

        suggestions = []
        if complexity_level == "high":
            suggestions.append("函数过于复杂，建议拆分为多个小函数")
        if self._count_nesting(code) > 4:
            suggestions.append("嵌套层次过深，考虑使用提前返回或策略模式")

        return {
            "cyclomatic_complexity": cyclomatic,
            "cognitive_complexity": cognitive,
            "complexity_level": complexity_level,
            "max_nesting": self._count_nesting(code),
            "suggestions": suggestions
        }

    def _calculate_cyclomatic_complexity(self, code):
        complexity = 1
        decision_points = ["if ", "elif ", "else:", "for ", "while ", "and ", "or ", "case "]
        for line in code.split('\n'):
            for keyword in decision_points:
                if keyword in line and not line.strip().startswith('#'):
                    complexity += 1
                    break
        return complexity

    def _estimate_cognitive_complexity(self, code):
        cognitive = 0
        for line in code.split('\n'):
            clean = line.strip()
            if clean.startswith(("if ", "for ", "while ", "try:")):
                cognitive += 2
            elif "and " in clean or "or " in clean:
                cognitive += 1
            elif "except " in clean:
                cognitive += 2
            elif "lambda " in clean:
                cognitive += 1
        return cognitive

    def _count_nesting(self, code):
        max_depth = 0
        for line in code.split('\n'):
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                max_depth = max(max_depth, indent // 4)
        return max_depth
```

---

## 4. TestCoverageSkill（测试覆盖率检查）

```python
class TestCoverageSkill(Skill):
    def __init__(self):
        super().__init__(
            name="测试覆盖率检查",
            description="检查代码的测试覆盖率和测试质量"
        )

    def execute(self, test_data):
        coverage_data = test_data.get("coverage_report", {})
        test_files = test_data.get("test_files", [])
        line_coverage = coverage_data.get("line_coverage", 0.0)
        branch_coverage = coverage_data.get("branch_coverage", 0.0)

        recommendations = []
        if line_coverage < 80:
            recommendations.append(f"行覆盖率较低 ({line_coverage}%)，建议增加单元测试")
        if branch_coverage < 70:
            recommendations.append(f"分支覆盖率较低 ({branch_coverage}%)，建议增加边界条件测试")

        test_quality = self._analyze_test_quality(test_files)

        return {
            "line_coverage": line_coverage,
            "branch_coverage": branch_coverage,
            "test_count": len(test_files),
            "test_quality_score": test_quality["score"],
            "test_issues": test_quality["issues"],
            "recommendations": recommendations,
            "overall_score": (line_coverage + branch_coverage + test_quality["score"]) / 3
        }

    def _analyze_test_quality(self, test_files):
        issues = []
        score = 100
        for test_file in test_files:
            if len(test_file.get("test_cases", [])) < 3:
                issues.append(f"测试文件 {test_file.get('name')} 包含的测试用例过少")
                score -= 10
        return {"score": max(score, 0), "issues": issues}
```

---

## 5. DuplicationDetectionSkill（代码重复检测）

```python
class DuplicationDetectionSkill(Skill):
    def __init__(self):
        super().__init__(
            name="代码重复检测",
            description="检测重复的代码块，建议提取为函数或工具类"
        )
        self.min_duplicate_lines = 5

    def execute(self, codebase_data):
        files = codebase_data.get("files", [])
        file_contents = codebase_data.get("file_contents", {})
        duplicates = []

        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                if file1 != file2:
                    blocks = self._find_duplicate_blocks(
                        file_contents.get(file1, ""),
                        file_contents.get(file2, "")
                    )
                    if blocks:
                        duplicates.append({
                            "file1": file1,
                            "file2": file2,
                            "duplicate_blocks": blocks,
                            "total_duplicate_lines": sum(len(b) for b in blocks)
                        })

        duplicate_rate = self._calculate_duplicate_rate(duplicates, file_contents)
        return {
            "duplicate_pairs": duplicates,
            "duplicate_rate": duplicate_rate,
            "suggestion": "考虑将重复代码提取为公共函数或工具类" if duplicate_rate > 0.1 else None
        }

    def _find_duplicate_blocks(self, content1, content2):
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')
        duplicate_blocks = []
        for i in range(len(lines1) - self.min_duplicate_lines + 1):
            for j in range(len(lines2) - self.min_duplicate_lines + 1):
                if lines1[i:i+self.min_duplicate_lines] == lines2[j:j+self.min_duplicate_lines]:
                    duplicate_blocks.append(lines1[i:i+self.min_duplicate_lines])
        return duplicate_blocks

    def _calculate_duplicate_rate(self, duplicates, file_contents):
        total_lines = sum(len(c.split('\n')) for c in file_contents.values())
        duplicate_lines = sum(p["total_duplicate_lines"] for p in duplicates)
        return duplicate_lines / total_lines if total_lines > 0 else 0
```

---

## CodeReviewAgent（代码审核智能体）

```python
class CodeReviewAgent:
    def __init__(self, name="CodeReviewBot", version="1.0"):
        self.name = name
        self.version = version
        self.skills = {}
        self.memory = {
            "review_history": [],
            "project_stats": {},
            "rule_violations": {}
        }
        self.config = {
            "strict_mode": False,
            "auto_approve_threshold": 90,
            "notify_on_critical": True
        }
        self._initialize_skills()

    def _initialize_skills(self):
        self.skills = {
            "static_analysis": StaticAnalysisSkill(),
            "security_scan": SecurityScanSkill(),
            "complexity_analysis": ComplexityAnalysisSkill(),
            "test_coverage": TestCoverageSkill(),
            "duplication_detection": DuplicationDetectionSkill()
        }

    def review_code(self, code_data, context=None):
        if not self._validate_code_data(code_data):
            return {"error": "无效的代码数据"}

        self.current_context = context or {}
        review_results = {
            "overall_score": 100,
            "issues": [],
            "vulnerabilities": [],
            "recommendations": [],
            "skills_used": []
        }

        # 1. 静态分析
        static_result = self._use_skill("static_analysis", code_data)
        review_results["static_analysis"] = static_result
        review_results["overall_score"] = min(
            review_results["overall_score"],
            static_result.get("score", 100)
        )
        review_results["issues"].extend(static_result.get("issues", []))

        # 2. 安全扫描
        security_result = self._use_skill("security_scan", code_data)
        review_results["security_scan"] = security_result
        if not security_result.get("passed", True):
            review_results["overall_score"] -= 20
            review_results["vulnerabilities"].extend(
                security_result.get("vulnerabilities", [])
            )

        # 3. 复杂度分析
        complexity_result = self._use_skill("complexity_analysis", code_data)
        review_results["complexity_analysis"] = complexity_result
        if complexity_result.get("complexity_level") == "high":
            review_results["overall_score"] -= 15
            review_results["recommendations"].extend(
                complexity_result.get("suggestions", [])
            )

        # 4. 测试覆盖率（如有测试数据）
        if code_data.get("has_tests", False):
            test_result = self._use_skill("test_coverage", {
                "coverage_report": code_data.get("coverage_report", {}),
                "test_files": code_data.get("test_files", [])
            })
            review_results["test_coverage"] = test_result
            if test_result.get("overall_score", 100) < 80:
                review_results["overall_score"] -= 10
                review_results["recommendations"].append("测试覆盖率不足，建议增加测试")

        # 5. 代码重复（多文件时）
        if code_data.get("file_count", 1) > 1:
            dup_result = self._use_skill("duplication_detection", {
                "files": code_data.get("related_files", []),
                "file_contents": code_data.get("related_file_contents", {})
            })
            review_results["duplication_detection"] = dup_result
            if dup_result.get("duplicate_rate", 0) > 0.1:
                review_results["overall_score"] -= 5

        review_results["conclusion"] = self._generate_conclusion(review_results)
        self._record_review(review_results)
        report = self._generate_report(review_results)

        return {
            "agent": self.name,
            "timestamp": self._get_timestamp(),
            "review_results": review_results,
            "report": report
        }

    def _use_skill(self, skill_name, input_data):
        if skill_name not in self.skills:
            return {"error": f"技能 '{skill_name}' 不存在"}
        skill = self.skills[skill_name]
        try:
            result = skill.execute(input_data)
            result["skill_name"] = skill.name
            return result
        except Exception as e:
            return {"error": f"技能执行失败: {str(e)}"}

    def _validate_code_data(self, code_data):
        required_fields = ["code", "language"]
        for field in required_fields:
            if field not in code_data:
                return False
        return True

    def _generate_conclusion(self, review_results):
        score = review_results["overall_score"]
        if score >= 90:
            return {"status": "通过", "level": "优秀",
                    "message": "代码质量优秀，可以合并", "requires_changes": False}
        elif score >= 80:
            return {"status": "有条件通过", "level": "良好",
                    "message": "代码质量良好，建议修复部分问题后合并",
                    "requires_changes": len(review_results["vulnerabilities"]) == 0}
        elif score >= 60:
            return {"status": "需要修改", "level": "一般",
                    "message": "代码质量一般，需要修复发现的问题", "requires_changes": True}
        else:
            return {"status": "拒绝", "level": "较差",
                    "message": "代码质量较差，存在严重问题，需要重构", "requires_changes": True}

    def _generate_report(self, review_results):
        conclusion = review_results["conclusion"]
        report = f"""代码审核报告
{'='*50}
总体评分: {review_results['overall_score']}/100
审核结论: {conclusion['status']} ({conclusion['level']})
{conclusion['message']}
"""
        if review_results.get("vulnerabilities"):
            report += "\n安全问题:\n"
            for v in review_results["vulnerabilities"]:
                report += f"  - [{v.get('severity','未知').upper()}] {v.get('description','')}\n"
                report += f"    建议: {v.get('recommendation','')}\n"
        if review_results.get("issues"):
            report += "\n代码问题:\n"
            for i in review_results["issues"]:
                report += f"  - [{i.get('severity','信息')}] {i.get('message','')}\n"
                if i.get('suggestion'):
                    report += f"    建议: {i.get('suggestion')}\n"
        if review_results.get("recommendations"):
            report += "\n改进建议:\n"
            for r in review_results["recommendations"]:
                report += f"  - {r}\n"
        return report

    def _record_review(self, review_results):
        self.memory["review_history"].append({
            "timestamp": self._get_timestamp(),
            "score": review_results["overall_score"],
            "issue_count": len(review_results["issues"]) + len(review_results["vulnerabilities"]),
            "conclusion": review_results["conclusion"]["status"]
        })
        if len(self.memory["review_history"]) > 100:
            self.memory["review_history"].pop(0)

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_stats(self):
        total = len(self.memory["review_history"])
        if total == 0:
            return {"total_reviews": 0, "average_score": 0, "skills_available": len(self.skills)}
        avg_score = sum(r["score"] for r in self.memory["review_history"]) / total
        return {
            "total_reviews": total,
            "average_score": round(avg_score, 2),
            "skills_available": len(self.skills)
        }
```
