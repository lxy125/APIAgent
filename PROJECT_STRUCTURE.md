api_bug_diagnosis_system/
├── pyproject.toml                          # 项目配置
├── requirements.txt                        # Python 依赖
├── README.md                               # 项目说明
│
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                    # 配置管理
│   │   └── prompts.py                     # LLM Prompt 模板
│   │
│   ├── agents/                             # Agent 层
│   │   ├── __init__.py
│   │   ├── base.py                        # Agent 基类
│   │   ├── supervisor.py                  # Supervisor Agent
│   │   ├── semantic_analyzer.py           # Semantic Analyzer Agent
│   │   ├── root_cause_strategist.py       # Root Cause Agent
│   │   └── test_case_generator.py         # Test Case Generator Agent
│   │
│   ├── skills/                             # Skill 层
│   │   ├── __init__.py
│   │   ├── base.py                        # Skill 基类
│   │   ├── supervisor/
│   │   │   ├── __init__.py
│   │   │   ├── routing_skill.py
│   │   │   ├── coordination_skill.py
│   │   │   └── aggregation_skill.py
│   │   ├── semantic_analysis/
│   │   │   ├── __init__.py
│   │   │   ├── api_analysis_skill.py
│   │   │   └── error_classification_skill.py
│   │   ├── root_cause/
│   │   │   ├── __init__.py
│   │   │   ├── root_cause_analysis_skill.py
│   │   │   └── fix_strategy_skill.py
│   │   └── test_generation/
│   │       ├── __init__.py
│   │       ├── test_case_generation_skill.py
│   │       └── regression_strategy_skill.py
│   │
│   ├── tools/                              # Tool 层
│   │   ├── __init__.py
│   │   ├── base.py                        # Tool 基类
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── json_parser_tool.py
│   │   │   ├── yaml_parser_tool.py
│   │   │   └── openapi_parser_tool.py
│   │   ├── extractors/
│   │   │   ├── __init__.py
│   │   │   ├── field_extractor_tool.py
│   │   │   ├── header_extractor_tool.py
│   │   │   └── endpoint_extractor_tool.py
│   │   ├── classifiers/
│   │   │   ├── __init__.py
│   │   │   ├── error_classifier_tool.py
│   │   │   └── severity_inferencer_tool.py
│   │   ├── inference/
│   │   │   ├── __init__.py
│   │   │   ├── root_cause_inference_tool.py
│   │   │   └── correlation_tool.py
│   │   ├── generators/
│   │   │   ├── __init__.py
│   │   │   ├── fix_suggester_tool.py
│   │   │   ├── test_case_generator_tool.py
│   │   │   └── mock_generator_tool.py
│   │   └── validators/
│   │       ├── __init__.py
│   │       ├── schema_validator_tool.py
│   │       └── response_validator_tool.py
│   │
│   ├── models/                             # 数据模型
│   │   ├── __init__.py
│   │   ├── schemas.py                     # Pydantic Schema 定义
│   │   └── enums.py                       # 枚举定义
│   │
│   ├── graph/                              # LangGraph 扩展（可选）
│   │   ├── __init__.py
│   │   ├── workflow.py                     # 工作流定义
│   │   └── nodes.py                       # 图节点
│   │
│   └── utils/                              # 工具函数
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
│
├── tests/                                  # 测试
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_tools.py
│   │   ├── test_skills.py
│   │   └── test_agents.py
│   ├── integration/
│   │   └── test_workflow.py
│   └── fixtures/
│       └── sample_data.py
│
├docs/                                      # 文档
│   ├── architecture.md
│   ├── api.md
│   └── examples.md
│
└── examples/                               # 示例代码
    ├── basic_usage.py
    ├── batch_processing.py
    └── custom_agent.py
