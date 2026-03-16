"""
API Bug 诊断系统 - 数据模型与 Schema 定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# =============================================================================
# 枚举定义
# =============================================================================

class InputType(str, Enum):
    """输入类型枚举"""
    RAW_ERROR = "raw_error"            # 原始错误信息
    REQUEST_RESPONSE = "request_response"  # 请求响应对
    LOG_FRAGMENT = "log_fragment"      # 日志片段
    API_DOCUMENTATION = "api_documentation"  # API 文档
    NATURAL_LANGUAGE = "natural_language"  # 自然语言描述
    OPENAPI_SPEC = "openapi_spec"      # OpenAPI 规范


class ErrorCategory(str, Enum):
    """错误类别枚举"""
    HTTP_ERROR = "http_error"          # HTTP 层错误 (4xx, 5xx)
    BUSINESS_ERROR = "business_error"   # 业务逻辑错误
    VALIDATION_ERROR = "validation_error"  # 参数验证错误
    TIMEOUT_ERROR = "timeout_error"     # 超时错误
    AUTH_ERROR = "auth_error"           # 认证/授权错误
    NETWORK_ERROR = "network_error"     # 网络层错误
    DATABASE_ERROR = "database_error"   # 数据库错误
    UNKNOWN_ERROR = "unknown_error"     # 未知错误


class ErrorSeverity(str, Enum):
    """错误严重程度枚举"""
    CRITICAL = "critical"               # 严重 - 系统不可用
    HIGH = "high"                       # 高 - 核心功能受影响
    MEDIUM = "medium"                   # 中 - 功能受限
    LOW = "low"                         # 低 - 非关键功能
    INFO = "info"                       # 信息 - 不影响功能


class RootCauseCategory(str, Enum):
    """根因类别枚举"""
    CODE_BUG = "code_bug"               # 代码 Bug
    CONFIGURATION_ERROR = "configuration_error"  # 配置错误
    DEPENDENCY_ISSUE = "dependency_issue"  # 依赖问题
    DATA_INCONSISTENCY = "data_inconsistency"  # 数据不一致
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # 资源耗尽
    INTEGRATION_ERROR = "integration_error"  # 集成问题
    DESIGN_FLAW = "design_flaw"         # 设计缺陷
    EXTERNAL_SERVICE = "external_service"  # 外部服务问题


class FixPriority(str, Enum):
    """修复优先级"""
    IMMEDIATE = "immediate"             # 立即修复
    URGENT = "urgent"                   # 紧急
    NORMAL = "normal"                   # 正常
    LOW = "low"                         # 低优先级
    DEPRECATED = "deprecated"           # 已废弃，不需修复


class TestCaseType(str, Enum):
    """测试用例类型"""
    POSITIVE = "positive"               # 正向测试
    NEGATIVE = "negative"               # 负向测试
    EDGE_CASE = "edge_case"             # 边界测试
    REGRESSION = "regression"           # 回归测试


# =============================================================================
# 基础模型
# =============================================================================

class RequestInfo(BaseModel):
    """HTTP 请求信息"""
    method: str = Field(..., description="HTTP 方法 (GET, POST, PUT, DELETE)")
    url: str = Field(..., description="请求 URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    query_params: Dict[str, Any] = Field(default_factory=dict, description="查询参数")
    body: Optional[Dict[str, Any]] = Field(None, description="请求体")
    content_type: Optional[str] = Field(None, description="Content-Type")


class ResponseInfo(BaseModel):
    """HTTP 响应信息"""
    status_code: int = Field(..., description="HTTP 状态码")
    headers: Dict[str, str] = Field(default_factory=dict, description="响应头")
    body: Optional[Dict[str, Any]] = Field(None, description="响应体")
    content_type: Optional[str] = Field(None, description="Content-Type")
    elapsed_ms: Optional[float] = Field(None, description="响应耗时 (毫秒)")


class EndpointInfo(BaseModel):
    """API 端点信息"""
    path: str = Field(..., description="端点路径")
    method: str = Field(..., description="HTTP 方法")
    description: Optional[str] = Field(None, description="端点描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数定义")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="响应 Schema")


# =============================================================================
# Agent 输入输出模型
# =============================================================================

class UserInput(BaseModel):
    """用户输入模型"""
    input_type: InputType = Field(..., description="输入类型")
    content: str = Field(..., description="输入内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="输入时间")


class SemanticAnalysisResult(BaseModel):
    """语义分析结果 - Agent 1 输出"""
    request_info: Optional[RequestInfo] = Field(None, description="请求信息")
    response_info: Optional[ResponseInfo] = Field(None, description="响应信息")
    endpoint_info: Optional[EndpointInfo] = Field(None, description="端点信息")
    error_category: Optional[ErrorCategory] = Field(None, description="错误类别")
    error_code: Optional[str] = Field(None, description="错误码")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="错误详情")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="提取的关键字段")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="分析置信度")


class RootCauseAnalysisResult(BaseModel):
    """根因分析结果 - Agent 2 输出"""
    root_cause_category: Optional[RootCauseCategory] = Field(None, description="根因类别")
    root_cause_description: str = Field(..., description="根因描述")
    possible_causes: List[str] = Field(default_factory=list, description="可能的原因列表")
    affected_components: List[str] = Field(default_factory=list, description="受影响的组件")
    related_logs: List[Dict[str, Any]] = Field(default_factory=list, description="相关日志")
    correlation_chain: List[str] = Field(default_factory=list, description="关联链路")


class FixStrategy(BaseModel):
    """修复策略 - Agent 2 输出"""
    priority: FixPriority = Field(..., description="修复优先级")
    suggestions: List[str] = Field(default_factory=list, description="修复建议列表")
    code_changes: List[Dict[str, Any]] = Field(default_factory=list, description="代码变更建议")
    configuration_changes: List[Dict[str, Any]] = Field(default_factory=list, description="配置变更建议")
    estimated_effort: Optional[str] = Field(None, description="预估工作量")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="风险等级")
    validation_steps: List[str] = Field(default_factory=list, description="验证步骤")


class TestCase(BaseModel):
    """测试用例 - Agent 3 输出"""
    case_id: str = Field(..., description="用例 ID")
    name: str = Field(..., description="用例名称")
    description: str = Field(..., description="用例描述")
    case_type: TestCaseType = Field(..., description="用例类型")
    request: RequestInfo = Field(..., description="请求信息")
    expected_response: Optional[ResponseInfo] = Field(None, description="期望响应")
    expected_error: Optional[str] = Field(None, description="期望的错误")
    priority: int = Field(default=1, description="优先级 (1-5)")
    tags: List[str] = Field(default_factory=list, description="标签")


class TestSuite(BaseModel):
    """测试套件 - Agent 3 输出"""
    suite_name: str = Field(..., description="套件名称")
    test_cases: List[TestCase] = Field(default_factory=list, description="测试用例列表")
    setup_steps: List[str] = Field(default_factory=list, description="前置步骤")
    teardown_steps: List[str] = Field(default_factory=list, description="后置步骤")


class RegressionStrategy(BaseModel):
    """回归策略 - Agent 3 输出"""
    affected_endpoints: List[str] = Field(default_factory=list, description="受影响的端点")
    regression_priority: List[str] = Field(default_factory=list, description="回归优先级排序")
    suggested_test_suites: List[TestSuite] = Field(default_factory=list, description="建议的测试套件")
    smoke_tests: List[str] = Field(default_factory=list, description="冒烟测试列表")


# =============================================================================
# 最终报告模型
# =============================================================================

class DiagnosticReport(BaseModel):
    """完整诊断报告 - Supervisor 最终输出"""
    report_id: str = Field(..., description="报告 ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="生成时间")

    # 输入摘要
    input_summary: UserInput = Field(..., description="输入摘要")

    # 各 Agent 结果
    semantic_analysis: SemanticAnalysisResult = Field(..., description="语义分析结果")
    root_cause_analysis: RootCauseAnalysisResult = Field(..., description="根因分析结果")
    fix_strategy: FixStrategy = Field(..., description="修复策略")
    test_suite: TestSuite = Field(..., description="测试套件")
    regression_strategy: RegressionStrategy = Field(..., description="回归策略")

    # 综合评估
    overall_severity: ErrorSeverity = Field(..., description="整体严重程度")
    estimated_fix_time: Optional[str] = Field(None, description="预估修复时间")
    recommendations: List[str] = Field(default_factory=list, description="综合建议")

    # 元数据
    agent_execution_log: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent 执行日志"
    )


# =============================================================================
# Agent 内部消息模型
# =============================================================================

class AgentMessage(BaseModel):
    """Agent 间通信消息"""
    sender: str = Field(..., description="发送方 Agent")
    receiver: str = Field(..., description="接收方 Agent")
    message_type: str = Field(..., description="消息类型")
    content: Dict[str, Any] = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    """Agent 状态"""
    agent_id: str = Field(..., description="Agent ID")
    status: Literal["idle", "processing", "completed", "error"] = Field(default="idle")
    current_task: Optional[str] = Field(None, description="当前任务")
    memory: Dict[str, Any] = Field(default_factory=dict, description="Agent 记忆")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="指标")


# =============================================================================
# Skill 执行结果模型
# =============================================================================

class SkillResult(BaseModel):
    """Skill 执行结果"""
    skill_name: str = Field(..., description="Skill 名称")
    success: bool = Field(..., description="是否成功")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time_ms: float = Field(..., description="执行时间 (毫秒)")
    tools_used: List[str] = Field(default_factory=list, description="使用的 Tool 列表")


class ToolResult(BaseModel):
    """Tool 执行结果"""
    tool_name: str = Field(..., description="Tool 名称")
    success: bool = Field(..., description="是否成功")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time_ms: float = Field(..., description="执行时间 (毫秒)")
