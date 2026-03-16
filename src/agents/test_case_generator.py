"""
测试用例生成 Agent
"""
from typing import Any, Dict
import uuid
from langchain_core.language_models import BaseChatModel
from src.agents.base import BaseAgent, AgentContext
from src.models.schemas import (
    TestCase,
    TestSuite,
    RegressionStrategy,
    RequestInfo,
    ResponseInfo,
    TestCaseType
)


class TestCaseGeneratorAgent(BaseAgent):
    """
    测试用例生成 Agent

    职责：
    - 生成正向、负向、边界测试用例
    - 生成回归测试建议
    - 提供测试优先级排序

    拥有的 Skills：
    - TestCaseGenerationSkill: 测试用例生成
    - RegressionStrategySkill: 回归策略
    """

    agent_id = "test_case_generator"
    agent_name = "Test Case Generator"
    agent_description = """
    A specialized agent for generating comprehensive test cases.
    Responsibilities:
    - Generate positive, negative, and edge case tests
    - Create regression test strategies
    - Provide test prioritization
    - Ensure test coverage for the fix
    """
    agent_version = "1.0.0"

    def __init__(
        self,
        llm: BaseChatModel,
        config: Dict[str, Any] = None
    ):
        super().__init__(llm, config)

    def _initialize_system_prompt(self):
        """初始化系统提示"""
        self._system_prompt = f"""
You are {self.agent_name}, an expert in test case design and quality assurance.

Your Responsibilities:
1. Generate comprehensive test cases covering positive, negative, and edge cases
2. Create regression test strategies to prevent future issues
3. Provide test prioritization based on risk and impact
4. Ensure test coverage for the identified fix

When processing input:
1. Review the semantic analysis and fix strategy
2. Consider the error category and root cause
3. Generate test cases that would have caught the bug
4. Create regression tests for related functionality
5. Prioritize tests based on risk and importance

Be thorough and ensure comprehensive coverage.
"""

    async def process(
        self,
        input_data: Any,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        处理输入并返回测试用例和回归策略

        Args:
            input_data: 输入数据
            context: Agent 上下文

        Returns:
            Dict: 包含测试套件和回归策略的结果
        """
        self.update_state(status="processing", current_task="test_case_generation")

        try:
            # 获取上下文信息
            semantic_analysis = context.shared_memory.get("semantic_analysis")
            fix_strategy = context.shared_memory.get("fix_strategy")

            # 生成测试套件
            test_suite = await self._generate_test_suite(
                input_data,
                semantic_analysis,
                fix_strategy
            )

            # 生成回归策略
            regression_strategy = await self._generate_regression_strategy(
                test_suite,
                semantic_analysis
            )

            # 更新共享记忆
            context.shared_memory["test_suite"] = test_suite.model_dump()
            context.shared_memory["regression_strategy"] = regression_strategy.model_dump()

            self.update_state(status="completed")

            return {
                "test_suite": test_suite.model_dump(),
                "regression_strategy": regression_strategy.model_dump()
            }

        except Exception as e:
            self.update_state(status="error")
            raise

    async def _generate_test_suite(
        self,
        input_data: Any,
        semantic_analysis: Dict[str, Any],
        fix_strategy: Dict[str, Any]
    ) -> TestSuite:
        """
        生成测试套件

        Args:
            input_data: 输入数据
            semantic_analysis: 语义分析结果
            fix_strategy: 修复策略

        Returns:
            TestSuite: 测试套件
        """
        # 生成正向测试用例
        positive_tests = await self._generate_positive_tests(
            input_data,
            semantic_analysis
        )

        # 生成负向测试用例
        negative_tests = await self._generate_negative_tests(
            input_data,
            semantic_analysis
        )

        # 生成边界测试用例
        edge_tests = await self._generate_edge_tests(
            input_data,
            semantic_analysis
        )

        all_tests = positive_tests + negative_tests + edge_tests

        return TestSuite(
            suite_name=f"api_bug_diagnosis_{uuid.uuid4().hex[:8]}",
            test_cases=all_tests,
            setup_steps=[
                "Initialize test environment",
                "Configure mock services"
            ],
            teardown_steps=[
                "Clean up test data",
                "Reset service state"
            ]
        )

    async def _generate_positive_tests(
        self,
        input_data: Any,
        semantic_analysis: Dict[str, Any]
    ) -> list[TestCase]:
        """
        生成正向测试用例

        Args:
            input_data: 输入数据
            semantic_analysis: 语义分析结果

        Returns:
            List[TestCase]: 正向测试用例列表
        """
        tests = []

        # 提取请求信息
        request_info = None
        if semantic_analysis and semantic_analysis.get("request_info"):
            request_data = semantic_analysis["request_info"]
            request_info = RequestInfo(**request_data)

        if request_info:
            # 生成成功的测试用例
            tests.append(TestCase(
                case_id=f"test_positive_{uuid.uuid4().hex[:8]}",
                name="Success case",
                description="Test successful API call with valid parameters",
                case_type=TestCaseType.POSITIVE,
                request=request_info,
                expected_response=ResponseInfo(
                    status_code=200,
                    body={"success": True}
                ),
                expected_error=None,
                priority=5,
                tags=["smoke", "happy-path"]
            ))

            # 生成基于不同参数的测试
            prompt = self._build_test_generation_prompt(
                "positive",
                request_info,
                semantic_analysis
            )

            response = await self.think(prompt)

            # 这里应该解析 LLM 响应生成更多测试
            # 简化处理
            pass

        return tests

    async def _generate_negative_tests(
        self,
        input_data: Any,
        semantic_analysis: Dict[str, Any]
    ) -> list[TestCase]:
        """
        生成负向测试用例

        Args:
            input_data: 输入数据
            semantic_analysis: 语义分析结果

        Returns:
            List[TestCase]: 负向测试用例列表
        """
        tests = []

        # 生成原始失败的测试用例
        request_info = None
        expected_error = None

        if semantic_analysis:
            if semantic_analysis.get("request_info"):
                request_info = RequestInfo(**semantic_analysis["request_info"])
            if semantic_analysis.get("error_message"):
                expected_error = semantic_analysis["error_message"]

        if request_info:
            tests.append(TestCase(
                case_id=f"test_negative_{uuid.uuid4().hex[:8]}",
                name="Original failure case",
                description="Test that reproduces the original bug",
                case_type=TestCaseType.NEGATIVE,
                request=request_info,
                expected_response=None,
                expected_error=expected_error,
                priority=5,
                tags=["regression", "bug-reproduction"]
            ))

        # 生成更多负向测试
        # 验证参数缺失
        # 验证无效参数
        # 验证权限问题
        # ...

        return tests

    async def _generate_edge_tests(
        self,
        input_data: Any,
        semantic_analysis: Dict[str, Any]
    ) -> list[TestCase]:
        """
        生成边界测试用例

        Args:
            input_data: 输入数据
            semantic_analysis: 语义分析结果

        Returns:
            List[TestCase]: 边界测试用例列表
        """
        tests = []

        # 边界情况测试
        # - 空值测试
        # - 极值测试
        # - 特殊字符测试
        # - 超长字符串测试
        # - 并发请求测试

        prompt = self._build_test_generation_prompt(
            "edge",
            None,
            semantic_analysis
        )

        response = await self.think(prompt)

        # 解析 LLM 响应生成边界测试
        # 简化处理

        return tests

    async def _generate_regression_strategy(
        self,
        test_suite: TestSuite,
        semantic_analysis: Dict[str, Any]
    ) -> RegressionStrategy:
        """
        生成回归策略

        Args:
            test_suite: 生成的测试套件
            semantic_analysis: 语义分析结果

        Returns:
            RegressionStrategy: 回归策略
        """
        # 识别受影响的端点
        affected_endpoints = []

        if semantic_analysis and semantic_analysis.get("endpoint_info"):
            endpoint_data = semantic_analysis["endpoint_info"]
            endpoint_path = endpoint_data.get("path")
            endpoint_method = endpoint_data.get("method")

            if endpoint_path:
                affected_endpoints.append(f"{endpoint_method} {endpoint_path}")

        # 生成回归优先级
        regression_priority = []

        if affected_endpoints:
            regression_priority.extend(affected_endpoints)

        # 使用 LLM 识别相关端点
        prompt = self._build_regression_prompt(
            affected_endpoints,
            semantic_analysis
        )

        response = await self.think(prompt)

        # 解析响应


        return RegressionStrategy(
            affected_endpoints=affected_endpoints,
            regression_priority=regression_priority,
            suggested_test_suites=[test_suite],
            smoke_tests=test_suite.test_cases[:3]  # 前 3 个作为冒烟测试
        )

    def _build_test_generation_prompt(
        self,
        test_type: str,
        request_info: RequestInfo,
        semantic_analysis: Dict[str, Any]
    ) -> str:
        """构建测试生成提示"""
        prompt = f"""
Generate {test_type} test cases for the following scenario:

Request Info:
{request_info.model_dump() if request_info else 'N/A'}

Semantic Analysis:
{semantic_analysis if semantic_analysis else 'N/A'}

Please generate test cases that would:
- For positive tests: Cover happy paths and valid scenarios
- For negative tests: Cover error scenarios and invalid inputs
- For edge tests: Cover boundary conditions and corner cases

Format each test case with:
- Name
- Description
- Request details
- Expected response or expected error

Provide 3-5 test cases for this category.
"""

        return prompt

    def _build_regression_prompt(
        self,
        affected_endpoints: list[str],
        semantic_analysis: Dict[str, Any]
    ) -> str:
        """构建回归策略提示"""
        prompt = f"""
Identify endpoints that might be affected by the fix.

Affected Endpoints:
{', '.join(affected_endpoints) if affected_endpoints else 'None'}

Semantic Analysis:
{semantic_analysis if semantic_analysis else 'N/A'}

Please identify:
1. Related endpoints that might be affected
2. Priority order for regression testing
3. Any integration points to consider

Format as a list of endpoints in priority order.
"""

        return prompt
