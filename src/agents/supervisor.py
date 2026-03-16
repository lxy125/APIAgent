"""
Supervisor Agent - 协调所有 Agent 的工作
"""
import uuid
from typing import Any, Dict, List, Optional
import asyncio
from langchain_core.language_models import BaseChatModel

from src.agents.base import BaseAgent, AgentContext, AgentState
from src.models.schemas import (
    UserInput,
    InputType,
    DiagnosticReport,
    ErrorSeverity,
    SemanticAnalysisResult,
    RootCauseAnalysisResult,
    FixStrategy,
    TestSuite,
    RegressionStrategy
)


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent

    职责：
    - 任务路由：分析输入类型，决定路由到哪些 Agent
    - 协调执行：协调各 Agent 的执行顺序和数据流转
    - 结果聚合：汇总各 Agent 结果，生成最终报告

    拥有的 Skills：
    - RoutingSkill: 路由决策
    - CoordinationSkill: 协调执行
    - AggregationSkill: 结果聚合
    """

    agent_id = "supervisor"
    agent_name = "Supervisor"
    agent_description = """
    The supervisor agent that orchestrates the entire API bug diagnosis workflow.
    Responsibilities:
    - Analyze input type and route to appropriate agents
    - Coordinate agent execution and data flow
    - Aggregate results and generate final reports
    - Handle workflow state and error recovery
    """
    agent_version = "1.0.0"

    def __init__(
        self,
        llm: BaseChatModel,
        semantic_analyzer,
        root_cause_strategist,
        test_case_generator,
        config: Dict[str, Any] = None
    ):
        """
        初始化 Supervisor

        Args:
            llm: LangChain LLM 实例
            semantic_analyzer: 语义分析 Agent
            root_cause_strategist: 根因分析 Agent
            test_case_generator: 测试用例生成 Agent
            config: 配置
        """
        super().__init__(llm, config)

        # 注册子 Agents
        self.semantic_analyzer = semantic_analyzer
        self.root_cause_strategist = root_cause_strategist
        self.test_case_generator = test_case_generator

        # 工作流状态
        self._workflow_state = {}

    def _initialize_system_prompt(self):
        """初始化系统提示"""
        self._system_prompt = f"""
You are {self.agent_name}, the central coordinator for API bug diagnosis.

Your Responsibilities:
1. Analyze the type of user input
2. Route the task to appropriate specialist agents
3. Coordinate the execution flow and data sharing
4. Aggregate results into comprehensive reports
5. Handle error recovery and fallback strategies

Available Specialist Agents:
- semantic_analyzer: Analyzes API semantics and classifies errors
- root_cause_strategist: Analyzes root causes and generates fix strategies
- test_case_generator: Generates test cases and regression strategies

Workflow:
1. Route input based on type
2. Execute semantic analysis (always)
3. Execute root cause analysis (depends on semantic analysis)
4. Execute test case generation (can run in parallel with root cause)
5. Aggregate all results into final report

