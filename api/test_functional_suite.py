import sys
import os
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# 测试数据：覆盖3类预测类型，每类5组边界值
test_cases = [
    # temperature_rise 测试用例
    {
        "name": "temperature_rise_normal",
        "input": {
            "temperature": 85.5,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-12T14:30:00",
            "unit": "°C"
        },
        "expected_prediction": "temperature_rise",
        "expected_confidence": 0.94
    },
    {
        "name": "temperature_rise_confidence_boundary_high",
        "input": {
            "temperature": 81.0,
            "pressure": 4.0,
            "flow_rate": 10.0,
            "heat_value": 1200.0,
            "timestamp": "2026-04-12T14:31:00",
            "unit": "°C"
        },
        "expected_prediction": "temperature_rise",
        "expected_confidence": 0.90
    },
    {
        "name": "temperature_rise_confidence_boundary_low",
        "input": {
            "temperature": 79.0,
            "pressure": 4.0,
            "flow_rate": 10.0,
            "heat_value": 1100.0,
            "timestamp": "2026-04-12T14:32:00",
            "unit": "°C"
        },
        "expected_prediction": "normal",
        "expected_confidence": 0.90
    },
    {
        "name": "temperature_rise_unit_celsius",
        "input": {
            "temperature": 85.5,
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-12T14:33:00",
            "unit": "°C"
        },
        "expected_prediction": "temperature_rise",
        "expected_confidence": 0.94
    },
    {
        "name": "temperature_rise_unit_invalid",
        "input": {
            "temperature": 358.65,  # 85.5°C in Kelvin
            "pressure": 4.2,
            "flow_rate": 10.5,
            "heat_value": 1250.8,
            "timestamp": "2026-04-12T14:34:00",
            "unit": "K"
        },
        "expected_error": True
    },
    
    # pressure_drop 测试用例
    {
        "name": "pressure_drop_normal",
        "input": {
            "temperature": 75.0,
            "pressure": 3.0,
            "flow_rate": 10.0,
            "heat_value": 1000.0,
            "timestamp": "2026-04-12T14:35:00",
            "unit": "°C"
        },
        "expected_prediction": "pressure_drop",
        "expected_confidence": 0.92
    },
    {
        "name": "pressure_drop_confidence_boundary_high",
        "input": {
            "temperature": 75.0,
            "pressure": 3.4,
            "flow_rate": 10.0,
            "heat_value": 1000.0,
            "timestamp": "2026-04-12T14:36:00",
            "unit": "°C"
        },
        "expected_prediction": "pressure_drop",
        "expected_confidence": 0.86
    },
    {
        "name": "pressure_drop_confidence_boundary_low",
        "input": {
            "temperature": 75.0,
            "pressure": 3.6,
            "flow_rate": 10.0,
            "heat_value": 1000.0,
            "timestamp": "2026-04-12T14:37:00",
            "unit": "°C"
        },
        "expected_prediction": "normal",
        "expected_confidence": 0.88
    },
    {
        "name": "pressure_drop_unit_celsius",
        "input": {
            "temperature": 75.0,
            "pressure": 3.0,
            "flow_rate": 10.0,
            "heat_value": 1000.0,
            "timestamp": "2026-04-12T14:38:00",
            "unit": "°C"
        },
        "expected_prediction": "pressure_drop",
        "expected_confidence": 0.92
    },
    {
        "name": "pressure_drop_unit_invalid",
        "input": {
            "temperature": 348.15,  # 75°C in Kelvin
            "pressure": 3.0,
            "flow_rate": 10.0,
            "heat_value": 1000.0,
            "timestamp": "2026-04-12T14:39:00",
            "unit": "K"
        },
        "expected_error": True
    },
    
    # flow_instability 测试用例
    {
        "name": "flow_instability_normal",
        "input": {
            "temperature": 75.0,
            "pressure": 4.0,
            "flow_rate": 8.5,
            "heat_value": 1100.0,
            "timestamp": "2026-04-12T14:40:00",
            "unit": "°C"
        },
        "expected_prediction": "flow_instability",
        "expected_confidence": 0.75
    },
    {
        "name": "flow_instability_confidence_boundary_high",
        "input": {
            "temperature": 75.0,
            "pressure": 4.0,
            "flow_rate": 9.0,
            "heat_value": 1100.0,
            "timestamp": "2026-04-12T14:41:00",
            "unit": "°C"
        },
        "expected_prediction": "flow_instability",
        "expected_confidence": 0.84
    },
    {
        "name": "flow_instability_confidence_boundary_low",
        "input": {
            "temperature": 75.0,
            "pressure": 4.0,
            "flow_rate": 9.5,
            "heat_value": 1100.0,
            "timestamp": "2026-04-12T14:42:00",
            "unit": "°C"
        },
        "expected_prediction": "normal",
        "expected_confidence": 0.86
    },
    {
        "name": "flow_instability_unit_celsius",
        "input": {
            "temperature": 75.0,
            "pressure": 4.0,
            "flow_rate": 8.5,
            "heat_value": 1100.0,
            "timestamp": "2026-04-12T14:43:00",
            "unit": "°C"
        },
        "expected_prediction": "flow_instability",
        "expected_confidence": 0.75
    },
    {
        "name": "flow_instability_unit_invalid",
        "input": {
            "temperature": 348.15,  # 75°C in Kelvin
            "pressure": 4.0,
            "flow_rate": 8.5,
            "heat_value": 1100.0,
            "timestamp": "2026-04-12T14:44:00",
            "unit": "K"
        },
        "expected_error": True
    }
]

