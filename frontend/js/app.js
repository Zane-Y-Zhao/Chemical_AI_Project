/**
 * 应用主入口文件
 * 初始化应用并加载所有组件
 */

import { DashboardView } from './views/DashboardView.js';

// 全局变量，用于在HTML中调用方法
window.dashboard = null;

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('app');
    if (container) {
        // 初始化仪表盘视图
        window.dashboard = new DashboardView(container);
        console.log('化工余热智能管理系统初始化完成');
    } else {
        console.error('未找到应用容器元素');
    }
});

