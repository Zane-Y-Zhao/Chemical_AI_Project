/**
 * 趋势图组件
 * 用于显示温度、压力和热量回收的趋势
 */

class TrendChart {
    constructor(container, options) {
        this.container = container;
        this.options = {
            title: '',
            data: {
                labels: [],
                temperature: [],
                pressure: [],
                heatRecovery: []
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
                data: data.labels,
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
                    data: data.temperature,
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
                    data: data.pressure,
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
                    data: data.heatRecovery,
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

        this.chart.setOption(option);
    }

    resize() {
        if (this.chart) {
            this.chart.resize();
        }
    }
}