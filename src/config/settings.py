"""
配置管理
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """LLM 配置"""
    provider: str = Field(default="anthropic", description="LLM 提供商")
    model: str = Field(default="glm-4.7", description="模型名称")
    temperature: float = Field(default=0.1, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大 token 数")
    api_key: str = Field(default="96473256-1632-46df-adb2-1a5fe9e0ad6b", description="API Key")
    base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/coding", description="API Base URL")
    timeout: int = Field(default=60, description="超时时间（秒）")


class AgentSettings(BaseSettings):
    """Agent 配置"""
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟（秒）")
    execution_timeout: int = Field(default=300, description="执行超时（秒）")
    memory_limit: int = Field(default=100, description="记忆条数限制")


class SkillSettings(BaseSettings):
    """Skill 配置"""
    default_timeout: int = Field(default=120, description="默认超时（秒）")
    tool_parallelism: int = Field(default=3, description="Tool 并行数")


class ToolSettings(BaseSettings):
    """Tool 配置"""
    default_timeout: int = Field(default=30, description="默认超时（秒）")
    enable_caching: bool = Field(default=True, description="启用缓存")
    cache_ttl: int = Field(default=3600, description="缓存 TTL（秒）")


class Settings(BaseSettings):
    """全局配置"""
    # LLM 配置
    llm: LLMSettings = Field(default_factory=LLMSettings)

    # Agent 配置
    agent: AgentSettings = Field(default_factory=AgentSettings)

    # Skill 配置
    skill: SkillSettings = Field(default_factory=SkillSettings)

    # Tool 配置
    tool: ToolSettings = Field(default_factory=ToolSettings)

    # 应用配置
    app_name: str = "API Bug Diagnosis System"
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"


# 创建默认配置实例
default_settings = Settings()
