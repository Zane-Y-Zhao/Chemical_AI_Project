/**
 * 能耗分析图组件
 * 用于显示能耗对比数据
 */

class EnergyChart {
    constructor(container, options) {
        this.container = container;
        this.options = {
            title: '能耗分析',
            data: {
                labels: ['反应釜', '换热器', '泵', '冷却系统'],
                actual: [120, 80, 45, 60],
                target: [100, 70, 40, 50]
            },
            ...options
        };
        this.chart = null;
        this.init();
    }

    init() {
        if (!window.echarts) {
            console.error('ECharts not loaded');
            return;
        }

        this.chart = echarts.init(this.container);
        this.update(this.options.data);

        // 响应式调整
        window.addEventListener('resize', () => {
            this.chart.resize();
        });
    }

    update(data) {
        if (!this.chart) return;

        const option = {
            title: {
                text: this.options.title,
                left: 'center',
                textStyle: {
                    color: '#1976D2',
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
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

        this.chart.setOption(option);
    }

    resize() {
        if (this.chart) {
            this.chart.resize();
        }
    }
}