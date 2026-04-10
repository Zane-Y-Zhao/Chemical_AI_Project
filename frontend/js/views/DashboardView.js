/**
 * 仪表盘视图组件
 * 整合所有子组件，形成完整的监控大屏
 */

import { getKpiData, getTrendData, getEquipmentStatus, getAlerts } from '../api/dataClient.js';
import { getDecisionAdvice, executeDecision, ignoreDecision } from '../api/decisionClient.js';

export class DashboardView {
    constructor(container) {
        this.container = container;
        this.kpiData = null;
        this.trendData = null;
        this.equipmentList = [];
        this.alerts = [];
        this.recommendations = [];
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
                    <h1>🏭 化工余热智能管理系统</h1>
                    <div class="header-actions">
                        <div class="tooltip">
                            <button class="action-btn execute" onclick="dashboard.exportData('csv')">导出CSV</button>
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

                <!-- 主要内容 -->
                <div class="grid">
                    <!-- 综合概览 -->
                    <div class="overview card">
                        <h2>📊 综合概览</h2>
                        <div class="kpi-grid" id="kpiGrid"></div>
                    </div>

                    <!-- 趋势分析 -->
                    <div class="trends card">
                        <div class="card-header">
                            <h2>📈 趋势分析</h2>
                            <div class="card-actions">
                                <div class="tooltip">
                                    <button class="action-btn view" onclick="dashboard.exportChart('trend')">导出图表</button>
                                    <span class="tooltip-text">导出趋势分析图表为图片</span>
                                </div>
                            </div>
                        </div>
                        <div class="chart-container" id="trendChart"></div>
                    </div>

                    <!-- 预警信息 -->
                    <div class="alerts card">
                        <h2>⚠️ 预警信息</h2>
                        <div class="alert-list" id="alertList"></div>
                    </div>

                    <!-- 能耗分析 -->
                    <div class="analysis card">
                        <div class="card-header">
                            <h2>📊 能耗分析</h2>
                            <div class="card-actions">
                                <div class="tooltip">
                                    <button class="action-btn view" onclick="dashboard.exportChart('energy')">导出图表</button>
                                    <span class="tooltip-text">导出能耗分析图表为图片</span>
                                </div>
                            </div>
                        </div>
                        <div class="energy-chart" id="energyChart"></div>
                    </div>

                    <!-- 智能操作建议 -->
                    <div class="recommendations card">
                        <div class="card-header">
                            <h2>💡 智能操作建议</h2>
                        </div>
                        <div class="recommendation-list" id="recommendationList"></div>
                        <div class="source-trace" id="sourceTrace" style="display: none;">
                            <h4>🔍 溯源依据</h4>
                            <div class="source-trace-content" id="sourceTraceContent"></div>
                            <button class="action-btn close" onclick="document.getElementById('sourceTrace').style.display = 'none'">关闭</button>
                        </div>
                    </div>

                    <!-- 设备状态 -->
                    <div class="equipment card">
                        <h2>🏗️ 设备状态</h2>
                        <div class="equipment-grid" id="equipmentGrid"></div>
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
                <div class="kpi-value">${kpi.value}${kpi.unit}</div>
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
            this.trendChart.resize();
        });
    }

    updateTrendChart() {
        if (!this.trendChart || !this.trendData) return;

        const option = {
            tooltip: {
                trigger: 'item',
                triggerOn: 'mousemove|click',
                axisPointer: {
                    type: 'cross',
                    snap: true,
                    label: {
                        backgroundColor: '#6a7985'
                    }
                },
                formatter: function(params) {
                    let unit = '';
                    if (params.seriesName === '温度') unit = ' °C';
                    else if (params.seriesName === '压力') unit = ' MPa';
                    else if (params.seriesName === '回收热量') unit = ' kJ';
                    return params.name + '<br/>' + params.marker + params.seriesName + ': ' + params.value + unit;
                },
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                textStyle: {
                    color: '#fff'
                },
                borderColor: '#1976D2',
                borderWidth: 1
            },
            legend: {
                data: ['温度', '压力', '回收热量'],
                textStyle: {
                    color: '#333'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: this.trendData.labels,
                axisLabel: {
                    color: '#333'
                }
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    color: '#333'
                }
            },
            series: [
                {
                    name: '温度',
                    type: 'line',
                    data: this.trendData.temperature,
                    smooth: true,
                    itemStyle: {
                        color: '#1976D2'
                    },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(25, 118, 210, 0.3)' },
                            { offset: 1, color: 'rgba(25, 118, 210, 0.1)' }
                        ])
                    }
                },
                {
                    name: '压力',
                    type: 'line',
                    data: this.trendData.pressure,
                    smooth: true,
                    itemStyle: {
                        color: '#2196F3'
                    },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(33, 150, 243, 0.3)' },
                            { offset: 1, color: 'rgba(33, 150, 243, 0.1)' }
                        ])
                    }
                },
                {
                    name: '回收热量',
                    type: 'line',
                    data: this.trendData.heatRecovery,
                    smooth: true,
                    itemStyle: {
                        color: '#64B5F6'
                    },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(100, 181, 246, 0.3)' },
                            { offset: 1, color: 'rgba(100, 181, 246, 0.1)' }
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
            if (equipment.status === 'warning') statusText = '需要维护';
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
            this.energyChart.resize();
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
            tooltip: {
                trigger: 'item',
                triggerOn: 'mousemove|click',
                axisPointer: {
                    type: 'shadow',
                    snap: true
                },
                formatter: function(params) {
                    return params.name + '<br/>' + params.marker + params.seriesName + ': ' + params.value + ' kW';
                },
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                textStyle: {
                    color: '#fff'
                },
                borderColor: '#1976D2',
                borderWidth: 1
            },
            legend: {
                data: ['实际能耗', '节能目标'],
                textStyle: {
                    color: '#333'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: data.labels,
                axisLabel: {
                    color: '#333'
                }
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    color: '#333',
                    formatter: '{value} kW'
                }
            },
            series: [
                {
                    name: '实际能耗',
                    type: 'bar',
                    data: data.actual,
                    itemStyle: {
                        color: '#1976D2'
                    }
                },
                {
                    name: '节能目标',
                    type: 'bar',
                    data: data.target,
                    itemStyle: {
                        color: '#64B5F6'
                    }
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
     * @param {string} format - 导出格式
     */
    exportData(format) {
        if (format === 'csv') {
            this.exportToCSV();
        }
    }

    /**
     * 导出数据为CSV文件
     */
    exportToCSV() {
        // 准备CSV数据
        let csvContent = "数据类型,当前值,预测值\n";
        
        if (this.kpiData) {
            csvContent += `余热温度,${this.kpiData.temperature},${this.kpiData.temperaturePrediction}\n`;
            csvContent += `系统压力,${this.kpiData.pressure},${this.kpiData.pressurePrediction}\n`;
            csvContent += `余热回收,${this.kpiData.heatRecovery},${this.kpiData.heatRecoveryPrediction}\n`;
            csvContent += `节能效果,${this.kpiData.energySaving},${this.kpiData.energySavingPrediction}\n`;
        }

        // 添加趋势数据
        if (this.trendData) {
            csvContent += "\n时间,温度,压力,回收热量\n";
            for (let i = 0; i < this.trendData.labels.length; i++) {
                csvContent += `${this.trendData.labels[i]},${this.trendData.temperature[i]},${this.trendData.pressure[i]},${this.trendData.heatRecovery[i]}\n`;
            }
        }

        // 创建下载链接
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
            // 使用ECharts的toBase64Image方法
            const dataURL = chart.getDataURL({
                pixelRatio: 2, // 提高图片清晰度
                backgroundColor: '#fff'
            });

            // 创建下载链接
            const link = document.createElement('a');
            link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.png`;
            link.href = dataURL;
            link.click();
        }
    }
}