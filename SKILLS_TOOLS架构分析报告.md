# Skills 与 Tools 架构分析报告

## 目录

- [1. 架构概览](#架构概览)
- [2. Tool 层详细分析](#tool-层详细分析)
- [3. Skill 层详细分析](#skill-层详细分析)
- [4. Skill 与 Tool 的核心区别](#skill-与-tool-的核心区别)
- [5. 数据流转关系](#数据流转关系)
- [6. 设计模式总结](#设计模式总结)

---

## 架构概览

本项目采用**三层架构**设计，从底层的原子能力到顶层的自主决策实体：

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Agent 层                              │
│  (LLM 驱动、自主决策、状态管理、记忆能力）            │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Skill 层                               │
│  (面向任务、组织多个 Tool、有执行策略和流程）        │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Tool 层                                │
│  (原子能力、无状态、单一职责、纯功能、可独立测试）      │
└─────────────────────────────────────────────────────────────────────┘
```

### 层级对比

| 层级 | 职责 | 状态 | 复杂度 | 示例 |
|------|------|------|--------|------|
| **Tool** | 原子功能 | 无状态/状态隔离 | 低 | JSON解析、错误分类 |
| **Skill** | 面向任务的策略性能力 | 可有配置 | 中 | API语义分析 |
| **Agent** | LLM 驱动的自主决策实体 | 有状态和记忆 | 高 | 语义分析 Agent |

---

## Tool 层详细分析

### 1. BaseTool 抽象基类

**文件位置：** `src/tools/base.py`

**核心属性：**

```python
class BaseTool(ABC):
    tool_name: str              # 工具唯一标识
    tool_description: str         # 工具描述
    tool_version: str            # 版本信息
    config: Dict[str, Any]       # 配置参数
```

**核心方法：**

| 方法 | 说明 | 返回类型 |
|------|------|----------|
| `execute()` | 抽象方法，子类必须实现核心逻辑 | `ToolResult` |
| `_execute_with_timing()` | 带计时和错误处理的包装器 | `ToolResult` |
| `validate_input()` | 验证输入数据有效性 | `bool` |
| `get_schema()` | 获取工具的 Schema 定义 | `Dict` |

### 2. ToolContext 上下文类

**作用：** 传递 Tool 执行所需的上下文信息

```python
@dataclass
class ToolContext:
    agent_id: str              # 调用此 Tool 的 Agent ID
    skill_name: str            # 调用此 Tool 的 Skill 名称
    session_id: str            # 会话唯一标识
    metadata: Dict[str, Any]   # 额外的元数据
```

### 3. ToolResult 结果模型

**定义在：** `src/models/schemas.py`

```python
class ToolResult(BaseModel):
    tool_name: str              # 工具名称
    success: bool              # 是否执行成功
    result: Any                # 执行结果
    error: Optional[str]        # 错误信息
    execution_time_ms: float    # 执行耗时（毫秒）
```

### 4. ToolRegistry 注册表

**设计模式：** 单例模式 (Singleton)

**功能：**
- 管理 Tool 类的注册和查找
- 全局唯一实例
- 提供 `register()`, `get()`, `list_all()`, `clear()` 方法

### 5. 具体 Tool 实现

#### 5.1 JSONParserTool

**文件位置：** `src/tools/parsers/json_parser_tool.py`

**功能：**
- 解析 JSON 字符串为 Python 对象
- 支持嵌套字段提取（使用点表示法）
- 验证 JSON 格式有效性

**特性：**
- 纯函数式设计，无状态
- 支持配置编码（默认 UTF-8）
- 完整的错误处理

**使用示例：**
```python
# 基本解析
tool = JSONParserTool()
result = await tool.execute('{"name": "John"}', context)

# 字段提取
result = await tool.execute({
    "json_str": '{"user": {"name": "John"}}',
    "field_path": "user.name"
}, context)
```

#### 5.2 ErrorClassifierTool

**文件位置：** `src/tools/classifiers/error_classifier_tool.py`

**功能：**
- 基于 HTTP 状态码识别错误类型
- 基于错误消息进行关键词匹配
- 推断错误严重程度

**状态码映射：**

| 状态码 | 错误类别 | 严重程度 | 说明 |
|--------|----------|----------|------|
| 400 | VALIDATION_ERROR | MEDIUM | 客户端请求参数错误 |
| 401/403 | AUTH_ERROR | HIGH | 认证/授权失败 |
| 404 | HTTP_ERROR | MEDIUM | 资源不存在 |
| 409 | BUSINESS_ERROR | MEDIUM | 冲突 |
| 422 | VALIDATION_ERROR | MEDIUM | 语义验证失败 |
| 429 | HTTP_ERROR | HIGH | 请求过多 |
| 500 | DATABASE_ERROR | CRITICAL | 数据库错误 |
| 502 | NETWORK_ERROR | CRITICAL | 网关错误 |
| 503 | HTTP_ERROR | CRITICAL | 服务不可用 |
| 504 | TIMEOUT_ERROR | CRITICAL | 超时错误 |

**关键词分类逻辑：**
- 超时错误：timeout, timed out, deadline
- 认证错误：unauthorized, forbidden, authentication
- 网络错误：network, connection, dns
- 数据库错误：database, sql, query
- 验证错误：validation, invalid, required

---

## Skill 层详细分析

### 1. BaseSkill 抽象基类

**文件位置：** `src/skills/base.py`

**核心属性：**

```python
class BaseSkill(ABC):
    skill_name: str              # Skill 唯一标识
    skill_description: str         # Skill 描述
    skill_version: str            # 版本信息
    config: Dict[str, Any]       # 配置参数
    _tools: Dict[str, BaseTool]  # 依赖的 Tool 实例
    _tool_registry: ToolRegistry  # Tool 注册表
```

**核心方法：**

| 方法 | 说明 | 返回类型 |
|------|------|----------|
| `execute()` | 抽象方法，子类必须实现核心逻辑 | `SkillResult` |
| `register_tool()` | 注册 Tool 到 Skill | `None` |
| `get_tool()` | 获取已注册的 Tool | `Optional[BaseTool]` |
| `execute_tool()` | 执行指定的 Tool | `ToolResult` |
| `execute_tool_chain()` | 执行 Tool 链（串行） | `List[ToolResult]` |
| `execute_tools_parallel()` | 并行执行多个 Tools | `List[ToolResult]` |
| `_execute_with_timing()` | 带计时的执行包装器 | `SkillResult` |
| `validate_input()` | 验证输入数据 | `bool` |
| `get_schema()` | 获取 Skill Schema | `Dict` |

### 2. SkillContext 上下文类

**作用：** 传递 Skill 执行所需的上下文信息

```python
@dataclass
class SkillContext:
    agent_id: str              # 调用此 Skill 的 Agent ID
    session_id: str            # 会话唯一标识
    task_id: Optional[str]       # 任务 ID
    metadata: Dict[str, Any]   # 额外元数据
    shared_memory: Dict[str, Any]  # 共享记忆（跨 Agent）
```

**方法：**
- `get_tool_context(skill_name)` - 为指定 Tool 创建上下文

### 3. SkillResult 结果模型

**定义在：** `src/models/schemas.py`

```python
class SkillResult(BaseModel):
    skill_name: str              # Skill 名称
    success: bool              # 是否执行成功
    result: Optional[Dict[str, Any]]  # 执行结果
    error: Optional[str]        # 错误信息
    execution_time_ms: float    # 执行耗时（毫秒）
    tools_used: List[str]      # 使用的 Tool 列表
```

### 4. SkillRegistry 注册表

**设计模式：** 单例模式 (Singleton)

**功能：**
- 管理 Skill 类的注册和查找
- 全局唯一实例
- 提供 `register()`, `get()`, `list_all()`, `clear()` 方法

### 5. 具体 Skill 实现

#### 5.1 APIAnalysisSkill

**文件位置：** `src/skills/semantic_analysis/api_analysis_skill.py`

**功能：**
- 完整的 API 语义分析流程
- 解析请求和响应数据
- 提取端点信息
- 识别关键字段
- 计算分析置信度

**依赖的 Tools：**
1. `json_parser` - JSONParserTool
2. `error_classifier` - ErrorClassifierTool

**执行流程：**

```
输入数据
  ↓
[步骤 1] 解析请求 (使用 json_parser)
  → RequestInfo (method, url, headers, body, content_type)
  ↓
[步骤 2] 解析响应 (使用 json_parser)
  → ResponseInfo (status_code, headers, body, content_type, elapsed_ms)
  ↓
[步骤 3] 提取端点信息
  → EndpointInfo (path, method, description, parameters, response_schema)
  ↓
[步骤 4] 错误分类 (使用 error_classifier)
  → ErrorCategory & ErrorSeverity
  ↓
[步骤 5] 提取关键字段
  → Dict of extracted_fields
  ↓
[步骤 6] 计算置信度
  → float (0.0 - 1.0)
  ↓
SkillResult
```

**结果结构：**

```python
{
    "request_info": {
        "method": "POST",
        "url": "https://api.example.com/products",
        "headers": {...},
        "query_params": {...},
        "body": {...},
        "content_type": "application/json"
    },
    "response_info": {
        "status_code": 500,
        "headers": {...},
        "body": {...},
        "content_type": "application/json",
        "elapsed_ms": 150.5
    },
    "endpoint_info": {
        "path": "/products",
        "method": "POST",
        "description": "Create product endpoint",
        "parameters": {...},
        "response_schema": {...}
    },
    "error_category": "database_error",
    "error_severity": "critical",
    "error_details": {...},
    "extracted_fields": {...},
    "confidence": 0.85
}
```

---

## Skill 与 Tool 的核心区别

### 1. 抽象层级对比

| 维度 | Tool | Skill |
|------|------|-------|
| **职责范围** | 单一职责，执行一个原子操作 | 面向任务，组织多个 Tool 完成复杂目标 |
| **状态管理** | 无状态（或状态隔离） | 可有配置和执行状态 |
| **决策能力** | 无决策，纯执行流程 | 有执行策略和流程控制 |
| **LLM 依赖** | 不依赖 LLM，纯逻辑实现 | 可能依赖 LLM 进行复杂决策 |
| **可组合性** | 原子级别，不可再分 | 可组合多个 Tool 完成任务 |

### 2. 依赖关系对比

```
Skill
  ↓ 拥有/依赖
  ├─→ Tool 1
  ├─→ Tool 2
  └─→ Tool N
```

**示例：**
- `APIAnalysisSkill` 拥有 `JSONParserTool` 和 `ErrorClassifierTool`
- Skill 负责组织和协调这些 Tool 的执行
- Tool 只关注自己的功能实现

### 3. 执行模式对比

#### Tool 执行模式：
```python
# 简单直接执行
result = await tool.execute(input_data, context)

# 自动带计时和错误处理
result = await tool._execute_with_timing(input_data, context)
```

#### Skill 执行模式：

```python
# 串行执行 Tool 链
results = await skill.execute_tool_chain([
    ("tool1", transform_func1),
    ("tool2", transform_func2),
    ("tool3", None)
], initial_data, context)

# 并行执行多个 Tools
configs = [
    {"name": "tool1", "input_data": data1},
    {"name": "tool2", "input_data": data2}
]
results = await skill.execute_tools_parallel(configs, context)
```

### 4. 错误处理对比

**Tool 级别：**
```python
return ToolResult(
    tool_name=self.tool_name,
    success=False,
    result=None,
    error=str(exception),  # 直接返回错误
    execution_time_ms=0
)
```

**Skill 级别：**
```python
return SkillResult(
    skill_name=self.skill_name,
    success=False,
    result=None,
    error=str(exception),
    execution_time_ms=0,
    tools_used=["tool1", "tool2", ...]  # 还记录使用了哪些 Tool
)
```

### 5. 扩展性对比

| 扩展点 | Tool | Skill |
|--------|------|-------|
| **新增功能** | 创建新的 Tool 子类 | 创建新的 Skill 子类 |
| **注册方式** | `ToolRegistry.register()` | `SkillRegistry.register()` |
| **配置管理** | 通过 `__init__` 参数 | 通过 `__init__` 参数 |
| **工具组合** | 不适用 | 可以动态注册多个 Tool |

---

## 数据流转关系

### 1. 自底向上的数据流

```
用户输入数据
  ↓
┌─────────────────────────────────────┐
│  Tool: JSONParserTool          │  ← 处理 JSON 字符串
│  输入: {"json_str": "..."}      │
│  输出: Python Dict              │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  Tool: ErrorClassifierTool       │  ← 分类错误类型
│  输入: status_code, message      │
│  输出: category, severity       │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  Skill: APIAnalysisSkill          │  ← 组织多个 Tool 结果
│  输入: 原始 API 数据         │
│  使用: json_parser,              │
│        error_classifier             │
│  输出: SemanticAnalysisResult  │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  Agent: SemanticAnalyzerAgent     │  ← LLM 驱动的决策
│  输入: 用户原始数据            │
│  使用: api_analysis skill         │
│  输出: Dict (分析结果）        │
└─────────────────────────────────────┘
```

### 2. 上下文传播链

```
AgentContext
  ↓ (调用)
  ├──→ SkillContext
  │      └──→ ToolContext
  │
  ├──→ 共享记忆 (shared_memory)
  │      └──→ 跨 Agent 共享
```

**上下文包含的信息层次：**

| 上下文类型 | 包含信息 | 作用 |
|------------|----------|------|
| `ToolContext` | agent_id, skill_name, session_id, metadata | Tool 执行时知道调用来源 |
| `SkillContext` | agent_id, session_id, task_id, metadata, shared_memory | Skill 执行时可访问共享记忆 |
| `AgentContext` | session_id, task_id, metadata, shared_memory | Agent 执行时管理会话状态 |

### 3. 结果返回链

```
ToolResult
  ↓ (被 Skill 包装)
SkillResult
  ↓ (被 Agent 使用)
Dict[str, Any]
  ↓ (被 Supervisor 聚合)
DiagnosticReport
```

---

## 设计模式总结

### 1. 使用的设计模式

#### 1.1 单例模式 (Singleton Pattern)

**应用位置：**
- `ToolRegistry`
- `SkillRegistry`
- `AgentRegistry`

**目的：** 确保全局只有一个注册表实例

**实现：**
```python
class ToolRegistry:
    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, type] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

#### 1.2 策略模式 (Strategy Pattern)

**应用位置：**
- `BaseSkill` 的 `execute_tool()` 等方法
- 允许 Skill 灵活选择执行策略（串行、并行）

#### 1.3 模板方法模式 (Template Method Pattern)

**应用位置：**
- `BaseTool._execute_with_timing()` - 执行前后自动添加计时
- `BaseSkill._execute_with_timing()` - 执行前后自动添加计时和工具追踪

#### 1.4 责任链模式 (Chain of Responsibility Pattern)

**应用位置：**
- `Skill.execute_tool_chain()` - 一个 Tool 的输出传递给下一个
- 支持数据转换函数在链中间

#### 1.5 工厂模式 (Factory Pattern)

**应用位置：**
- `ToolRegistry.get(tool_name)` - 根据名称创建 Tool 实例
- `SkillRegistry.get(skill_name)` - 根据 Skill 名称创建实例

### 2. 架构优势

| 优势 | 说明 |
|------|------|
| **可测试性** | Tool 可独立单元测试，无需依赖 Skill/Agent |
| **可复用性** | Tool 可在多个 Skill 中复用 |
| **可维护性** | 职责分离使代码更易维护 |
| **可扩展性** | 新增 Tool 不影响现有 Skill，新增 Skill 不影响 Agent |
| **性能优化** | Tool 可针对性优化，Skill 可并行执行多个 Tool |
| **错误隔离** | Tool 错误不会影响整个系统，有清晰的错误边界 |

### 3. 最佳实践

#### Tool 开发最佳实践：

1. **单一职责** - 每个 Tool 只做一件事
2. **无状态设计** - 不依赖外部状态，只基于输入产生输出
3. **完整错误处理** - 所有异常都应返回结构化的 `ToolResult`
4. **输入验证** - 实现 `validate_input()` 方法
5. **文档完善** - 清晰的 `tool_name` 和 `tool_description`

#### Skill 开发最佳实践：

1. **组织 Tool** - 合理组织多个 Tool 完成任务
2. **执行策略** - 使用 `execute_tool_chain()` 或 `execute_tools_parallel()`
3. **结果聚合** - 将多个 Tool 结果组合成有意义的结果
4. **共享记忆使用** - 通过 `SkillContext.shared_memory` 与其他 Agent 协作
5. **工具追踪** - 在 `SkillResult` 中记录使用的 Tool 列表

---

## 文件结构总览

```
src/
├── tools/                          # Tool 层
│   ├── __init__.py
│   ├── base.py                     # BaseTool 抽象基类
│   ├── parsers/                     # 解析器 Tools
│   │   ├── __init__.py
│   │   └── json_parser_tool.py    # JSON 解析 Tool
│   └── classifiers/                 # 分类器 Tools
│       ├── __init__.py
│       └── error_classifier_tool.py  # 错误分类 Tool
│
├── skills/                         # Skill 层
│   ├── __init__.py
│   ├── base.py                      # BaseSkill 抽象基类
│   └── semantic_analysis/
│       ├── __init__.py
│       └── api_analysis_skill.py    # API 语义分析 Skill
│
├── models/                         # 数据模型
│   ├── __init__.py
│   ├── schemas.py                   # Pydantic 模型定义
│   └── enums.py                     # 枚举定义
│
├── agents/                         # Agent 层
│   ├── __init__.py
│   ├── base.py                      # BaseAgent 抽象基类
│   ├── supervisor.py                 # Supervisor Agent
│   ├── semantic_analyzer.py           # 语义分析 Agent
│   ├── root_cause_strategist.py     # 根因分析 Agent
│   └── test_case_generator.py         # 测试用例生成 Agent
│
└── __init__.py                     # 系统入口点
```

---

## 总结

本项目通过清晰的三层架构设计，实现了从**原子能力**到**智能决策**的完整技术栈：

1. **Tool 层** - 提供可靠、可测试、可复用的基础功能
2. **Skill 层** - 组织多个 Tool 完成面向任务的复杂操作
3. **Agent 层** - 使用 LLM 进行自主决策，拥有状态和记忆

这种设计模式使得系统具有：
- 高度的模块化和可维护性
- 良好的可测试性
- 灵活的可扩展性
- 清晰的职责边界
