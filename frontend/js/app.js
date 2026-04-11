/**
 * 应用主入口文件
 * 初始化应用并加载所有组件
 */

import { DashboardView } from './views/DashboardView.js';

// 全局变量，用于在HTML中调用方法
window.dashboard = null;

// 鼠标跟随光影效果
function initLightEffect() {
    // 创建光影元素
    const lightEffect = document.createElement('div');
    lightEffect.className = 'light-effect';
    document.body.appendChild(lightEffect);
    
    // 鼠标移动事件监听
    document.addEventListener('mousemove', (e) => {
        const { clientX, clientY } = e;
        lightEffect.style.left = `${clientX - 150}px`;
        lightEffect.style.top = `${clientY - 150}px`;
    });
    
    // 触摸移动事件监听（移动设备）
    document.addEventListener('touchmove', (e) => {
        if (e.touches.length > 0) {
            const { clientX, clientY } = e.touches[0];
            lightEffect.style.left = `${clientX - 150}px`;
            lightEffect.style.top = `${clientY - 150}px`;
        }
    });
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('app');
    if (container) {
        // 初始化鼠标跟随光影效果
        initLightEffect();
        
        // 初始化仪表盘视图
        window.dashboard = new DashboardView(container);
        console.log('化工余热智能管理系统初始化完成');
    } else {
        console.error('未找到应用容器元素');
    }
});

