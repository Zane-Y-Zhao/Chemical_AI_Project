/**
 * 预警面板组件
 * 用于显示系统的预警信息
 */

class AlertPanel {
    constructor(container, options) {
        this.container = container;
        this.options = {
            title: '预警信息',
            alerts: [],
            ...options
        };
        this.render();
    }

    render() {
        const panel = document.createElement('div');
        panel.className = 'alerts';

        panel.innerHTML = `
            <h2>⚠️ ${this.options.title}</h2>
            <div class="alert-list" id="alertList"></div>
        `;

        this.container.appendChild(panel);
        this.updateAlerts(this.options.alerts);
    }

    updateAlerts(alerts) {
        const list = document.getElementById('alertList');
        if (!list) return;

        list.innerHTML = '';

        if (alerts.length === 0) {
            list.innerHTML = '<div class="alert-item info"><div class="alert-message">暂无预警信息</div></div>';
            return;
        }

        alerts.forEach(alert => {
            const item = document.createElement('div');
            item.className = `alert-item ${alert.level}`;

            item.innerHTML = `
                <div class="alert-message">${alert.message}</div>
                <div class="alert-time">${alert.time}</div>
            `;

            list.appendChild(item);
        });
    }

    update(alerts) {
        this.options.alerts = alerts;
        this.updateAlerts(alerts);
    }

    addAlert(alert) {
        this.options.alerts.unshift(alert);
        // 限制预警数量
        if (this.options.alerts.length > 10) {
            this.options.alerts = this.options.alerts.slice(0, 10);
        }
        this.updateAlerts(this.options.alerts);
    }
}