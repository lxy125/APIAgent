"""
LLM Prompt 模板
"""
from typing import Dict, Any


# Semantic Analyzer Prompts
SEMANTIC_ANALYSIS_PROMPT = """
You are an expert API analyst. Your task is to analyze the given API interaction and extract key information.

Input:
{input}

Please provide:
1. HTTP method and endpoint
2. Request structure and parameters
3. Response structure and status
4. Error type and classification
5. Key fields and their values

Format as JSON.
"""

ERROR_CLASSIFICATION_PROMPT = """
Classify the following error:

Error Details:
{error_details}

Status Code: {status_code}

Please classify by:
1. Error category (http_error, business_error, validation_error, auth_error, etc.)
2. Severity (critical, high, medium, low)
3. Affected components

Format as JSON.
"""

# Root Cause Strategist Prompts
ROOT_CAUSE_ANALYSIS_PROMPT = """
Analyze the root cause of the following issue:

API Interaction:
{api_interaction}

Error Information:
- Category: {error_category}
- Severity: {error_severity}
- Message: {error_message}

Please analyze and provide:
1. Root cause category (code_bug, configuration_error, dependency_issue, etc.)
2. Detailed description
3. Possible causes (ordered by likelihood)
4. Affected components
5. Related system components
6. Correlation chain

Think step by step and be thorough.
"""

FIX_STRATEGY_PROMPT = """
Based on the root cause analysis, generate a comprehensive fix strategy:

Root Cause Analysis:
{root_cause_analysis}

Please provide:
1. Fix priority (immediate, urgent, normal, low, deprecated)
2. Detailed fix suggestions
3. Specific code changes
4. Configuration changes
5. Estimated effort
6. Risk level (low, medium, high)
7. Validation steps
8. Rollback plan

Format with clear sections.
"""

# Test Case Generator Prompts
TEST_CASE_GENERATION_PROMPT = """
Generate comprehensive test cases for the following scenario:

Bug Report:
{bug_report}

API Details:
- Endpoint: {endpoint}
- Method: {method}
- Error: {error}

Please generate:
1. Positive test cases (happy paths)
2. Negative test cases (error scenarios)
3. Edge cases (boundary conditions)

For each test case, provide:
- Test name
- Description
- Request details
- Expected response or error
- Priority
- Tags

Format as structured test cases.
"""

REGRESSION_STRATEGY_PROMPT = """
Generate a regression testing strategy:

Affected Components:
{affected_components}

Fix Details:
{fix_details}

Please identify:
1. Related endpoints that need regression testing
2. Integration points to test
3. Priority order
4. Test suite structure

Provide a comprehensive regression plan.
"""

# Supervisor Prompts
INPUT_DETECTION_PROMPT = """
Analyze the following input and determine its type:

Input: {input}

Possible types:
- raw_error: Raw error message or stack trace
- request_response: HTTP request/response pair
- log_fragment: Log file fragment
- api_documentation: API documentation
- natural_language: Natural language description
- openapi_spec: OpenAPI/Swagger specification

Return the most appropriate type.
"""

REPORT_GENERATION_PROMPT = """
Generate a comprehensive diagnostic report:

Semantic Analysis:
{semantic_analysis}

Root Cause Analysis:
{root_cause_analysis}

Fix Strategy:
{fix_strategy}

Test Cases:
{test_cases}

Please generate:
1. Executive summary
2. Detailed findings
3. Actionable recommendations
4. Risk assessment
5. Next steps

Format as a professional report.
"""


class PromptManager:
    """Prompt 箮理器"""

    @staticmethod
    def get_template(name: str) -> str:
        """获取 Prompt 模板"""
        templates = {
            "semantic_analysis": SEMANTIC_ANALYSIS_PROMPT,
            "error_classification": ERROR_CLASSIFICATION_PROMPT,
            "root_cause_analysis": ROOT_CAUSE_ANALYSIS_PROMPT,
            "fix_strategy": FIX_STRATEGY_PROMPT,
            "test_case_generation": TEST_CASE_GENERATION_PROMPT,
            "regression_strategy": REGRESSION_STRATEGY_PROMPT,
            "input_detection": INPUT_DETECTION_PROMPT,
            "report_generation": REPORT_GENERATION_PROMPT
        }
        return templates.get(name, "")

    @staticmethod
    def format_template(name: str, **kwargs) -> str:
        """格式化 Prompt 模板"""
        template = PromptManager.get_template(name)
        return template.format(**kwargs)
