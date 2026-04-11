import requests
import sys
import json

# 设置标准输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# API端点
API_URL = "http://127.0.0.1:8001/api/v1/decision"

# 测试用例数据
test_cases = [
    # 温度升高测试用例
    {
        "name": "temperature_rise_normal",
        "data": {
            "temperature": 85.5,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "temperature_rise"
    },
    {
        "name": "temperature_rise_confidence_boundary_1",
        "data": {
            "temperature": 80.0,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "temperature_rise"
    },
    {
        "name": "temperature_rise_confidence_boundary_2",
        "data": {
            "temperature": 79.9,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "normal"
    },
    {
        "name": "temperature_rise_unit_celsius",
        "data": {
            "temperature": 85.5,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "temperature_rise"
    },
    {
        "name": "temperature_rise_unit_kelvin",
        "data": {
            "temperature": 358.65,  # 85.5°C in Kelvin
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "K"
        },
        "expected_prediction": "error"  # 应该返回错误，因为只支持°C
    },
    
    # 压力下降测试用例
    {
        "name": "pressure_drop_normal",
        "data": {
            "temperature": 75.0,
            "pressure": 2.0,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "pressure_drop"
    },
    {
        "name": "pressure_drop_confidence_boundary_1",
        "data": {
            "temperature": 75.0,
            "pressure": 2.5,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "pressure_drop"
    },
    {
        "name": "pressure_drop_confidence_boundary_2",
        "data": {
            "temperature": 75.0,
            "pressure": 2.6,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "normal"
    },
    {
        "name": "pressure_drop_unit_celsius",
        "data": {
            "temperature": 75.0,
            "pressure": 2.0,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "pressure_drop"
    },
    {
        "name": "pressure_drop_unit_kelvin",
        "data": {
            "temperature": 348.15,  # 75.0°C in Kelvin
            "pressure": 2.0,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "K"
        },
        "expected_prediction": "error"  # 应该返回错误，因为只支持°C
    },
    
    # 流量不稳定测试用例
    {
        "name": "flow_instability_normal",
        "data": {
            "temperature": 75.0,
            "pressure": 4.2,
            "flow_rate": 5.0,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "flow_instability"
    },
    {
        "name": "flow_instability_confidence_boundary_1",
        "data": {
            "temperature": 75.0,
            "pressure": 4.2,
            "flow_rate": 6.0,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "flow_instability"
    },
    {
        "name": "flow_instability_confidence_boundary_2",
        "data": {
            "temperature": 75.0,
            "pressure": 4.2,
            "flow_rate": 6.1,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "normal"
    },
    {
        "name": "flow_instability_unit_celsius",
        "data": {
            "temperature": 75.0,
            "pressure": 4.2,
            "flow_rate": 5.0,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "flow_instability"
    },
    {
        "name": "flow_instability_unit_kelvin",
        "data": {
            "temperature": 348.15,  # 75.0°C in Kelvin
            "pressure": 4.2,
            "flow_rate": 5.0,
            "heat_value": 1250.8,
            "timestamp": "2026-04-10T14:30:00",
            "unit": "K"
        },
        "expected_prediction": "error"  # 应该返回错误，因为只支持°C
    }
]

def test_api_endpoint():
    """测试API端点的功能完备性"""
    print("=== 开始功能完备性测试 ===")
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"输入数据: {json.dumps(test_case['data'], ensure_ascii=False)}")
        
        try:
            # 发送请求
            response = requests.post(API_URL, json=test_case['data'], headers={"Content-Type": "application/json"})
            
            # 检查响应状态码
            if test_case['expected_prediction'] == "error":
                # 对于单位错误的情况，应该返回422
                assert response.status_code == 422, f"Expected status code 422 for invalid unit, got {response.status_code}"
                print("✅ 验证通过: 正确处理了无效单位")
                passed += 1
            else:
                # 对于正常情况，应该返回200
                assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
                
                # 解析响应
                response_data = response.json()
                
                # 验证响应结构
                assert "status" in response_data, "Missing status field"
                assert "suggestion" in response_data, "Missing suggestion field"
                assert "decision" in response_data, "Missing decision field"
                assert "source_trace" in response_data, "Missing source_trace field"
                
                # 验证suggestion字段包含【智能建议】
                assert "【智能建议】" in response_data["suggestion"], "Suggestion field missing 【智能建议】"
                
                # 验证source_trace三方署名完整
                assert "prediction_source" in response_data["source_trace"], "Missing prediction_source field"
                assert "knowledge_source" in response_data["source_trace"], "Missing knowledge_source field"
                assert "safety_clause" in response_data["source_trace"], "Missing safety_clause field"
                
                # 验证knowledge_source字段精确匹配杨泽彤文档名
                knowledge_source = response_data["source_trace"]["knowledge_source"]
                assert "杨泽彤-" in knowledge_source, f"Knowledge source missing 杨泽彤 prefix: {knowledge_source}"
                
                # 验证置信度字段
                assert "confidence" in response_data["source_trace"], "Missing confidence field"
                confidence = response_data["source_trace"]["confidence"]
                assert 0.0 <= confidence <= 1.0, f"Confidence out of range: {confidence}"
                
                print("✅ 验证通过: 响应结构正确，包含【智能建议】，三方署名完整")
                print(f"   置信度: {confidence}")
                print(f"   知识来源: {knowledge_source}")
                
                passed += 1
                
        except Exception as e:
            print(f"❌ 验证失败: {str(e)}")
            failed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总测试数: {len(test_cases)}")
    
    if failed == 0:
        print("🎉 所有测试用例通过！")
        return True
    else:
        print("⚠️  部分测试用例失败，请检查")
        return False

def test_health_check():
    """测试健康检查端点"""
    print("\n=== 测试健康检查端点 ===")
    
    try:
        response = requests.get("http://127.0.0.1:8001/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("✅ 健康检查通过")
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试健康检查
    health_passed = test_health_check()
    
    # 测试API端点
    api_passed = test_api_endpoint()
    
    # 总体结果
    if health_passed and api_passed:
        print("\n🏆 功能完备性测试全部通过！")
        sys.exit(0)
    else:
        print("\n❌ 功能完备性测试存在失败项")
        sys.exit(1)
