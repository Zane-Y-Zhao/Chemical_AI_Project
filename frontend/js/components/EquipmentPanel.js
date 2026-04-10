/**
 * 设备状态面板组件
 * 用于显示设备的运行状态和健康度
 */

class EquipmentPanel {
    constructor(container, options) {
        this.container = container;
        this.options = {
            title: '设备状态',
            equipmentList: [],
            ...options
        };
        this.render();
    }

    render() {
        const panel = document.createElement('div');
        panel.className = 'equipment';

        panel.innerHTML = `
            <h2>🏗️ ${this.options.title}</h2>
            <div class="equipment-grid" id="equipmentGrid"></div>
        `;

        this.container.appendChild(panel);
        this.updateEquipmentList(this.options.equipmentList);
    }

    updateEquipmentList(equipmentList) {
        const grid = document.getElementById('equipmentGrid');
        if (!grid) return;

        grid.innerHTML = '';

        equipmentList.forEach(equipment => {
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

    update(equipmentList) {
        this.options.equipmentList = equipmentList;
        this.updateEquipmentList(equipmentList);
    }
}