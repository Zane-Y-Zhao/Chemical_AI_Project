/**
 * KPI卡片组件
 * 用于显示关键性能指标
 */

class KpiCard {
    constructor(container, options) {
        this.container = container;
        this.options = {
            label: '',
            value: 0,
            unit: '',
            prediction: null,
            ...options
        };
        this.render();
    }

    render() {
        const card = document.createElement('div');
        card.className = 'kpi-card';

        card.innerHTML = `
            <div class="kpi-label">${this.options.label}</div>
            <div class="kpi-value">${this.options.value}${this.options.unit}</div>
            ${this.options.prediction !== null ? 
                `<div class="kpi-prediction">预测: ${this.options.prediction}${this.options.unit}</div>` : ''}
        `;

        this.container.appendChild(card);
    }

    update(value, prediction = null) {
        this.options.value = value;
        this.options.prediction = prediction;
        this.container.innerHTML = '';
        this.render();
    }
}