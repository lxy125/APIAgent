"""
根因分析与修复策略 Agent
"""
from typing import Any, Dict
from langchain_core.language_models import BaseChatModel
from src.agents.base import BaseAgent, AgentContext
from src.models.schemas import (
    RootCauseAnalysisResult,
    FixStrategy
)


class RootCauseStrategistAgent(BaseAgent):
    """
    根因分析与修复策略 Agent

    职责：
    - 基于语义分析结果推断可能根因
    - 生成修复建议和策略
    - 评估修复影响和优先级

    拥有的 Skills：
    - RootCauseAnalysisSkill: 根因分析
    - FixStrategySkill: 修复策略生成
    """

    agent_id = "root_cause_strategist"
    agent_name = "Root Cause & Fix Strategist"
    agent_description = """
    A specialized agent for root cause analysis and fix strategy generation.
    Responsibilities:
    - Analyze root causes based on semantic analysis results
    - Generate comprehensive fix strategies
    - Assess impact and provide priority recommendations
    - Suggest validation steps
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
You are {self.agent_name}, an expert in debugging and problem solving.

Your Responsibilities:
1. Analyze root causes based on semantic analysis and available context
2. Generate comprehensive and actionable fix strategies
3. Assess the impact of the fix and provide priority recommendations
4. Suggest validation steps to verify the fix

When processing input:
1. Review the semantic analysis results
2. Correlate error information with potential root causes
3. Consider the error category and severity in your analysis
4. Provide clear, step-by-step fix recommendations
5. Include validation steps to verify the fix

Think systematically and consider multiple potential causes before concluding.
"""

    async def process(
        self,
        input_data: Any,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        处理输入并返回根因分析和修复策略

        Args:
            input_data: 输入数据（通常包含语义分析结果）
            context: Agent 上下文

        Returns:
            Dict: 包含根因分析和修复策略的结果
        """
        self.update_state(status="processing", current_task="root_cause_analysis")

        try:
            # 获取语义分析结果
            semantic_analysis = context.shared_memory.get("semantic_analysis")

            # 执行根因分析
            root_cause_result = await self._analyze_root_cause(
                input_data,
                semantic_analysis
            )

            # 生成修复策略
            fix_strategy = await self._generate_fix_strategy(
                root_cause_result,
                semantic_analysis
            )

            # 更新共享记忆
            context.shared_memory["root_cause_analysis"] = root_cause_result.model_dump()
            context.shared_memory["fix_strategy"] = fix_strategy.model_dump()

            self.update_state(status="completed")

            return {
                "root_cause_analysis": root_cause_result.model_dump(),
                "fix_strategy": fix_strategy.model_dump()
            }

        except Exception as e:
            self.update_state(status="error")
            raise

    async def _analyze_root_cause(
        self,
        input_data: Any,
        semantic_analysis: Dict[str, Any]
    ) -> RootCauseAnalysisResult:
        """
        分析根因

        Args:
            input_data: 输入数据
            semantic_analysis: 语义分析结果

        Returns:
            RootCauseAnalysisResult: 根因分析结果
        """
        # 构建分析提示
        prompt = self._build_root_cause_prompt(
            input_data,
            semantic_analysis
        )

        response = await self.think(prompt)

        # 这里应该解析 LLM 响应为结构化数据
        # 简化处理
        return RootCauseAnalysisResult(
            root_cause_category="code_bug",
            root_cause_description=response[:500] if response else "Analysis pending",
            possible_causes=[
                "Potential issue in business logic",
                "Data validation problem",
                "External service dependency issue"
            ],
            affected_components=["API Layer", "Business Logic"],
            related_logs=[],
            correlation_chain=[]
        )

    async def _generate_fix_strategy(
        self,
        root_cause_result: RootCauseAnalysisResult,
        semantic_analysis: Dict[str, Any]
    ) -> FixStrategy:
        """
        生成修复策略

        Args:
            root_cause_result: 根因分析结果
            semantic_analysis: 语义分析结果

        Returns:
            FixStrategy: 修复策略
        """
        # 构建策略生成提示
        prompt = self._build_fix_strategy_prompt(
            root_cause_result,
            semantic_analysis
        )

        response = await self.think(prompt)

        # 这里应该解析 LLM 响应为结构化数据
        # 简化处理
        return FixStrategy(
            priority="normal",
            suggestions=[
                "Review the business logic in the endpoint handler",
                "Add input validation before processing",
                "Implement proper error handling"
            ],
            code_changes=[],
            configuration_changes=[],
            estimated_effort="2-4 hours",
            risk_level="medium",
            validation_steps=[
                "Test the fix with the original failing case",
                "Run unit tests",
                "Perform integration testing"
            ]
        )

    def _build_root_cause_prompt(
        self,
        input_data: Any,
        semantic_analysis: Dict[str, Any]
    ) -> str:
        """构建根因分析提示"""
        prompt = """
Analyze the root cause of the following issue:

Input Data:
{input}

Semantic Analysis:
- Error Category: {error_category}
- Error Severity: {error_severity}
- Status Code: {status_code}

Please analyze and provide:
1. Root cause category (code_bug, configuration_error, dependency_issue, etc.)
2. Detailed root cause description
3. List of possible causes (ordered by likelihood)
4. Affected components
5. Correlation chain (if applicable)

Think step by step and provide a thorough analysis.
"""

        status_code = None
        if semantic_analysis:
            if semantic_analysis.get("response_info"):
                status_code = semantic_analysis["response_info"].get("status_code")

        return prompt.format(
            input=str(input_data),
            error_category=semantic_analysis.get("error_category") if semantic_analysis else "unknown",
            error_severity=semantic_analysis.get("error_severity") if semantic_analysis else "unknown",
            status_code=status_code
        )

    def _build_fix_strategy_prompt(
        self,
        root_cause_result: RootCauseAnalysisResult,
        semantic_analysis: Dict[str, Any]
    ) -> str:
        """构建修复策略提示"""
        prompt = """
Based on the root cause analysis, generate a comprehensive fix strategy:

Root Cause Analysis:
- Category: {category}
- Description: {description}
- Possible Causes: {causes}
- Affected Components: {components}

Please provide:
1. Fix priority (immediate, urgent, normal, low, deprecated)
2. Detailed suggestions for fixing the issue
3. Specific code changes (if applicable)
4. Configuration changes (if applicable)
5. Estimated effort
6. Risk level (low, medium, high)
7. Validation steps

Format your response clearly with each section labeled.
"""

        return prompt.format(
            category=root_cause_result.root_cause_category,
            description=root_cause_result.root_cause_description,
            causes=", ".join(root_cause_result.possible_causes),
            components=", ".join(root_cause_result.affected_components)
        )
