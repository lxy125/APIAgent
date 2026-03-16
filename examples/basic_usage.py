"""
基本使用示例
"""
import asyncio
from src import APIDiagnosisSystem


async def main():
    # 创建诊断系统（使用默认配置，已内置 API Key）
    system = APIDiagnosisSystem()

    # 示例 1: 处理请求响应对
    input_data_1 = {
        "request": {
            "method": "POST",
            "url": "https://api.example.com/users",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer token123"
            },
            "body": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        },
        "response": {
            "status_code": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
                "error": "Internal Server Error",
                "message": "Database connection failed"
            }
        },
        "log": "2024-01-15 10:30:00 ERROR [db-connector] Connection timeout to database"
    }

    print("=" * 60)
    print("Diagnosing API Error...")
    print("=" * 60)

    report = await system.diagnose(input_data_1)

    # 输出报告
    print("\n📊 Diagnostic Report")
    print(f"Report ID: {report.report_id}")
    print(f"Timestamp: {report.timestamp}")
    print(f"Overall Severity: {report.overall_severity}")

    print("\n🔍 Semantic Analysis:")
    print(f"  Error Category: {report.semantic_analysis.error_category}")
    print(f"  Error Code: {report.semantic_analysis.error_code}")
    print(f"  Confidence: {report.semantic_analysis.confidence}")

    print("\n🎯 Root Cause Analysis:")
    print(f"  Category: {report.root_cause_analysis.root_cause_category}")
    print(f"  Description: {report.root_cause_analysis.root_cause_description}")
    print(f"  Possible Causes: {report.root_cause_analysis.possible_causes}")

    print("\n🔧 Fix Strategy:")
    print(f"  Priority: {report.fix_strategy.priority}")
    print(f"  Estimated Effort: {report.fix_strategy.estimated_effort}")
    print(f"  Risk Level: {report.fix_strategy.risk_level}")
    print("\n  Suggestions:")
    for i, suggestion in enumerate(report.fix_strategy.suggestions, 1):
        print(f"    {i}. {suggestion}")

    print("\n✅ Test Cases Generated:")
    print(f"  Suite Name: {report.test_suite.suite_name}")
    print(f"  Total Test Cases: {len(report.test_suite.test_cases)}")
    print(f"\n  Test Cases:")
    for test_case in report.test_suite.test_cases:
        print(f"    - {test_case.name} ({test_case.case_type})")

    print("\n🔄 Regression Strategy:")
    print(f"  Affected Endpoints: {report.regression_strategy.affected_endpoints}")
    print(f"  Smoke Tests: {len(report.regression_strategy.smoke_tests)}")

    print("\n💡 Recommendations:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"  {i}. {rec[:100]}...")

    # 示例 2: 处理自然语言描述
    print("\n" + "=" * 60)
    print("Diagnosing Natural Language Description...")
    print("=" * 60)

    input_data_2 = """
    The user creation API is returning a 400 error when the email address
    contains a plus sign (+). The error message says 'Invalid email format'.
    This works fine with normal email addresses.
    """

    report_2 = await system.diagnose(input_data_2)

    print(f"\n📊 Report ID: {report_2.report_id}")
    print(f"🎯 Root Cause: {report_2.root_cause_analysis.root_cause_description[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
