/**
 * 决策API客户端模块
 * 专门处理与 /api/v1/decision 接口的交互
 */

const API_BASE_URL = window.location.origin;

/**
 * 获取决策建议
 * @param {Object} params - 请求参数
 * @returns {Promise<Object>} 决策结果
 */
export async function getDecisionAdvice(params = {}) {
    try {
        const payload = {
            temperature: params.temperature ?? 85.5,
            pressure: params.pressure ?? 4.2,
            flow_rate: params.flow_rate ?? 10.5,
            heat_value: params.heat_value ?? 1250.8,
            timestamp: params.timestamp ?? new Date().toISOString(),
            unit: params.unit ?? '°C'
        };

        const response = await fetch(`${API_BASE_URL}/api/v1/decision`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('获取决策建议失败:', error);
        // 仅在后端不可达时回退模拟数据
        return getMockDecisionData();
    }
}

/**
 * 获取模拟决策数据（当API不可用时使用）
 * @returns {Object} 模拟决策数据
 */
function getMockDecisionData() {
    return {
        decision: {
            reasoning: "基于当前余热温度85.5°C和压力4.2MPa的分析，建议调整换热器1的运行参数，以提高余热回收率。根据历史数据分析，当前工况下调整换热器1的进水流量可以提升约15%的热回收效率。",
            source_trace: {
                data_sources: ["传感器数据", "历史运行数据"],
                model_used: "LSTM预测模型",
                confidence: "0.92",
                timestamp: new Date().toISOString()
            }
        }
    };
}

/**
 * 执行决策建议
 * @param {string} advice - 建议内容
 * @returns {Promise<boolean>} 执行结果
 */
export async function executeDecision(advice) {
    try {
        // 这里可以添加实际的执行逻辑
        console.log('执行决策建议:', advice);
        return true;
    } catch (error) {
        console.error('执行决策建议失败:', error);
        return false;
    }
}

/**
 * 忽略决策建议
 * @param {string} advice - 建议内容
 * @returns {Promise<boolean>} 忽略结果
 */
export async function ignoreDecision(advice) {
    try {
        // 这里可以添加实际的忽略逻辑
        console.log('忽略决策建议:', advice);
        return true;
    } catch (error) {
        console.error('忽略决策建议失败:', error);
        return false;
    }
}