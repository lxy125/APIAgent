"""
Tool 基类 - 定义 Tool 的统一接口和基础功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from time import perf_counter
from src.models.schemas import ToolResult


@dataclass
class ToolContext:
    """Tool 执行上下文"""
    agent_id: str
    skill_name: str
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """
    Tool 基类

    Tool 是原子能力单元，特征：
    - 无状态（或状态隔离）
    - 单一职责
    - 纯功能（或副作用可控）
    - 可独立测试
    """

    tool_name: str = "base_tool"
    tool_description: str = "Base tool class"
    tool_version: str = "1.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 Tool"""
        self.config = config or {}

    @abstractmethod
    async def execute(
        self,
        input_data: Any,
        context: ToolContext
    ) -> ToolResult:
        """
        执行 Tool 核心逻辑

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            ToolResult: 执行结果
        """
        pass

    async def _execute_with_timing(
        self,
        input_data: Any,
        context: ToolContext
    ) -> ToolResult:
        """
        带计时和错误处理的执行包装器
        """
        start_time = perf_counter()
        try:
            result = await self.execute(input_data, context)
            execution_time = (perf_counter() - start_time) * 1000  # 转换为毫秒
            result.execution_time_ms = execution_time
            return result
        except Exception as e:
            execution_time = (perf_counter() - start_time) * 1000
            return ToolResult(
                tool_name=self.tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=execution_time
            )

    def validate_input(self, input_data: Any) -> bool:
        """
        验证输入数据

        Returns:
            bool: 是否有效
        """
        return True

    def get_schema(self) -> Dict[str, Any]:
        """
        获取 Tool 的输入/输出 Schema

        Returns:
            Dict: Schema 定义
        """
        return {
            "name": self.tool_name,
            "description": self.tool_description,
            "version": self.tool_version,
            "config": self.config
        }


class ToolRegistry:
    """
    Tool 注册表 - 管理 Tool 的注册和查找
    """

    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, type] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, tool_class: type):
        """注册 Tool 类"""
        instance = tool_class()
        cls._tools[instance.tool_name] = tool_class
        return tool_class

    @classmethod
    def get(cls, tool_name: str) -> Optional[type]:
        """获取 Tool 类"""
        return cls._tools.get(tool_name)

    @classmethod
    def list_all(cls) -> list:
        """列出所有 Tool"""
        return list(cls._tools.keys())

    @classmethod
    def clear(cls):
        """清空注册表（主要用于测试）"""
        cls._tools.clear()
