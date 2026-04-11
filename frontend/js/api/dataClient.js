/**
 * 数据API客户端模块
 * 处理与其他数据接口的交互
 */

const API_BASE_URL = window.location.origin;

/**
 * 获取KPI数据
 * @returns {Promise<Object>} KPI数据
 */
export async function getKpiData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/kpi`);
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('获取KPI数据失败:', error);
        return getMockKpiData();
    }
}

/**
 * 获取趋势数据
 * @param {number} days - 天数
 * @returns {Promise<Object>} 趋势数据
 */
export async function getTrendData(days = 7) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/trends?days=${days}`);
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('获取趋势数据失败:', error);
        return getMockTrendData();
    }
}

/**
 * 获取设备状态
 * @returns {Promise<Object>} 设备状态数据
 */
export async function getEquipmentStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/equipment`);
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('获取设备状态失败:', error);
        return getMockEquipmentStatus();
    }
}

/**
 * 获取预警信息
 * @returns {Promise<Object>} 预警信息
 */
export async function getAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/alerts`);
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('获取预警信息失败:', error);
        return getMockAlerts();
    }
}

/**
 * 获取模拟KPI数据
 * @returns {Object} 模拟KPI数据
 */
function getMockKpiData() {
    return {
        temperature: 85.5,
        pressure: 4.2,
        heatRecovery: 1250.8,
        energySaving: 320.5,
        temperaturePrediction: 87.2,
        pressurePrediction: 4.1,
        heatRecoveryPrediction: 1280.5,
        energySavingPrediction: 340.2
    };
}

/**
 * 获取模拟趋势数据
 * @returns {Object} 模拟趋势数据
 */
function getMockTrendData() {
    return {
        labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
        temperature: [78, 82, 85, 88, 86, 84, 80],
        pressure: [3.8, 4.0, 4.2, 4.3, 4.2, 4.1, 4.0],
        heatRecovery: [1100, 1150, 1200, 1250, 1230, 1210, 1180]
    };
}

/**
 * 获取模拟设备状态
 * @returns {Array} 模拟设备状态
 */
function getMockEquipmentStatus() {
    return [
        { id: 1, name: '换热器1', status: 'normal', health: 95 },
        { id: 2, name: '换热器2', status: 'warning', health: 75 },
        { id: 3, name: '泵1', status: 'normal', health: 90 },
        { id: 4, name: '阀门1', status: 'normal', health: 85 }
    ];
}

/**
 * 获取模拟预警信息
 * @returns {Array} 模拟预警信息
 */
function getMockAlerts() {
    return [
        {
            id: 1,
            level: 'warning',
            message: '换热器2需要维护',
            time: new Date().toLocaleTimeString()
        },
        {
            id: 2,
            level: 'info',
            message: '系统运行正常',
            time: new Date().toLocaleTimeString()
        }
    ];
}