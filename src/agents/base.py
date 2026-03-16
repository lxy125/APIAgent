"""
Agent 基类 - 定义 Agent 的统一接口和基础功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import logging
import uuid

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from src.skills.base import BaseSkill, SkillContext, SkillRegistry
from src.models.schemas import (
    SkillResult,
    AgentState,
    AgentMessage,
    SemanticAnalysisResult,
    RootCauseAnalysisResult,
    FixStrategy,
    TestSuite,
    RegressionStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Agent 执行上下文"""
    session_id: str
    task_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)

    def get_skill_context(self, agent_id: str) -> SkillContext:
        """创建 Skill 上下文"""
        return SkillContext(
            agent_id=agent_id,
            session_id=self.session_id,
            task_id=self.task_id,
            metadata=self.metadata
        )


class BaseAgent(ABC):
    """
    Agent 基类

    Agent 是自主决策实体，特征：
    - 有身份和状态
    - LLM 驱动的自主决策能力
    - 拥有多个 Skills
    - 可以与其它 Agent 通信
    - 有记忆和学习能力
    """

    agent_id: str = "base_agent"
    agent_name: str = "Base Agent"
    agent_description: str = "Base agent class"
    agent_version: str = "1.0.0"

    def __init__(
        self,
        llm: BaseChatModel,
        config: Optional[Dict[str, Any]] = None,
        skills: Optional[Dict[str, BaseSkill]] = None
    ):
        """
        初始化 Agent

        Args:
            llm: LangChain LLM 实例
            config: Agent 配置
            skills: 依赖的 Skill 实例字典
        """
        self.llm = llm
        self.config = config or {}
        self._skills = skills or {}
        self._state = AgentState(agent_id=self.agent_id)
        self._memory: List[BaseMessage] = []
        self._skill_registry = SkillRegistry()

        # 初始化默认 Skills
        self._initialize_default_skills()

        # 初始化系统提示
        self._initialize_system_prompt()

    def _initialize_default_skills(self):
        """
        初始化默认 Skills
        子类可以重写此方法来定义默认依赖的 Skills
        """
        pass

    def _initialize_system_prompt(self):
        """
        初始化系统提示
        子类可以重写此方法来定义 Agent 的系统提示
        """
        self._system_prompt = f"""
You are {self.agent_name}, a helpful agent with the following description:
{self.agent_description}

Your ID is: {self.agent_id}
Available skills: {', '.join(self._skills.keys())}

Think step by step and decide which skills to use for each task.
"""

    @abstractmethod
    async def process(
        self,
        input_data: Any,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        处理输入并返回结果

        Args:
            input_data: 输入数据
            context: Agent 上下文

        Returns:
            Dict: 处理结果
        """
        pass

    def register_skill(self, name: str, skill: BaseSkill):
        """注册 Skill"""
        self._skills[name] = skill
        logger.debug(f"Skill '{name}' registered to agent '{self.agent_id}'")

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取 Skill"""
        return self._skills.get(name)

    async def execute_skill(
        self,
        skill_name: str,
        input_data: Any,
        context: AgentContext
    ) -> SkillResult:
        """
        执行指定的 Skill

        Args:
            skill_name: Skill 名称
            input_data: 输入数据
            context: Agent 上下文

        Returns:
            SkillResult: Skill 执行结果
        """
        skill = self.get_skill(skill_name)
        if not skill:
            logger.error(f"Skill '{skill_name}' not found in agent '{self.agent_id}'")
            return SkillResult(
                skill_name=skill_name,
                success=False,
                result=None,
                error=f"Skill '{skill_name}' not found",
                execution_time_ms=0
            )

        skill_context = context.get_skill_context(self.agent_id)
        logger.info(f"Agent '{self.agent_id}' executing skill '{skill_name}'")

        return await skill._execute_with_timing(input_data, skill_context)

    def add_to_memory(self, message: BaseMessage):
        """添加消息到记忆"""
        self._memory.append(message)
        # 限制记忆长度
        if len(self._memory) > 100:
            self._memory = self._memory[-100:]

    def get_memory(self, n: Optional[int] = None) -> List[BaseMessage]:
        """获取记忆"""
        if n is None:
            return self._memory
        return self._memory[-n:]

    def clear_memory(self):
        """清空记忆"""
        self._memory.clear()

    async def think(self, prompt: str) -> str:
        """
        使用 LLM 进行推理

        Args:
            prompt: 输入提示

        Returns:
            str: LLM 输出
        """
        # 构建消息序列
        messages = [HumanMessage(content=self._system_prompt)]
        messages.extend(self.get_memory())
        messages.append(HumanMessage(content=prompt))

        # 调用 LLM
        response = await self.llm.ainvoke(messages)

        # 添加到记忆
        self.add_to_memory(HumanMessage(content=prompt))
        self.add_to_memory(AIMessage(content=response.content))

        return response.content

    async def decide_skills(
        self,
        task_description: str,
        available_skills: List[str]
    ) -> List[str]:
        """
        决定使用哪些 Skills

        Args:
            task_description: 任务描述
            available_skills: 可用的 Skills 列表

        Returns:
            List[str]: 选择的 Skills 列表
        """
        prompt = f"""
Task: {task_description}

Available Skills:
{', '.join(available_skills)}

Please decide which skills to use for this task.
Return a JSON list of skill names to use, in order of execution.
Example: ["skill1", "skill2"]
"""

        response = await self.think(prompt)
        # 这里需要解析 JSON 响应，简化处理
        # 实际实现应该使用 JSON parser
        return [s.strip() for s in response if s in available_skills]

    def update_state(
        self,
        status: Optional[str] = None,
        current_task: Optional[str] = None,
        **kwargs
    ):
        """更新 Agent 状态"""
        if status:
            self._state.status = status
        if current_task:
            self._state.current_task = current_task
        self._state.memory.update(kwargs)

    def get_state(self) -> AgentState:
        """获取 Agent 状态"""
        return self._state

    def receive_message(self, message: AgentMessage):
        """接收来自其他 Agent 的消息"""
        if message.receiver == self.agent_id:
            logger.info(
                f"Agent '{self.agent_id}' received message from '{message.sender}': "
                f"{message.message_type}"
            )
            # 处理消息
            self._handle_message(message)

    def send_message(
        self,
        receiver: str,
        message_type: str,
        content: Dict[str, Any]
    ) -> AgentMessage:
        """发送消息给其他 Agent"""
        return AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            content=content
        )

    def _handle_message(self, message: AgentMessage):
        """
        处理接收到的消息
        子类可以重写此方法来实现特定的消息处理逻辑
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """获取 Agent 的 Schema"""
        return {
            "id": self.agent_id,
            "name": self.agent_name,
            "description": self.agent_description,
            "version": self.agent_version,
            "skills": list(self._skills.keys()),
            "state": self._state.model_dump()
        }


class AgentRegistry:
    """
    Agent 注册表 - 管理 Agent 的注册和查找
    """

    _instance: Optional["AgentRegistry"] = None
    _agents: Dict[str, type] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, agent_class: type):
        """注册 Agent 类"""
        # 创建临时实例来获取 agent_id
        temp_instance = agent_class(llm=None)
        cls._agents[temp_instance.agent_id] = agent_class
        return agent_class

    @classmethod
    def get(cls, agent_id: str) -> Optional[type]:
        """获取 Agent 类"""
        return cls._agents.get(agent_id)

    @classmethod
    def list_all(cls) -> list:
        """列出所有 Agent"""
        return list(cls._agents.keys())

    @classmethod
    def clear(cls):
        """清空注册表"""
        cls._agents.clear()
