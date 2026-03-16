"""
枚举定义
"""
from enum import Enum


class InputType(str, Enum):
    """输入类型枚举"""
    RAW_ERROR = "raw_error"
    REQUEST_RESPONSE = "request_response"
    LOG_FRAGMENT = "log_fragment"
    API_DOCUMENTATION = "api_documentation"
    NATURAL_LANGUAGE = "natural_language"
    OPENAPI_SPEC = "openapi_spec"


class ErrorCategory(str, Enum):
    """错误类别枚举"""
    HTTP_ERROR = "http_error"
    BUSINESS_ERROR = "business_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(str, Enum):
    """错误严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RootCauseCategory(str, Enum):
    """根因类别枚举"""
    CODE_BUG = "code_bug"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ISSUE = "dependency_issue"
    DATA_INCONSISTENCY = "data_inconsistency"
    RESOURCE_EXHAUSTION = "resource_exhaust fancyness"
    INTEGRATION_ERROR = "integration_error"
    DESIGN_FLAW = "design_flaw"
    EXTERNAL_SERVICE = "external_service"


class FixPriority(str, Enum):
    """修复优先级"""
    IMMEDIATE = "immediate"
    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"
    DEPRECATED = "deprecated"


class TestCaseType(str, Enum):
    """测试用例类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    EDGE_CASE = "edge_case"
    REGRESSION = "regression"