Coordinate effectively and ensure data flows correctly between agents.
"""

    async def process(
        self,
        input_data: Any,
        context: AgentContext
    ) -> DiagnosticReport:
        """
        处理用户输入并返回完整诊断报告

        Args:
            input_data: 用户输入数据
            context: Agent 上下文

        Returns:
            DiagnosticReport: 完整诊断报告
        """
        self.update_state(status="processing", current_task="diagnosis_workflow")

        try:
            # 生成报告 ID
            report_id = f"diag_{uuid.uuid4().hex[:12]}"

            # 步骤 1: 路由分析
            input_type = await self._route_input(input_data, context)

            # 构建用户输入模型
            user_input = UserInput(
                input_type=input_type,
                content=str(input_data),
                metadata={"raw_data": input_data}
            )

            # 步骤 2: 语义分析（必选）
            self.update_state(
                status="processing",
                current_task="semantic_analysis"
            )

            semantic_result = await self._execute_semantic_analysis(
                input_data,
                context
            )
            semantic_result_model = SemanticAnalysisResult(**semantic_result)

            # 步骤 3: 并行执行根因分析和测试生成
            self.update_state(
                status="processing",
                current="parallel_execution"
            )

            root_cause_task = self._execute_root_cause_analysis(
                input_data,
                context
            )

            test_generation_task = self._execute_test_generation(
                input_data,
                context
            )

            # 等待并行任务完成
            root_cause_result, test_generation_result = await asyncio.gather(
                root_cause_task,
                test_generation_task,
                return_exceptions=True
            )

            # 处理根因分析结果
            if isinstance(root_cause_result, Exception):
                # 错误处理
                root_cause_analysis = self._get_fallback_root_cause()
                fix_strategy = self._get_fallback_fix_strategy()
            else:
                root_cause_analysis = RootCauseAnalysisResult(
                    **root_cause_result["root_cause_analysis"]
                )
                fix_strategy = FixStrategy(
                    **root_cause_result["fix_strategy"]
                )

            # 处理测试生成结果
            if isinstance(test_generation_result, Exception):
                # 错误处理
                test_suite = self._get_fallback_test_suite()
                regression_strategy = self._get_fallback_regression_strategy()
            else:
                test_suite = TestSuite(
                    **test_generation_result["test_suite"]
                )
                regression_strategy = RegressionStrategy(
                    **test_generation_result["regression_strategy"]
                )

            # 步骤 4: 聚合结果生成最终报告
            self.update_state(
                status="processing",
                current_task="aggregation"
            )

            report = await self._aggregate_report(
                report_id=report_id,
                user_input=user_input,
                semantic_analysis=semantic_result_model,
                root_cause_analysis=root_cause_analysis,
                fix_strategy=fix_strategy,
                test_suite=test_suite,
                regression_strategy=regression_strategy,
                context=context
            )

            self.update_state(status="completed")

            return report

        except Exception as e:
            self.update_state(status="error")
            raise

    async def _route_input(
        self,
        input_data: Any,
        context: AgentContext
    ) -> InputType:
        """
        分析输入类型并路由

        Args:
            input_data: 输入数据
            context: Agent 上下文

        Returns:
            InputType: 输入类型
        """
        # 简单的路由逻辑
        if isinstance(input_data, dict):
            if "request" in input_data or "response" in input_data:
                return InputType.REQUEST_RESPONSE
            elif "openapi" in input_data or "swagger" in input_data:
                return InputType.OPENAPI_SPEC
            elif "log" in input_data or "trace" in input_data:
                return InputType.LOG_FRAGMENT
            elif "doc" in input_data or "documentation" in input_data:
                return InputType.API_DOCUMENTATION

        # 使用 LLM 进行更智能的路由
        prompt = f"""
Analyze the following input and determine its type:

Input: {input_data}

Possible types:
- raw_error: Raw error message
- request_response: HTTP request/response pair
- log_fragment: Log file fragment
- api_documentation: API documentation
- natural_language: Natural language description
- openapi_spec: OpenAPI specification

