"""
错误分类 Tool - 原子能力
"""
from typing import Any, Dict, Optional
from src.tools.base import BaseTool, ToolContext, ToolResult
from src.models.enums import ErrorCategory, ErrorSeverity


class ErrorClassifierTool(BaseTool):
    """
    错误分类工具

    功能：
    - 识别 HTTP 错误类型 (4xx, 5xx)
    - 分类业务错误
    - 推断错误严重程度
    """

    tool_name = "error_classifier"
    tool_description = "Classify errors by category and severity"
    tool_version = "1.0.0"

    # HTTP 状态码映射
    HTTP_ERROR_MAP = {
        # 4xx - Client Errors
        400: {"category": ErrorCategory.VALIDATION_ERROR, "severity": ErrorSeverity.MEDIUM},
        401: {"category": ErrorCategory.AUTH_ERROR, "severity": ErrorSeverity.HIGH},
        403: {"category": ErrorCategory.AUTH_ERROR, "severity": ErrorSeverity.HIGH},
        404: {"category": ErrorCategory.HTTP_ERROR, "severity": ErrorSeverity.MEDIUM},
        405: {"category": ErrorCategory.HTTP_ERROR, "severity": ErrorSeverity.MEDIUM},
        409: {"category": ErrorCategory.BUSINESS_ERROR, "severity": ErrorSeverity.MEDIUM},
        422: {"category": ErrorCategory.VALIDATION_ERROR, "severity": ErrorSeverity.MEDIUM},
        429: {"category": ErrorCategory.HTTP_ERROR, "severity": ErrorSeverity.HIGH},

        # 5xx - Server Errors
        500: {"category": ErrorCategory.DATABASE_ERROR, "severity": ErrorSeverity.CRITICAL},
        502: {"category": ErrorCategory.NETWORK_ERROR, "severity": ErrorSeverity.CRITICAL},
        503: {"category": ErrorCategory.HTTP_ERROR, "severity": ErrorSeverity.CRITICAL},
        504: {"category": ErrorCategory.TIMEOUT_ERROR, "severity": ErrorSeverity.CRITICAL},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

    async def execute(
        self,
        input_data: Any,
        context: ToolContext
    ) -> ToolResult:
        """
        执行错误分类

        Args:
            input_data: 可以是:
                - HTTP 状态码 (int)
                - 包含 'status_code' 的字典
                - 包含 'error_message' 的字典 (用于业务错误分类)
            context: 执行上下文

        Returns:
            ToolResult: 分类结果
        """
        try:
            category = None
            severity = None
            details = {}

            # 基于 HTTP 状态码分类
            status_code = self._extract_status_code(input_data)
            if status_code:
                classification = self._classify_by_status_code(status_code)
                category = classification["category"]
                severity = classification["severity"]
                details["status_code"] = status_code

            # 基于错误消息分类
            error_message = self._extract_error_message(input_data)
            if error_message and not category:
                classification = self._classify_by_message(error_message)
                category = classification["category"]
                severity = classification["severity"]
                details["error_keywords"] = classification.get("keywords", [])

            # 提取错误码
            error_code = self._extract_error_code(input_data)
            if error_code:
                details["error_code"] = error_code

            # 如果无法分类，使用默认值
            if not category:
                category = ErrorCategory.UNKNOWN_ERROR
                severity = ErrorSeverity.LOW

            result = {
                "category": category.value if category else None,
                "severity": severity.value if severity else None,
                "details": details
            }

            return ToolResult(
                tool_name=self.tool_name,
                success=True,
                result=result,
                error=None,
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

    def _extract_status_code(self, input_data: Any) -> Optional[int]:
        """从输入中提取状态码"""
        if isinstance(input_data, int):
            return input_data if 100 <= input_code <= 599 else None
        if isinstance(input_data, dict):
            if "status_code" in input_data:
                return input_data["status_code"]
            if "status" in input_data:
                return input_data["status"]
            if "response" in input_data and isinstance(input_data["response"], dict):
                if "status_code" in input_data["response"]:
                    return input_data["response"]["status_code"]
        return None

    def _extract_error_message(self, input_data: Any) -> Optional[str]:
        """从输入中提取错误消息"""
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, dict):
            for key in ["error_message", "message", "error", "detail"]:
                if key in input_data:
                    return str(input_data[key])
            # 嵌套查找
            if "error" in input_data and isinstance(input_data["error"], dict):
                if "message" in input_data["error"]:
                    return str(input_data["error"]["message"])
        return None

    def _extract_error_code(self, input_data: Any) -> Optional[str]:
        """从输入中提取错误码"""
        if isinstance(input_data, dict):
            for key in ["error_code", "code", "errorCode"]:
                if key in input_data:
                    return str(input_data[key])
        return None

    def _classify_by_status_code(self, status_code: int) -> Dict[str, Any]:
        """基于状态码分类"""
        if status_code in self.HTTP_ERROR_MAP:
            return self.HTTP_ERROR_MAP[status_code]

        # 默认分类
        if 400 <= status_code < 500:
            return {"category": ErrorCategory.HTTP_ERROR, "severity": ErrorSeverity.MEDIUM}
        elif 500 <= status_code < 600:
            return {"category": ErrorCategory.HTTP_ERROR, "severity": ErrorSeverity.CRITICAL}
        else:
            return {"category": ErrorCategory.UNKNOWN_ERROR, "severity": ErrorSeverity.LOW}

    def _classify_by_message(self, message: str) -> Dict[str, Any]:
        """基于错误消息分类"""
        message_lower = message.lower()
        keywords = []

        # 超时错误
        if any(keyword in message_lower for keyword in ["timeout", "timed out", "deadline"]):
            keywords.append("timeout")
            return {
                "category": ErrorCategory.TIMEOUT_ERROR,
                "severity": ErrorSeverity.HIGH,
                "keywords": keywords
            }

        # 认证错误
        if any(keyword in message_lower for keyword in ["unauthorized", "forbidden", "authentication"]):
            keywords.append("auth")
            return {
                "category": ErrorCategory.AUTH_ERROR,
                "severity": ErrorSeverity.HIGH,
                "keywords": keywords
            }

        # 网络错误
        if any(keyword in message_lower for keyword in ["network", "connection", "dns"]):
            keywords.append("network")
            return {
                "category": ErrorCategory.NETWORK_ERROR,
                "severity": ErrorSeverity.HIGH,
                "keywords": keywords
            }

        # 数据库错误
        if any(keyword in message_lower for keyword in ["database", "sql", "query"]):
            keywords.append("database")
            return {
                "category": ErrorCategory.DATABASE_ERROR,
                "severity": ErrorSeverity.CRITICAL,
                "keywords": keywords
            }

        # 验证错误
        if any(keyword in message_lower for keyword in ["validation", "invalid", "required"]):
            keywords.append("validation")
            return {
                "category": ErrorCategory.VALIDATION_ERROR,
                "severity": ErrorSeverity.MEDIUM,
                "keywords": keywords
            }

        return {"category": ErrorCategory.BUSINESS_ERROR, "severity": ErrorSeverity.MEDIUM, "keywords": keywords}
