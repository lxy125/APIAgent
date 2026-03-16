"""
API Bug 诊断系统 - Web 前端

使用 Streamlit 构建的交互式界面
"""
import streamlit as st
import asyncio
import json
import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, str(Path(__file__).parent))

from src import APIDiagnosisSystem


# 初始化诊断系统
@st.cache_resource
def init_diagnosis_system():
    """初始化诊断系统（缓存以避免重复初始化）"""
    return APIDiagnosisSystem()


def main():
    """主函数"""
    st.set_page_config(
        page_title="API Bug 诊断系统",
        page_icon="🐛",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 标题
    st.title("🐛 API Bug 智能诊断系统")
    st.markdown("---")

    # 初始化系统
    try:
        if 'system' not in st.session_state:
            with st.spinner("正在初始化诊断系统..."):
                st.session_state.system = init_diagnosis_system()
        st.success("✓ 系统初始化完成")
    except Exception as e:
        st.error(f"✗ 系统初始化失败: {e}")
        st.stop()

    # 创建两列布局
    col1, col2 = st.columns([1, 1])

    # 左侧：输入区域
    with col1:
        st.subheader("📥 输入 API 数据")

        # 输入方式选择
        input_mode = st.radio(
            "选择输入方式",
            ["JSON 编辑器", "表单填写"],
            horizontal=True
        )

        if input_mode == "JSON 编辑器":
            # JSON 编辑器
            json_input = st.text_area(
                "输入 API 数据（JSON 格式）",
                value='''{
  "request": {
    "method": "POST",
    "url": "https://api.example.com/products",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "name": "Product Name",
      "price": 99.99
    }
  },
  "response": {
    "status_code": 500,
    "body": {
      "error": "Internal Server Error",
      "message": "Database connection failed"
    }
  }
}''',
                height=400,
                key="json_input"
            )

            # 验证JSON
            try:
                api_data = json.loads(json_input)
                st.success("✓ JSON 格式有效")
            except json.JSONDecodeError as e:
                st.error(f"✗ JSON 格式错误: {e}")
                api_data = None

        else:
            # 表单填写
            st.markdown("#### 请求信息")
            with st.expander("Request", expanded=True):
                method = st.selectbox("HTTP 方法", ["GET", "POST", "PUT", "DELETE"], index=1)
                url = st.text_input("API URL", value="https://api.example.com/products")

                st.markdown("##### 请求头")
                content_type = st.selectbox("Content-Type", ["application/json", "application/x-www-form-urlencoded"])
                auth = st.text_input("Authorization (可选)", type="password")

                st.markdown("##### 请求体")
                use_body = st.checkbox("包含请求体", value=True)
                if use_body:
                    body_key = st.text_input("Body Key 1", value="name")
                    body_value = st.text_input("Body Value 1", value="Product Name")
                    body_key2 = st.text_input("Body Key 2", value="price")
                    body_value2 = st.text_input("Body Value 2", value="99.99")

            st.markdown("#### 响应信息")
            with st.expander("Response", expanded=True):
                status_code = st.selectbox(
                    "HTTP 状态码",
                    [200, 201, 400, 401, 403, 404, 422, 500, 502, 503],
                    index=7
                )
                error_message = st.text_input("错误消息", value="Internal Server Error")
                error_detail = st.text_area("错误详情（可选）", height=100)

            # 构建数据
            api_data = {
                "request": {
                    "method": method,
                    "url": url,
                    "headers": {
                        "Content-Type": content_type
                    }
                }
            }

            if auth:
                api_data["request"]["headers"]["Authorization"] = f"Bearer {auth}"

            if use_body:
                api_data["request"]["body"] = {
                    body_key: body_value,
                    body_key2: body_value2
                }

            api_data["response"] = {
                "status_code": status_code,
                "body": {
                    "error": error_message
                }
            }

            if error_detail:
                api_data["response"]["body"]["detail"] = error_detail

    # 诊断按钮
    if st.button("🔍 开始诊断", type="primary", use_container_width=True):
        if api_data:
            # 显示输入摘要
            with col2:
                st.subheader("📊 诊断结果")
                with st.spinner("正在分析 API 数据..."):
                    try:
                        # 执行诊断
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        report = loop.run_until_complete(
                            st.session_state.system.diagnose(api_data)
                        )
                        loop.close()

                        # 显示结果
                        st.session_state.report = report
                        st.session_state.diagnosis_done = True

                    except Exception as e:
                        st.error(f"✗ 诊断失败: {e}")
                        st.exception(e)
                        st.session_state.diagnosis_done = False

    # 右侧：结果显示
    with col2:
        if 'diagnosis_done' in st.session_state and st.session_state.diagnosis_done:
            report = st.session_state.report

            # 基本信息
            st.info(f"🆔 报告 ID: `{report.report_id}`")
            st.info(f"⏰ 诊断时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

            # 严重程度
            severity_colors = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢",
                "INFO": "🔵"
            }
            severity_emoji = severity_colors.get(str(report.overall_severity), "⚪")
            st.markdown(f"### {severity_emoji} 严重程度: {report.overall_severity}")
            st.markdown("---")

            # 语义分析
            with st.expander("🔍 语义分析", expanded=True):
                st.write(f"**错误类别:** {report.semantic_analysis.error_category}")
                st.write(f"**分析置信度:** {report.semantic_analysis.confidence * 100:.0f}%")

                if report.semantic_analysis.extracted_fields:
                    st.write("**提取的字段:**")
                    for key, value in report.semantic_analysis.extracted_fields.items():
                        st.write(f"- {key}: {value}")

            # 根因分析
            with st.expander("🎯 根因分析"):
                st.write(f"**根因描述:** {report.root_cause_analysis.root_cause_description}")

                if report.root_cause_analysis.possible_causes:
                    st.write("**可能的原因:**")
                    for i, cause in enumerate(report.root_cause_analysis.possible_causes, 1):
                        st.write(f"{i}. {cause}")

                if report.root_cause_analysis.affected_components:
                    st.write(f"**受影响的组件:** {', '.join(report.root_cause_analysis.affected_components)}")

            # 修复策略
            with st.expander("🔧 修复策略"):
                st.write(f"**优先级:** {report.fix_strategy.priority}")
                st.write(f"**预估工作量:** {report.fix_strategy.estimated_effort}")
                st.write(f"**风险等级:** {report.fix_strategy.risk_level}")

                if report.fix_strategy.suggestions:
                    st.write("**修复建议:**")
                    for i, suggestion in enumerate(report.fix_strategy.suggestions, 1):
                        st.write(f"{i}. {suggestion}")

                if report.fix_strategy.validation_steps:
                    st.write("**验证步骤:**")
                    for i, step in enumerate(report.fix_strategy.validation_steps, 1):
                        st.write(f"{i}. {step}")

            # 测试用例
            with st.expander("✅ 测试用例"):
                st.write(f"**测试套件名称:** {report.test_suite.suite_name}")
                st.write(f"**总测试用例数:** {len(report.test_suite.test_cases)}")

                if report.test_suite.test_cases:
                    for i, test_case in enumerate(report.test_suite.test_cases, 1):
                        type_emoji = {
                            "positive": "✅",
                            "negative": "❌",
                            "edge_case": "⚠️",
                            "regression": "🔄"
                        }
                        emoji = type_emoji.get(str(test_case.case_type), "📝")

                        with st.expander(f"{emoji} {test_case.name}"):
                            st.write(f"**描述:** {test_case.description}")
                            st.write(f"**类型:** {test_case.case_type}")
                            st.write(f"**优先级:** {test_case.priority}")

                            if test_case.tags:
                                st.write(f"**标签:** {', '.join(test_case.tags)}")

            # 回归策略
            with st.expander("🔄 回归策略"):
                if report.regression_strategy.affected_endpoints:
                    st.write(f"**受影响的端点:**")
                    for endpoint in report.regression_strategy.affected_endpoints:
                        st.write(f"- {endpoint}")

                st.write(f"**冒烟测试数量:** {len(report.regression_strategy.smoke_tests)}")

            # 综合建议
            with st.expander("💡 综合建议"):
                for i, rec in enumerate(report.recommendations, 1):
                    st.write(f"{i}. {rec}")

            # 导出按钮
            st.markdown("---")
            if st.button("📥 导出 JSON 报告"):
                st.json(report.model_dump(), expanded=False)
                st.success("✓ 报告已导出")

            if st.button("📋 复制报告 ID"):
                st.clipboard_text(report.report_id)
                st.success("✓ 已复制到剪贴板")


if __name__ == "__main__":
    main()
