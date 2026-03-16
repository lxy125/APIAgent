"""
JSON 解析 Tool - 原子能力
"""
import json
from typing import Any, Dict, Optional
from src.tools.base import BaseTool, ToolContext, ToolResult


class JSONParserTool(BaseTool):
    """
    JSON 解析工具

    功能：
    - 解析 JSON 字符串为 Python 对象
    - 提取 JSON 中的特定字段
    - 验证 JSON 格式
    """

    tool_name = "json_parser"
    tool_description = "Parse JSON strings and extract fields"
    tool_version = "1.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.encoding = config.get("encoding", "utf-8") if config else "utf-8"

    async def execute(
        self,
        input_data: Any,
        context: ToolContext
    ) -> ToolResult:
        """
        执行 JSON 解析

        Args:
            input_data: 可以是:
                - JSON 字符串
                - 包含 'json_str' 字段的字典
                - 包含 'json_str' 和 'field_path' 的字典（用于提取字段）
            context: 执行上下文

        Returns:
            ToolResult: 解析结果
        """
        try:
            # 处理输入
            if isinstance(input_data, str):
                json_str = input_data
                field_path = None
            elif isinstance(input_data, dict):
                json_str = input_data.get("json_str")
                field_path = input_data.get("field_path")
            else:
                raise ValueError(f"Unsupported input type: {type(input_data)}")

            if not json_str:
                raise ValueError("JSON string is required")

            # 解析 JSON
            parsed_data = json.loads(json_str)

            # 如果指定了字段路径，提取该字段
            if field_path:
                result = self._extract_field(parsed_data, field_path)
            else:
                result = parsed_data

            return ToolResult(
                tool_name=self.tool_name,
                success=True,
                result=result,
                error=None,
                execution_time_ms=0  # 会被包装器覆盖
            )

        except json.JSONDecodeError as e:
            return ToolResult(
                tool_name=self.tool_name,
                success=False,
                result=None,
                error=f"Invalid JSON: {str(e)}",
                execution_time_ms=0
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=0
            )

    def _extract_field(self, data: Any, field_path: str) -> Any:
        """
        从嵌套数据中提取字段

        Args:
            data: 解析后的数据
            field_path: 字段路径，支持点表示法，如 "data.user.name"

        Returns:
            Any: 提取的字段值
        """
        current = data
        for key in field_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    raise IndexError(f"Index {index} out of range")
            else:
                raise KeyError(f"Field '{key}' not found")
        return current

    def validate_input(self, input_data: Any) -> bool:
        """验证输入"""
        if isinstance(input_data, str):
            return True
        if isinstance(input_data, dict):
            return "json_str" in input_data
        return False
