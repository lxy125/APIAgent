"""
测试脚本 - 测试 API Bug 诊断系统
"""
import asyncio
import sys
import os
sys.path.insert(0, 'D:\\claude\\api_bug_diagnosis_system')

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src import APIDiagnosisSystem


async def test_diagnosis():
    """测试诊断功能"""
    print("=" * 70)
    print("🚀 API Bug 诊断系统测试")
    print("=" * 70)

    # 创建测试数据 - 一个真实的 API 错误场景
    test_input = {
        "request": {
            "method": "POST",
            "url": "https://api.ecommerce.com/v1/products",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "X-Request-ID": "req-abc123"
            },
            "body": {
                "name": "Wireless Headphones",
                "price": 199.99,
                "category": "electronics",
                "stock": 50,
                "sku": "WH-2024-001"
            }
        },
        "response": {
            "status_code": 422,
            "headers": {
                "Content-Type": "application/json",
                "X-Request-ID": "req-abc123"
            },
            "body": {
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": [
                    {
                        "field": "price",
                        "message": "Price must be a positive integer",
                        "code": "INVALID_TYPE"
                    }
                ]
            }
        },
        "log": """[2024-03-16 14:32:15] INFO [api-gateway] POST /v1/products - Request received
[2024-03-16 14:32:15] INFO [api-gateway] User ID: user_12345 authenticated
[2024-03-16 14:32:15] DEBUG [product-service] Validating product data
[2024-03-16 14:32:15] ERROR [product-service] Validation failed for field 'price': expected int, got float
[2024-03-16 14:32:15] WARN [api-gateway] Returning 422 to client"""
    }

    print("\n📥 输入数据:")
    print(f"   方法: {test_input['request']['method']}")
    print(f"   端点: {test_input['request']['url']}")
    print(f"   状态码: {test_input['response']['status_code']}")
    print(f"   错误消息: {test_input['response']['body']['message']}")

    print("\n" + "=" * 70)
    print("🔍 开始诊断...")
    print("=" * 70)

    try:
        # 创建诊断系统
        system = APIDiagnosisSystem()

        # 执行诊断
        report = await system.diagnose(test_input)

        print("\n" + "=" * 70)
        print("📊 诊断报告")
        print("=" * 70)

        print(f"\n🆔 报告 ID: {report.report_id}")
        print(f"📅 时间戳: {report.timestamp}")
        print(f"⚠️  整体严重程度: {report.overall_severity}")

        print("\n" + "-" * 70)
        print("🔍 语义分析结果")
        print("-" * 70)
        print(f"   错误类别: {report.semantic_analysis.error_category}")
        print(f"   错误码: {report.semantic_analysis.error_code}")
        print(f"   分析置信度: {report.semantic_analysis.confidence}")
        if report.semantic_analysis.extracted_fields:
            print(f"   提取的字段: {list(report.semantic_analysis.extracted_fields.keys())}")

        print("\n" + "-" * 70)
        print("🎯 根因分析")
        print("-" * 70)
        print(f"   根因类别: {report.root_cause_analysis.root_cause_category}")
        print(f"   根因描述: {report.root_cause_analysis.root_cause_description}")
        print(f"\n   可能的原因:")
        for i, cause in enumerate(report.root_cause_analysis.possible_causes, 1):
            print(f"     {i}. {cause}")
        print(f"\n   受影响的组件: {', '.join(report.root_cause_analysis.affected_components)}")

        print("\n" + "-" * 70)
        print("🔧 修复策略")
        print("-" * 70)
        print(f"   优先级: {report.fix_strategy.priority}")
        print(f"   预估工作量: {report.fix_strategy.estimated_effort}")
        print(f"   风险等级: {report.fix_strategy.risk_level}")
        print(f"\n   修复建议:")
        for i, suggestion in enumerate(report.fix_strategy.suggestions, 1):
            print(f"     {i}. {suggestion}")

        if report.fix_strategy.validation_steps:
            print(f"\n   验证步骤:")
            for i, step in enumerate(report.fix_strategy.validation_steps, 1):
                print(f"     {i}. {step}")

        print("\n" + "-" * 70)
        print("✅ 测试用例")
        print("-" * 70)
        print(f"   测试套件名称: {report.test_suite.suite_name}")
        print(f"   总测试用例数: {len(report.test_suite.test_cases)}")

        if report.test_suite.test_cases:
            print(f"\n   生成的测试用例:")
            for test_case in report.test_suite.test_cases:
                type_emoji = {
                    "positive": "✅",
                    "negative": "❌",
                    "edge_case": "⚠️",
                    "regression": "🔄"
                }
                emoji = type_emoji.get(test_case.case_type, "📝")
                print(f"     {emoji} {test_case.name} ({test_case.case_type}) - 优先级: {test_case.priority}")

        print("\n" + "-" * 70)
        print("🔄 回归策略")
        print("-" * 70)
        print(f"   受影响的端点: {', '.join(report.regression_strategy.affected_endpoints) if report.regression_strategy.affected_endpoints else '无'}")
        print(f"   冒烟测试数量: {len(report.regression_strategy.smoke_tests)}")

        print("\n" + "-" * 70)
        print("💡 综合建议")
        print("-" * 70)
        for i, rec in enumerate(report.recommendations, 1):
            print(f"   {i}. {rec}")

        print("\n" + "=" * 70)
        print("✅ 测试完成！")
        print("=" * 70)

        return report

    except Exception as e:
        print(f"\n❌ 测试失败: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_diagnosis())
