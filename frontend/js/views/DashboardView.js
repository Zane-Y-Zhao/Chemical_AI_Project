/**
 * 仪表盘视图组件 - 毛玻璃风格大屏版本
 * 整合所有子组件，形成完整的监控大屏
 */

import { getKpiData, getTrendData, getEquipmentStatus, getAlerts } from '../api/dataClient.js';
import { getDecisionAdvice, executeDecision, ignoreDecision } from '../api/decisionClient.js';
import { sendMessage } from '../api/conversationClient.js';

export class DashboardView {
    constructor(container) {
        this.container = container;
        this.kpiData = null;
        this.trendData = null;
        this.equipmentList = [];
        this.alerts = [];
        this.recommendations = [];
        this.sessionId = 'session_' + Date.now();
        this.conversationHistory = [];
        this.init();
    }

    init() {
        this.renderLayout();
        this.loadInitialData();
        this.startRealTimeUpdates();
    }

    renderLayout() {
        this.container.innerHTML = `
            <div class="dashboard">
                <!-- 头部 -->
                <div class="header">
                    <div class="header-left">
                        <h1>化工余热智能管理系统</h1>
                        <div class="tooltip">
                            <button class="action-btn execute" onclick="dashboard.exportToCSV()">导出CSV</button>
                            <span class="tooltip-text">导出当前数据为CSV文件</span>
                        </div>
                    </div>
                    <div class="status">
                        <div class="status-item">
                            <div class="status-indicator online"></div>
                            <span>系统运行正常</span>
                        </div>
                        <div class="status-item">
                            <span>实时监控中</span>
                        </div>
                        <div class="status-item">
                            <span id="currentTime"></span>
                        </div>
                    </div>
                </div>

                <!-- 主内容区 - 4列布局 -->
                <div class="grid">
                    <!-- 左侧列 - KPI概览 -->
                    <div class="left-panel">
                        <div class="card">
                            <h2>综合概览</h2>
                            <div class="kpi-grid" id="kpiGrid"></div>
                        </div>
                    </div>

                    <!-- 中间上方 - 趋势分析 -->
                    <div class="center-top-panel">
                        <div class="card">
                            <div class="card-header">
                                <h2>趋势分析</h2>
                                <div class="card-actions">
                                    <div class="tooltip">
                                        <button class="action-btn view" onclick="dashboard.exportChart('trend')">导出图表</button>
                                        <span class="tooltip-text">导出趋势分析图表为图片</span>
                                    </div>
                                </div>
                            </div>
                            <div class="chart-container" id="trendChart"></div>
                        </div>
                    </div>

                    <!-- 右侧面板 - 预警、建议和会话管理 -->
                    <div class="right-panel">
                        <!-- 预警信息 -->
                        <div class="right-top">
                            <div class="card">
                                <h2>预警信息</h2>
                                <div class="alert-list" id="alertList"></div>
                            </div>
                        </div>
                        
                        <!-- 智能操作建议 -->
                        <div class="right-middle">
                            <div class="card">
                                <h2>智能操作建议</h2>
                                <div class="recommendation-list" id="recommendationList"></div>
                                <div class="source-trace" id="sourceTrace" style="display: none;">
                                    <h4>溯源依据</h4>
                                    <div class="source-trace-content" id="sourceTraceContent"></div>
                                    <button class="action-btn close" onclick="document.getElementById('sourceTrace').style.display = 'none'">关闭</button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 会话管理 -->
                        <div class="right-bottom">
                            <div class="card">
                                <h2>智能助手</h2>
                                <div class="conversation-container">
                                    <div class="conversation-history" id="conversationHistory"></div>
                                    <div class="conversation-input">
                                        <input type="text" id="messageInput" placeholder="请输入您的问题..." onkeypress="if(event.key === 'Enter') dashboard.sendMessage()" />
                                        <button class="action-btn execute" onclick="dashboard.sendMessage()">发送</button>
                                    </div>
                                </div>
                                <div class="context-trace" id="contextTrace" style="display: none;">
                                    <h4>操作依据</h4>
                                    <div class="context-trace-content" id="contextTraceContent"></div>
                                    <button class="action-btn close" onclick="document.getElementById('contextTrace').style.display = 'none'">关闭</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 中间下方左侧 - 能耗分析 -->
                    <div class="center-bottom-left">
                        <div class="card">
                            <div class="card-header">
                                <h2>能耗分析</h2>
                                <div class="card-actions">
                                    <div class="tooltip">
                                        <button class="action-btn view" onclick="dashboard.exportChart('energy')">导出图表</button>
                                        <span class="tooltip-text">导出能耗分析图表为图片</span>
                                    </div>
                                </div>
                            </div>
                            <div class="energy-chart" id="energyChart"></div>
                        </div>
                    </div>

                    <!-- 中间下方右侧 - 设备状态 -->
                    <div class="center-bottom-right">
                        <div class="card">
                            <h2>设备状态</h2>
                            <div class="equipment-grid" id="equipmentGrid"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async loadInitialData() {
        // 加载KPI数据
        this.kpiData = await getKpiData();
        this.updateKpiCards();

        // 加载趋势数据
        this.trendData = await getTrendData();
        this.initTrendChart();

        // 加载设备状态
        this.equipmentList = await getEquipmentStatus();
        this.updateEquipmentStatus();

        // 加载预警信息
        this.alerts = await getAlerts();
        this.updateAlerts();

        // 加载决策建议
        await this.loadDecisionAdvice();

        // 初始化能耗分析图
        this.initEnergyChart();
    }

    updateKpiCards() {
        const grid = document.getElementById('kpiGrid');
        if (!grid || !this.kpiData) return;

        grid.innerHTML = '';

        const kpis = [
            { label: '余热温度', value: this.kpiData.temperature, unit: '°C', prediction: this.kpiData.temperaturePrediction },
            { label: '系统压力', value: this.kpiData.pressure, unit: 'MPa', prediction: this.kpiData.pressurePrediction },
            { label: '余热回收', value: this.kpiData.heatRecovery, unit: 'kJ', prediction: this.kpiData.heatRecoveryPrediction },
            { label: '节能效果', value: this.kpiData.energySaving, unit: 'kW', prediction: this.kpiData.energySavingPrediction }
        ];

        kpis.forEach(kpi => {
            const card = document.createElement('div');
            card.className = 'kpi-card';
            card.innerHTML = `
                <div class="kpi-label">${kpi.label}</div>
                <div class="kpi-value">${kpi.value}<span class="kpi-unit">${kpi.unit}</span></div>
                <div class="kpi-prediction">预测: ${kpi.prediction}${kpi.unit}</div>
            `;
            grid.appendChild(card);
        });
    }

    initTrendChart() {
        if (!window.echarts) return;

        const container = document.getElementById('trendChart');
        if (!container || !this.trendData) return;

        this.trendChart = echarts.init(container);
        this.updateTrendChart();

        window.addEventListener('resize', () => {
            if (this.trendChart) this.trendChart.resize();
        });
    }

    updateTrendChart() {
        if (!this.trendChart || !this.trendData) return;

        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(30, 30, 50, 0.9)',
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1,
                textStyle: {
                    color: '#fff'
                },
                formatter: function(params) {
                    let result = params[0].name + '<br/>';
                    params.forEach(param => {
                        let unit = '';
                        if (param.seriesName === '温度') unit = ' °C';
                        else if (param.seriesName === '压力') unit = ' MPa';
                        else if (param.seriesName === '回收热量') unit = ' kJ';
                        result += param.marker + param.seriesName + ': ' + param.value + unit + '<br/>';
                    });
                    return result;
                }
            },
            legend: {
                data: ['温度', '压力', '回收热量'],
                textStyle: {
                    color: 'rgba(255, 255, 255, 0.7)'
                },
                top: 0,
                right: 0
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: this.trendData.labels,
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255, 255, 255, 0.2)'
                    }
                },
                axisLabel: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    fontSize: 11
                }
            },
            yAxis: {
                type: 'value',
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255, 255, 255, 0.2)'
                    }
                },
                axisLabel: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    fontSize: 11
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            series: [
                {
                    name: '温度',
                    type: 'line',
                    data: this.trendData.temperature,
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 6,
                    lineStyle: {
                        color: '#60a5fa',
                        width: 3
                    },
                    itemStyle: {
                        color: '#60a5fa'
                    },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(96, 165, 250, 0.4)' },
                            { offset: 1, color: 'rgba(96, 165, 250, 0.05)' }
                        ])
                    }
                },
                {
                    name: '压力',
                    type: 'line',
                    data: this.trendData.pressure,
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 6,
                    lineStyle: {
                        color: '#34d399',
                        width: 3
                    },
                    itemStyle: {
                        color: '#34d399'
                    },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(52, 211, 153, 0.4)' },
                            { offset: 1, color: 'rgba(52, 211, 153, 0.05)' }
                        ])
                    }
                },
                {
                    name: '回收热量',
                    type: 'line',
                    data: this.trendData.heatRecovery,
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 6,
                    lineStyle: {
                        color: '#fbbf24',
                        width: 3
                    },
                    itemStyle: {
                        color: '#fbbf24'
                    },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(251, 191, 36, 0.4)' },
                            { offset: 1, color: 'rgba(251, 191, 36, 0.05)' }
                        ])
                    }
                }
            ]
        };

        this.trendChart.setOption(option);
    }

    updateEquipmentStatus() {
        const grid = document.getElementById('equipmentGrid');
        if (!grid) return;

        grid.innerHTML = '';

        this.equipmentList.forEach(equipment => {
            const card = document.createElement('div');
            card.className = `equipment-card ${equipment.status}`;

            let statusText = '正常';
            if (equipment.status === 'warning') statusText = '维护';
            else if (equipment.status === 'error') statusText = '故障';

            card.innerHTML = `
                <div class="equipment-name">${equipment.name}</div>
                <div class="equipment-status ${equipment.status}">${statusText}</div>
                ${equipment.health ? `<div class="equipment-health">健康度: ${equipment.health}%</div>` : ''}
            `;

            grid.appendChild(card);
        });
    }

    updateAlerts() {
        const list = document.getElementById('alertList');
        if (!list) return;

        list.innerHTML = '';

        if (this.alerts.length === 0) {
            list.innerHTML = '<div class="alert-item info"><div class="alert-message">暂无预警信息</div></div>';
            return;
        }

        this.alerts.forEach(alert => {
            const item = document.createElement('div');
            item.className = `alert-item ${alert.level}`;

            item.innerHTML = `
                <div class="alert-message">${alert.message}</div>
                <div class="alert-time">${alert.time}</div>
            `;

            list.appendChild(item);
        });
    }

    async loadDecisionAdvice() {
        try {
            const data = await getDecisionAdvice();
            if (data && data.decision) {
                this.recommendations = [{
                    id: 1,
                    content: data.decision.reasoning
                }];
                this.sourceTrace = data.decision.source_trace;
                this.updateRecommendations();
            }
        } catch (error) {
            console.error('加载决策建议失败:', error);
        }
    }

    updateRecommendations() {
        const list = document.getElementById('recommendationList');
        if (!list) return;

        list.innerHTML = '';

        this.recommendations.forEach(recommendation => {
            const item = document.createElement('div');
            item.className = 'recommendation-item';

            item.innerHTML = `
                <div class="recommendation-content">${recommendation.content}</div>
                <div class="recommendation-actions">
                    <div class="tooltip">
                        <button class="action-btn execute" onclick="dashboard.executeAdvice('${recommendation.content}')">立即执行</button>
                        <span class="tooltip-text">执行此操作建议</span>
                    </div>
                    <div class="tooltip">
                        <button class="action-btn view" onclick="dashboard.viewSourceTrace()">查看依据</button>
                        <span class="tooltip-text">查看决策溯源信息</span>
                    </div>
                    <div class="tooltip">
                        <button class="action-btn ignore" onclick="dashboard.ignoreAdvice('${recommendation.content}')">忽略</button>
                        <span class="tooltip-text">忽略此操作建议</span>
                    </div>
                </div>
            `;

            list.appendChild(item);
        });
    }

    viewSourceTrace() {
        const traceElement = document.getElementById('sourceTrace');
        const contentElement = document.getElementById('sourceTraceContent');
        if (!traceElement || !contentElement) return;

        if (this.sourceTrace) {
            let content = '';
            if (typeof this.sourceTrace === 'object') {
                content = JSON.stringify(this.sourceTrace, null, 2);
            } else {
                content = this.sourceTrace;
            }
            contentElement.textContent = content;
            traceElement.style.display = 'block';
        }
    }

    async executeAdvice(advice) {
        const success = await executeDecision(advice);
        if (success) {
            alert('操作建议已执行');
        } else {
            alert('执行操作建议失败');
        }
    }

    async ignoreAdvice(advice) {
        const success = await ignoreDecision(advice);
        if (success) {
            alert('操作建议已忽略');
        } else {
            alert('忽略操作建议失败');
        }
    }

    initEnergyChart() {
        if (!window.echarts) return;

        const container = document.getElementById('energyChart');
        if (!container) return;

        this.energyChart = echarts.init(container);
        this.updateEnergyChart();

        window.addEventListener('resize', () => {
            if (this.energyChart) this.energyChart.resize();
        });
    }

    updateEnergyChart() {
        if (!this.energyChart) return;

        const data = {
            labels: ['反应釜', '换热器', '泵', '冷却系统'],
            actual: [120, 80, 45, 60],
            target: [100, 70, 40, 50]
        };

        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(30, 30, 50, 0.9)',
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1,
                textStyle: {
                    color: '#fff'
                },
                axisPointer: {
                    type: 'shadow'
                }
            },
            legend: {
                data: ['实际能耗', '节能目标'],
                textStyle: {
                    color: 'rgba(255, 255, 255, 0.7)'
                },
                top: 0,
                right: 0
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: data.labels,
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255, 255, 255, 0.2)'
                    }
                },
                axisLabel: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    fontSize: 11
                }
            },
            yAxis: {
                type: 'value',
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255, 255, 255, 0.2)'
                    }
                },
                axisLabel: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    fontSize: 11
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            series: [
                {
                    name: '实际能耗',
                    type: 'bar',
                    data: data.actual,
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#60a5fa' },
                            { offset: 1, color: '#3b82f6' }
                        ])
                    },
                    barWidth: '30%',
                    borderRadius: [4, 4, 0, 0]
                },
                {
                    name: '节能目标',
                    type: 'bar',
                    data: data.target,
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#34d399' },
                            { offset: 1, color: '#10b981' }
                        ])
                    },
                    barWidth: '30%',
                    borderRadius: [4, 4, 0, 0]
                }
            ]
        };

        this.energyChart.setOption(option);
    }

    startRealTimeUpdates() {
        // 更新当前时间
        setInterval(() => {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            const timeElement = document.getElementById('currentTime');
            if (timeElement) {
                timeElement.textContent = timeString;
            }
        }, 1000);

        // 每5秒更新一次数据
        setInterval(async () => {
            try {
                // 更新KPI数据
                this.kpiData = await getKpiData();
                this.updateKpiCards();

                // 更新趋势数据
                this.trendData = await getTrendData();
                this.updateTrendChart();

                // 更新设备状态
                this.equipmentList = await getEquipmentStatus();
                this.updateEquipmentStatus();

                // 更新预警信息
                this.alerts = await getAlerts();
                this.updateAlerts();

                // 更新决策建议
                await this.loadDecisionAdvice();
            } catch (error) {
                console.error('更新数据失败:', error);
            }
        }, 5000);
    }

    /**
     * 导出数据为CSV文件
     */
    exportToCSV() {
        let csvContent = "数据类型,当前值,预测值\n";
        
        if (this.kpiData) {
            csvContent += `余热温度,${this.kpiData.temperature},${this.kpiData.temperaturePrediction}\n`;
            csvContent += `系统压力,${this.kpiData.pressure},${this.kpiData.pressurePrediction}\n`;
            csvContent += `余热回收,${this.kpiData.heatRecovery},${this.kpiData.heatRecoveryPrediction}\n`;
            csvContent += `节能效果,${this.kpiData.energySaving},${this.kpiData.energySavingPrediction}\n`;
        }

        if (this.trendData) {
            csvContent += "\n时间,温度,压力,回收热量\n";
            for (let i = 0; i < this.trendData.labels.length; i++) {
                csvContent += `${this.trendData.labels[i]},${this.trendData.temperature[i]},${this.trendData.pressure[i]},${this.trendData.heatRecovery[i]}\n`;
            }
        }

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `化工余热数据_${new Date().toISOString().slice(0, 10)}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * 导出图表为图片
     * @param {string} chartType - 图表类型
     */
    exportChart(chartType) {
        let chart;
        let filename;

        if (chartType === 'trend') {
            chart = this.trendChart;
            filename = '趋势分析图';
        } else if (chartType === 'energy') {
            chart = this.energyChart;
            filename = '能耗分析图';
        }

        if (chart) {
            const dataURL = chart.getDataURL({
                pixelRatio: 2,
                backgroundColor: '#1a1a2e'
            });

            const link = document.createElement('a');
            link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.png`;
            link.href = dataURL;
            link.click();
        }
    }

    /**
     * 发送会话消息
     */
    async sendMessage() {
        const inputElement = document.getElementById('messageInput');
        const message = inputElement.value.trim();
        if (!message) return;

        // 清空输入框
        inputElement.value = '';

        // 添加用户消息到会话历史
        this.conversationHistory.push({
            role: 'user',
            content: message
        });
        this.updateConversationHistory();

        // 发送消息到API
        try {
            const response = await sendMessage(this.sessionId, message);
            if (response.status === 'success') {
                // 更新会话历史
                this.conversationHistory = response.conversation;
                this.updateConversationHistory();
                
                // 显示操作依据
                this.showContextTrace(response.context_trace);
            }
        } catch (error) {
            console.error('发送消息失败:', error);
        }
    }

    /**
     * 更新会话历史显示
     */
    updateConversationHistory() {
        const historyElement = document.getElementById('conversationHistory');
        if (!historyElement) return;

        historyElement.innerHTML = '';

        this.conversationHistory.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${message.role}`;
            messageElement.innerHTML = `
                <div class="message-content">${message.content}</div>
            `;
            historyElement.appendChild(messageElement);
        });

        // 滚动到底部
        historyElement.scrollTop = historyElement.scrollHeight;
    }

    /**
     * 显示操作依据
     * @param {string} contextTrace - 操作依据
     */
    showContextTrace(contextTrace) {
        const traceElement = document.getElementById('contextTrace');
        const contentElement = document.getElementById('contextTraceContent');
        if (!traceElement || !contentElement) return;

        contentElement.textContent = contextTrace;
        traceElement.style.display = 'block';
    }
}