Return the type as a single word.
"""

        response = await self.think(prompt)

        # 映射 LLM 响应到 InputType
        type_mapping = {
            "raw_error": InputType.RAW_ERROR,
            "request_response": InputType.REQUEST_RESPONSE,
            "log_fragment": InputType.LOG_FRAGMENT,
            "api_documentation": InputType.API_DOCUMENTATION,
            "natural_language": InputType.NATURAL_LANGUAGE,
            "openapi_spec": InputType.OPENAPI_SPEC
        }

        response_clean = response.strip().lower()
        return type_mapping.get(response_clean, InputType.NATURAL_LANGUAGE)

    async def _execute_semantic_analysis(
        self,
        input_data: Any,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        执行语义分析

        Args:
            input_data: 输入数据
            context: Agent 上下文

        Returns:
            Dict: 语义分析结果
        """
        result = await self.semantic_analyzer.process(input_data, context)

        # 记录执行日志
        self._log_agent_execution(
            "semantic_analyzer",
            "completed",
            result
        )

        return result

    async def _execute_root_cause_analysis(
        self,
        input_data: Any,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        执行根因分析

        Args:
            input_data: 输入数据
            context: Agent 上下文

        Returns:
            Dict: 根因分析和修复策略结果
        """
        result = await self.root_cause_strategist.process(input_data, context)

        # 记录执行日志
        self._log_agent_execution(
            "root_cause_strategist",
            "completed",
            result
        )

        return result

    async def _execute_test_generation(
        self,
        input_data: Any,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        执行测试用例生成

        Args:
            input_data: 输入数据
            context: Agent 上下文

        Returns:
            Dict: 测试套件和回归策略结果
        """
        result = await self.test_case_generator.process(input_data, context)

        # 记录执行日志
        self._log_agent_execution(
            "test_case_generator",
            "completed",
            result
        )

        return result

    async def _aggregate_report(
        self,
        report_id: str,
        user_input: UserInput,
        semantic_analysis: SemanticAnalysisResult,
        root_cause_analysis: RootCauseAnalysisResult,
        fix_strategy: FixStrategy,
        test_suite: TestSuite,
        regression_strategy: RegressionStrategy,
        context: AgentContext
    ) -> DiagnosticReport:
        """
        聚合结果生成最终报告

        Args:
            report_id: 报告 ID
            user_input: 用户输入
            semantic_analysis: 语义分析结果
            root_cause_analysis: 根因分析结果
            fix_strategy: 修复策略
            test_suite: 测试套件
            regression_strategy: 回归策略
            context: Agent 上下文

        Returns:
            DiagnosticReport: 完整诊断报告
        """
        # 计算整体严重程度
        overall_severity = self._calculate_overall_severity(
            semantic_analysis,
            fix_strategy
        )

        # 生成综合建议
        recommendations = await self._generate_recommendations(
            semantic_analysis,
            root_cause_analysis,
            fix_strategy
        )

        # 预估修复时间
        estimated_fix_time = self._estimate_fix_time(fix_strategy)

        # 构建执行日志
        agent_execution_log = self._workflow_state.copy()

        return DiagnosticReport(
            report_id=report_id,
            input_summary=user_input,
            semantic_analysis=semantic_analysis,
            root_cause_analysis=root_cause_analysis,
            fix_strategy=fix_strategy,
            test_suite=test_suite,
            regression_strategy=regression_strategy,
            overall_severity=overall_severity,
            estimated_fix_time=estimated_fix_time,
            recommendations=recommendations,
            agent_execution_log=agent_execution_log
        )

    def _calculate_overall_severity(
        self,
        semantic_analysis: SemanticAnalysisResult,
        fix_strategy: FixStrategy
    ) -> ErrorSeverity:
        """
        计算整体严重程度

        Args:
            semantic_analysis: 语义分析结果
            fix_strategy: 修复策略

        Returns:
            ErrorSeverity: 整体严重程度
        """
        # 基于多个因素计算
        severity_score = 0

        # 考虑错误严重程度
        if semantic_analysis.error_details:
            # 这里可以根据 error_details 中的 severity 评分
            severity_score += 1

        # 考虑修复优先级
        priority_score = {
            "immediate": 3,
            "urgent": 2,
            "normal": 1,
            "low": 0,
            "deprecated": 0
        }
        severity_score += priority_score.get(fix_strategy.priority, 1)

        # 考虑风险等级
        risk_score = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        severity_score += risk_score.get(fix_strategy.risk_level, 2)

        # 映射到 ErrorSeverity
        if severity_score >= 6:
            return ErrorSeverity.CRITICAL
        elif severity_score >= 4:
            return ErrorSeverity.HIGH
        elif severity_score >= 2:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    async def _generate_recommendations(
        self,
        semantic_analysis: SemanticAnalysisResult,
        root_cause_analysis: RootCauseAnalysisResult,
        fix_strategy: FixStrategy
    ) -> List[str]:
        """
        生成综合建议

        Args:
            semantic_analysis: 语义分析结果
            root_cause_analysis: 根因分析结果
            fix_strategy: 修复策略

        Returns:
            List[str]: 建议列表
        """
        recommendations = []

        # 基于修复策略生成建议
        recommendations.extend(fix_strategy.suggestions)

        # 添加验证建议
        if fix_strategy.validation_steps:
            recommendations.append("\nValidation Steps:")
            recommendations.extend(fix_strategy.validation_steps)

        # 使用 LLM 生成额外建议
        prompt = self._build_recommendations_prompt(
            semantic_analysis,
            root_cause_analysis,
            fix_strategy
        )

        response = await self.think(prompt)

        # 解析 LLM 响应
        recommendations.append(f"\nAdditional Recommendations:\n{response}")

        return recommendations

    def _build_recommendations_prompt(
        self,
        semantic_analysis: SemanticAnalysisResult,
        root_cause_analysis: RootCauseAnalysisResult,
        fix_strategy: FixStrategy
    ) -> str:
        """构建建议生成提示"""
        return f"""
Based on the analysis, provide additional recommendations:

Root Cause: {root_cause_analysis.root_cause_description}
Fix Priority: {fix_strategy.priority}
Risk Level: {fix_strategy.risk_level}

Please provide:
1. Prevention measures to avoid similar issues
2. Monitoring and alerting suggestions
3. Documentation updates needed
4. Code review focus areas

Be concise and actionable.
"""

    def _estimate_fix_time(self, fix_strategy: FixStrategy) -> Optional[str]:
        """
        预估修复时间

        Args:
            fix_strategy: 修复策略

        Returns:
            str: 预估时间
        """
        # 基于优先级和风险预估时间
        if fix_strategy.estimated_effort:
            return fix_strategy.estimated_effort

        priority_time_map = {
            "immediate": "1-2 hours",
            "urgent": "2-4 hours",
            "normal": "4-8 hours",
            "low": "1-2 days",
            "deprecated": "N/A"
        }

        return priority_time_map.get(fix_strategy.priority, "4-8 hours")

    def _log_agent_execution(
        self,
        agent_id: str,
        status: str,
        result: Any
    ):
        """记录 Agent 执行日志"""
        self._workflow_state[agent_id] = {
            "status": status,
            "result_summary": str(result)[:200] if result else None
        }

    def _get_fallback_root_cause(self) -> RootCauseAnalysisResult:
        """获取备用根因分析结果"""
        return RootCauseAnalysisResult(
            root_cause_category=None,
            root_cause_description="Root cause analysis failed",
            possible_causes=["Analysis unavailable"],
            affected_components=[],
            related_logs=[],
            correlation_chain=[]
        )

    def _get_fallback_fix_strategy(self) -> FixStrategy:
        """获取备用修复策略"""
        return FixStrategy(
            priority="low",
            suggestions=["Review logs and analyze manually"],
            code_changes=[],
            configuration_changes=[],
            estimated_effort="Unknown",
            risk_level="low",
            validation_steps=["Manual testing required"]
        )

    def _get_fallback_test_suite(self) -> TestSuite:
        """获取备用测试套件"""
        return TestSuite(
            suite_name="fallback_test_suite",
            test_cases=[],
            setup_steps=[],
            teardown_steps=[]
        )

    def _get_fallback_regression_strategy(self) -> RegressionStrategy:
        """获取备用回归策略"""
        return RegressionStrategy(
            affected_endpoints=[],
            regression_priority=[],
            suggested_test_suites=[],
            smoke_tests=[]
        )
