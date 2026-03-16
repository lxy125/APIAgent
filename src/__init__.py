"""
API Bug 诊断系统 - 主入口

Usage:
    from src import APIDiagnosisSystem

    system = APIDiagnosisSystem()
    report = await system.diagnose(input_data)
"""
from src.agents.supervisor import SupervisorAgent
from src.config.settings import Settings
from langchain_anthropic import ChatAnthropic
from typing import Any, Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class APIDiagnosisSystem:
    """
    API Bug 诊断系统主类

    负责初始化所有组件并提供统一的诊断接口
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        llm: Optional[Any] = None
    ):
        """
        初始化诊断系统

        Args:
            settings: 配置对象，如果为 None 则使用默认配置
            llm: LangChain LLM 实例，如果为 None 则根据配置创建
        """
        self.settings = settings or Settings()
        self.llm = llm or self._create_llm()

        # 初始化 Agents
        self.supervisor = self._create_supervisor()

    def _create_llm(self):
        """创建 LLM 实例"""
        llm_config = self.settings.llm

        if llm_config.provider == "anthropic":
            return ChatAnthropic(
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                anthropic_api_key=llm_config.api_key if llm_config.api_key else None,
                timeout=llm_config.timeout,
                base_url=llm_config.base_url
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")

    def _create_supervisor(self) -> SupervisorAgent:
        """创建 Supervisor Agent"""
        from src.agents.semantic_analyzer import SemanticAnalyzerAgent
        from src.agents.root_cause_strategist import RootCauseStrategistAgent
        from src.agents.test_case_generator import TestCaseGeneratorAgent

        # 创建 Specialist Agents
        semantic_analyzer = SemanticAnalyzerAgent(
            llm=self.llm,
            config=self.settings.agent.model_dump()
        )

        root_cause_strategist = RootCauseStrategistAgent(
            llm=self.llm,
            config=self.settings.agent.model_dump()
        )

        test_case_generator = TestCaseGeneratorAgent(
            llm=self.llm,
            config=self.settings.agent.model_dump()
        )

        # 创建 Supervisor
        return SupervisorAgent(
            llm=self.llm,
            semantic_analyzer=semantic_analyzer,
            root_cause_strategist=root_cause_strategist,
            test_case_generator=test_case_generator,
            config=self.settings.agent.model_dump()
        )

    async def diagnose(
        self,
        input_data: Any,
        session_id: Optional[str] = None
    ):
        """
        执行 API Bug 诊断

        Args:
            input_data: 输入数据，可以是：
                - 原始错误信息
                - 请求响应对
                - 日志片段
                - API 文档
                - 自然语言描述
            session_id: 会话 ID，如果为 None 则自动生成

        Returns:
            DiagnosticReport: 完整诊断报告
        """
        import uuid

        if session_id is None:
            session_id = uuid.uuid4().hex

        task_id = uuid.uuid4().hex

        from src.agents.base import AgentContext

        context = AgentContext(
            session_id=session_id,
            task_id=task_id,
            metadata={}
        )

        logger.info(
            f"Starting diagnosis for session {session_id}, task {task_id}"
        )

        report = await self.supervisor.process(input_data, context)

        logger.info(
            f"Diagnosis completed for session {session_id}, "
            f"report ID: {report.report_id}"
        )

        return report

    async def diagnose_batch(
        self,
        inputs: list[Any]
    ):
        """
        批量诊断

        Args:
            inputs: 输入数据列表

        Returns:
            List[DiagnosticReport]: 诊断报告列表
        """
        reports = []

        for input_data in inputs:
            report = await self.diagnose(input_data)
            reports.append(report)

        return reports


# 便捷函数
async def diagnose(input_data: Any, llm: Optional[Any] = None):
    """
    便捷的诊断函数

    Args:
        input_data: 输入数据
        llm: LLM 实例（可选）

    Returns:
        DiagnosticReport: 诊断报告
    """
    system = APIDiagnosisSystem(llm=llm)
    return await system.diagnose(input_data)


__version__ = "0.1.0"
__all__ = [
    "APIDiagnosisSystem",
    "diagnose"
]
