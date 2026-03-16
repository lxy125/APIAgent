# API Bug 智能诊断与修复辅助系统

基于 LangChain 的多 Agent 系统，用于 API Bug 的智能诊断、根因分析、修复建议和测试用例生成。

## 架构概览

```
┌─────────────────────────────────────────┐
│              User Input               │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Supervisor Agent               │
│  (路由、协调、聚合)                     │
└─────────────────────────────────────────┘
        │          │          │
        ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Semantic │ │Root Cause│ │  Test    │
│ Analyzer │ │Strategist│ │ Generator│
└──────────┘ └──────────┘ └──────────┘
```

## 三层架构

| 层级 | 特征 | 示例 |
|------|------|------|
| **Tool** | 原子能力，无状态 | parse_json, classify_error |
| **Skill** | 面向任务的策略性能力 | API 语义分析策略 |
| **Agent** | LLM 驱动的自主决策实体 | 语义分析 Agent |

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 或使用 poetry
poetry install

# 或使用 pip 安装（推荐）
pip install -e .
```

## 快速开始

### Web 界面（推荐）

```bash
# 安装依赖
pip install -e .

# 启动 Web 应用
streamlit run web_app.py
```

浏览器将自动打开 `http://localhost:8501`，你可以在界面中：

- 📥 以 JSON 或表单方式输入 API 数据
- 🔍 一键启动智能诊断
- 📊 查看完整的诊断报告（语义分析、根因、修复策略、测试用例）
- 💡 导出 JSON 格式的诊断报告

### 命令行使用

```python
import asyncio
from src import APIDiagnosisSystem

async def main():
    # 初始化系统
    system = APIDiagnosisSystem()

    # 输入数据
    input_data = {
        "request": {
            "method": "POST",
            "url": "https://api.example.com/users",
            "body": {"name": "John", "email": "john@example.com"}
        },
        "response": {
            "status_code": 500,
            "body": {"error": "Database connection failed"}
        }
    }

    # 执行诊断
    report = await system.diagnose(input_data)

    # 查看结果
    print(f"Root Cause: {report.root_cause_analysis.root_cause_description}")
    print(f"Fix Priority: {report.fix_strategy.priority}")
    print(f"Test Cases: {len(report.test_suite.test_cases)}")

asyncio.run(main())
```

### 交互式 CLI

```bash
python interactive_cli.py
```

## 扩展功能

### LangGraph 集成

将工作流转换为 LangGraph 以实现：

- 状态持久化
- 条件路由
- 循环和分支
- 时间旅行调试

### RAG 集成

添加以下能力：

- 从历史案例库检索相似 Bug
- 基于文档库的根因推断
- 知识库驱动的修复建议

### OpenAPI 解析

增强功能：

- 自动解析 API 规范
- 生成 Schema 验证
- 智能推断端点关系

### 自动化测试框架

集成：

- pytest 测试用例生成
- Postman Collection 导出
- CI/CD 流水线集成

## 项目结构

详见 `PROJECT_STRUCTURE.md`

## 开发

```bash
# 运行测试
pytest

# 代码格式化
black src/
ruff check src/

# 类型检查
mypy src/
```

## License

MIT
