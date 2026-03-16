"""
API 语义分析 Agent
"""
from typing import Any, Dict
from langchain_core.language_models import BaseChatModel
from src.agents.base import BaseAgent, AgentContext
from src.skills.semantic_analysis.api_analysis_skill import APIAnalysisSkill
from src.models.schemas import SemanticAnalysisResult


class SemanticAnalyzerAgent(BaseAgent):
    """
    API 语义分析 Agent

    职责：
    - 深度解析 API 语义
    - 分析请求响应结构
    - 识别错误类型和关键信息

    拥有的 Skills：
    - APIAnalysisSkill: 完整的 API 语义分析
    - ErrorClassificationSkill: 错误分类（可扩展）
    """

    agent_id = "semantic_analyzer"
    agent_name = "API Semantic Analyzer"
    agent_description = """
    A specialized agent for API semantic analysis.
    Responsibilities:
    - Parse and analyze HTTP requests and responses
    - Extract key information from API interactions
    - Classify errors and determine their severity
    - Understand API semantics and structure
    """
    agent_version = "1.0.0"

    def __init__(
        self,
        llm: BaseChatModel,
        config: Dict[str, Any] = None
    ):
        super().__init__(llm, config)
        self._initialize_default_skills()

    def _initialize_default_skills(self):
        """初始化默认 Skills"""
        # 注册 API 分析 Skill
        api_analysis_skill = APIAnalysisSkill(self.config)
        self.register_skill("api_analysis", api_analysis_skill)

    def _initialize_system_prompt(self):
        """初始化系统提示"""
        self._system_prompt = f"""
You are {self.agent_name}, an expert in API analysis and diagnostics.

Your Responsibilities:
1. Analyze HTTP requests and responses to understand API semantics
2. Extract critical information from API interactions
3. Classify errors and determine their severity
4. Identify patterns in API behavior

Available Skills:
- api_analysis: Perform complete semantic analysis of API requests/responses

When processing input:
1. First, determine the type of input (error message, request/response pair, log, etc.)
2. Use the api_analysis skill to perform deep semantic analysis
3. Provide clear, structured output with key findings
4. Maintain context across the conversation for follow-up questions

Think step by step and be thorough in your analysis.
"""

    async def process(
        self,
        input_data: Any,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        处理输入并返回语义分析结果

        Args:
            input_data: 用户输入数据
            context: Agent 上下文

        Returns:
            Dict: 语义分析结果
        """
        self.update_state(status="processing", current_task="api_semantic_analysis")

        try:
            # 决定使用哪些 Skills
            skills_to_use = await self._decide_skills(input_data)

            # 执行 Skills
            analysis_result = None

            if "api_analysis" in skills_to_use:
                skill_result = await self.execute_skill(
                    "api_analysis",
                    input_data,
                    context
                )

                if skill_result.success:
                    analysis_result = skill_result.result

            # 如果 Skill 失败，使用 LLM 进行分析
            if not analysis_result:
                analysis_result = await self._llm_fallback_analysis(input_data)

            # 转换为 Schema
            semantic_result = self._convert_to_schema(analysis_result)

            # 更新共享记忆
            context.shared_memory["semantic_analysis"] = semantic_result.model_dump()

            self.update_state(status="completed")

            return semantic_result.model_dump()

        except Exception as e:
            self.update_state(status="error")
            raise

    async def _decide_skills(self, input_data: Any) -> list:
        """
        决定使用哪些 Skills

        策略：
        - 如果包含 request/response 数据，使用 api_analysis
        - 如果是错误消息，使用 api_analysis
        - 其他情况，直接使用 LLM 分析
        """
        skills = []

        if isinstance(input_data, dict):
            # 检查是否有 request/response 数据
            if "request" in input_data or "response" in input_data:
                skills.append("api_analysis")
            # 检查是否有状态码
            elif "status_code" in input_data or "status" in input_data:
                skills.append("api_analysis")

        return skills

    async def _llm_fallback_analysis(self, input_data: Any) -> Dict[str, Any]:
        """
        当 Skill 不可用或失败时，使用 LLM 进行分析

        Args:
            input_data: 输入数据

        Returns:
            Dict: 分析结果
        """
        prompt = f"""
Analyze the following input and provide a semantic analysis:

Input: {input_data}

Please provide:
1. Error category (http_error, business_error, validation_error, etc.)
2. Error severity (critical, high, medium, low)
3. Key extracted information
4. Confidence score (0-1)

Format as JSON.
"""

        response = await self.think(prompt)

        # 这里应该解析 JSON 响应
        # 简化处理，返回基本结构
        return {
            "request_info": None,
            "response_info": None,
            "endpoint_info": None,
            "error_category": "unknown",
            "error_severity": "low",
            "error_details": {},
            "extracted_fields": {"raw_input": str(input_data)},
            "confidence": 0.5
        }

    def _convert_to_schema(self, result: Dict[str, Any]) -> SemanticAnalysisResult:
        """将分析结果转换为 Schema"""
        return SemanticAnalysisResult(**result)
