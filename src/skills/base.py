"""
Skill 基类 - 定义 Skill 的统一接口和基础功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from time import perf_counter
import logging

from src.tools.base import BaseTool, ToolRegistry, ToolContext
from src.models.schemas import SkillResult, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class SkillContext:
    """Skill 执行上下文"""
    agent_id: str
    session_id: str
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_tool_context(self, skill_name: str) -> ToolContext:
        """创建 Tool 上下文"""
        return ToolContext(
            agent_id=self.agent_id,
            skill_name=skill_name,
            session_id=self.session_id,
            metadata=self.metadata
        )


class BaseSkill(ABC):
    """
    Skill 基类

    Skill 是面向任务的策略性能力，特征：
    - 有明确的任务目标
    - 组织多个 Tool 完成任务
    - 有执行策略和流程
    - 可配置和可扩展
    """

    skill_name: str = "base_skill"
    skill_description: str = "Base skill class"
    skill_version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        tools: Optional[Dict[str, BaseTool]] = None
    ):
        """
        初始化 Skill

        Args:
            config: Skill 配置
            tools: 依赖的 Tool 实例字典
        """
        self.config = config or {}
        self._tools = tools or {}
        self._tool_registry = ToolRegistry()

        # 初始化默认 Tools
        self._initialize_default_tools()

    def _initialize_default_tools(self):
        """
        初始化默认 Tools
        子类可以重写此方法来定义默认依赖的 Tools
        """
        pass

    def register_tool(self, name: str, tool: BaseTool):
        """注册 Tool"""
        self._tools[name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取 Tool"""
        return self._tools.get(name)

    @abstractmethod
    async def execute(
        self,
        input_data: Any,
        context: SkillContext
    ) -> SkillResult:
        """
        执行 Skill 核心逻辑

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            SkillResult: 执行结果
        """
        pass

    async def execute_tool(
        self,
        tool_name: str,
        input_data: Any,
        context: SkillContext
    ) -> ToolResult:
        """
        执行指定的 Tool

        Args:
            tool_name: Tool 名称
            input_data: 输入数据
            context: Skill 上下文

        Returns:
            ToolResult: Tool 执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found",
                execution_time_ms=0
            )

        tool_context = context.get_tool_context(self.skill_name)
        return await tool._execute_with_timing(input_data, tool_context)

    async def execute_tool_chain(
        self,
        chain: List[tuple],
        initial_data: Any,
        context: SkillContext
    ) -> List[ToolResult]:
        """
        执行 Tool 链（串行执行）

        Args:
            chain: Tool 链定义，每个元素是 (tool_name, transform_func)
                   transform_func 用于将前一个结果转换为下一个输入
            initial_data: 初始输入数据
            context: 执行上下文

        Returns:
            List[ToolResult]: 所有 Tool 的执行结果
        """
        results = []
        current_data = initial_data

        for tool_name, transform_func in chain:
            result = await self.execute_tool(tool_name, current_data, context)
            results.append(result)

            if not result.success:
                logger.error(f"Tool chain broken at {tool_name}: {result.error}")
                break

            # 转换数据用于下一个 Tool
            if transform_func:
                current_data = transform_func(result.result)

        return results

    async def execute_tools_parallel(
        self,
        tool_configs: List[Dict[str, Any]],
        context: SkillContext
    ) -> List[ToolResult]:
        """
        并行执行多个 Tools

        Args:
            tool_configs: Tool 配置列表，每个包含 'name' 和 'input_data'
            context: 执行上下文

        Returns:
            List[ToolResult]: 所有 Tool 的执行结果
        """
        import asyncio

        tasks = []
        for config in tool_configs:
            task = self.execute_tool(
                config['name'],
                config['input_data'],
                context
            )
            tasks.append(task)

        return await asyncio.gather(*tasks)

    async def _execute_with_timing(
        self,
        input_data: Any,
        context: SkillContext
    ) -> SkillResult:
        """
        带计时和错误跟踪的执行包装器
        """
        start_time = perf_counter()
        tools_used = []

        try:
            result = await self.execute(input_data, context)
            execution_time = (perf_counter() - start_time) * 1000

            # 提取使用的 Tools
            if result.tools_used:
                tools_used = result.tools_used

            result.execution_time_ms = execution_time
            result.tools_used = tools_used

            return result

        except Exception as e:
            execution_time = (perf_counter() - start_time) * 1000
            logger.exception(f"Skill {self.skill_name} execution failed: {e}")

            return SkillResult(
                skill_name=self.skill_name,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=execution_time,
                tools_used=tools_used
            )

    def validate_input(self, input_data: Any) -> bool:
        """验证输入数据"""
        return True

    def get_schema(self) -> Dict[str, Any]:
        """获取 Skill 的 Schema"""
        return {
            "name": self.skill_name,
            "description": self.skill_description,
            "version": self.skill_version,
            "tools": list(self._tools.keys()),
            "config": self.config
        }


class SkillRegistry:
    """
    Skill 注册表 - 管理 Skill 的注册和查找
    """

    _instance: Optional["SkillRegistry"] = None
    _skills: Dict[str, type] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, skill_class: type):
        """注册 Skill 类"""
        instance = skill_class()
        cls._skills[instance.skill_name] = skill_class
        return skill_class

    @classmethod
    def get(cls, skill_name: str) -> Optional[type]:
        """获取 Skill 类"""
        return cls._skills.get(skill_name)

    @classmethod
    def list_all(cls) -> list:
        """列出所有 Skill"""
        return list(cls._skills.keys())

    @classmethod
    def clear(cls):
        """清空注册表"""
        cls._skills.clear()