@pytest.mark.parametrize("test_case", test_cases)
def test_decision_api(test_case):
    """测试决策API的功能完备性"""
    response = client.post("/api/v1/decision", json=test_case["input"])
    
    if test_case.get("expected_error"):
        # 验证错误响应
        assert response.status_code == 422
        assert "Invalid unit" in response.json()["detail"]
    else:
        # 验证成功响应
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "status" in data
        assert "suggestion" in data
        assert "decision" in data
        assert "source_trace" in data
        assert "execution_time_ms" in data
        
        # 验证suggestion字段包含【智能建议】
        assert "【智能建议】" in data["suggestion"] or "[需人工复核]" in data["suggestion"]
        
        # 验证source_trace三方署名完整
        assert "prediction_source" in data["source_trace"]
        assert "knowledge_source" in data["source_trace"]
        assert "safety_clause" in data["source_trace"]
        assert "model_version" in data["source_trace"]
        assert "confidence" in data["source_trace"]
        assert "timestamp" in data["source_trace"]
        
        # 验证knowledge_source字段精确匹配杨泽彤文档名
        knowledge_source = data["source_trace"]["knowledge_source"]
        assert "杨泽彤-" in knowledge_source
        assert ".xlsx" in knowledge_source or ".pdf" in knowledge_source or ".docx" in knowledge_source
        assert "knowledge_base" not in knowledge_source  # 确保无路径拼接错误
        
        # 验证execution_time_ms为数字
        assert isinstance(data["execution_time_ms"], (int, float))
        assert data["execution_time_ms"] > 0

def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "components" in data
    assert data["components"]["vectorstore"] == "ready"
    assert data["components"]["llm_service"] == "ready"
    assert data["components"]["knowledge_base"] == "valid"

if __name__ == "__main__":
    # 运行所有测试
    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        try:
            test_decision_api(test_case)
            print(f"✅ {test_case['name']} 测试通过")
        except Exception as e:
            print(f"❌ {test_case['name']} 测试失败: {e}")
    
    print("\n测试健康检查端点")
    try:
        test_health_check()
        print("✅ 健康检查测试通过")
    except Exception as e:
        print(f"❌ 健康检查测试失败: {e}")
    
    print("\n所有测试完成!")
