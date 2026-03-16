"""
API 分析 Skill - 语义分析能力
"""
from typing import Any, Dict, List
from src.skills.base import BaseSkill, SkillContext, SkillResult
from src.tools.parsers.json_parser_tool import JSONParserTool
from src.tools.classifiers.error_classifier_tool import ErrorClassifierTool
from src.models.schemas import RequestInfo, ResponseInfo, EndpointInfo


class APIAnalysisSkill(BaseSkill):
    """
    API 语义分析 Skill

    功能：
    - 完整的 API 语义分析流程
    - 解析请求和响应
    - 提取端点信息
    - 识别关键字段

    使用的 Tools：
    - json_parser_tool: 解析 JSON 数据
    - error_classifier_tool: 错误分类
    """

    skill_name = "api_analysis"
    skill_description = "Perform complete API semantic analysis"
    skill_version = "1.0.0"

    def __init__(
        self,
        config: Dict[str, Any] = None,
        tools: Dict[str, Any] = None
    ):
        super().__init__(config, tools)
        self._initialize_default_tools()

    def _initialize_default_tools(self):
        """初始化依赖的 Tools"""
        self.register_tool("json_parser", JSONParserTool(self.config))
        self.register_tool("error_classifier", ErrorClassifierTool(self.config))

    async def execute(
        self,
        input_data: Any,
        context: SkillContext
    ) -> SkillResult:
        """
        执行 API 语义分析

        Args:
            input_data: 用户输入数据
            context: 执行上下文

        Returns:
            SkillResult: 分析结果
        """
        try:
            # 步骤 1: 解析请求
            request_info = await self._analyze_request(input_data, context)
            tools_used = ["json_parser"]

            # 步骤 2: 解析响应
            response_info = await self._analyze_response(input_data, context)

            # 步骤 3: 错端点信息
            endpoint_info = await self._extract_endpoint(request_info, input_data)

            # 步骤 4: 错误分类
            classification_result = await self._classify_error(input_data, context)
            tools_used.append("error_classifier")

            # 组装结果
            result = {
                "request_info": request_info.model_dump() if request_info else None,
                "response_info": response_info.model_dump() if response_info else None,
                "endpoint_info": endpoint_info.model_dump() if endpoint_info else None,
                "error_category": classification_result.get("category"),
                "error_severity": classification_result.get("severity"),
                "error_details": classification_result.get("details", {}),
                "extracted_fields": self._extract_key_fields(
                    request_info,
                    response_info,
                    endpoint_info
                ),
                "confidence": self._calculate_confidence(
                    request_info,
                    response_info,
                    classification_result
                )
            }

            return SkillResult(
                skill_name=self.skill_name,
                success=True,
                result=result,
                error=None,
                execution_time_ms=0,
                tools_used=tools_used
            )

        except Exception as e:
            return SkillResult(
                skill_name=self.skill_name,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=0,
                tools_used=["json_parser", "error_classifier"]
            )

    async def _analyze_request(
        self,
        input_data: Any,
        context: SkillContext
    ) -> RequestInfo:
        """分析请求信息"""
        request_data = None

        if isinstance(input_data, dict):
            if "request" in input_data:
                request_data = input_data["request"]
            elif "req" in input_data:
                request_data = input_data["req"]

        if not request_data:
            return None

        # 提取基本信息
        method = request_data.get("method", "GET")
        url = request_data.get("url", "")
        headers = request_data.get("headers", {})
        query_params = request_data.get("query_params", {})

        # 解析 Body
        body = None
        if "body" in request_data:
            body_data = request_data["body"]
            if isinstance(body_data, str):
                # 使用 JSON Parser 解析
                parser_result = await self.execute_tool(
                    "json_parser",
                    {"json_str": body_data},
                    context
                )
                if parser_result.success:
                    body = parser_result.result
            else:
                body = body_data

        content_type = headers.get("Content-Type") or headers.get("content-type")

        return RequestInfo(
            method=method,
            url=url,
            headers=headers,
            query_params=query_params,
            body=body,
            content_type=content_type
        )

    async def _analyze_response(
        self,
        input_data: Any,
        context: SkillContext
    ) -> ResponseInfo:
        """分析响应信息"""
        response_data = None

        if isinstance(input_data, dict):
            if "response" in input_data:
                response_data = input_data["response"]
            elif "resp" in input_data:
                response_data = input_data["resp"]

        if not response_data:
            return None

        # 提取基本信息
        status_code = response_data.get("status_code", response_data.get("status", 200))
        headers = response_data.get("headers", {})

        # 解析 Body
        body = None
        if "body" in response_data:
            body_data = response_data["body"]
            if isinstance(body_data, str):
                parser_result = await self.execute_tool(
                    "json_parser",
                    {"json_str": body_data},
                    context
                )
                if parser_result.success:
                    body = parser_result.result
            else:
                body = body_data

        content_type = headers.get("Content-Type") or headers.get("content-type")
        elapsed_ms = response_data.get("elapsed_ms")

        return ResponseInfo(
            status_code=status_code,
            headers=headers,
            body=body,
            content_type=content_type,
            elapsed_ms=elapsed_ms
        )

    async def _extract_endpoint(
        self,
        request_info: RequestInfo,
        input_data: Any
    ) -> EndpointInfo:
        """提取端点信息"""
        if not request_info:
            return None

        # 从 URL 提取路径
        from urllib.parse import urlparse
        parsed_url = urlparse(request_info.url)
        path = parsed_url.path

        # 从输入中获取额外信息
        description = None
        parameters = {}
        response_schema = None

        if isinstance(input_data, dict):
            if "endpoint_info" in input_data:
                endpoint_info = input_data["endpoint_info"]
                description = endpoint_info.get("description")
                parameters = endpoint_info.get("parameters", {})
                response_schema = endpoint_info.get("response_schema")

        return EndpointInfo(
            path=path,
            method=request_info.method,
            description=description,
            parameters=parameters,
            response_schema=response_schema
        )

    async def _classify_error(
        self,
        input_data: Any,
        context: SkillContext
    ) -> Dict[str, Any]:
        """分类错误"""
        classifier_result = await self.execute_tool(
            "error_classifier",
            input_data,
            context
        )

        if classifier_result.success and classifier_result.result:
            return classifier_result.result

        return {
            "category": None,
            "severity": None,
            "details": {}
        }

    def _extract_key_fields(
        self,
        request_info: RequestInfo,
        response_info: ResponseInfo,
        endpoint_info: EndpointInfo
    ) -> Dict[str, Any]:
        """提取关键字段"""
        fields = {}

        if request_info:
            fields["method"] = request_info.method
            fields["url"] = request_info.url
            if request_info.body:
                fields["request_body_keys"] = list(request_info.body.keys())

        if response_info:
            fields["status_code"] = response_info.status_code
            if response_info.body:
                fields["response_body_keys"] = list(response_info.body.keys())

        if endpoint_info:
            fields["endpoint_path"] = endpoint_info.path
            fields["endpoint_method"] = endpoint_info.method

        return fields

    def _calculate_confidence(
        self,
        request_info: RequestInfo,
        response_info: ResponseInfo,
        classification_result: Dict[str, Any]
    ) -> float:
        """计算分析置信度"""
        score = 0.0
        max_score = 3.0

        if request_info:
            score += 1.0
        if response_info:
            score += 1.0
        if classification_result.get("category"):
            score += 1.0

        return round(score / max_score, 2)
