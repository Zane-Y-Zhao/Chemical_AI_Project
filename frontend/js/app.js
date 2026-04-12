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
        const half = 210;
        lightEffect.style.left = `${clientX - half}px`;
        lightEffect.style.top = `${clientY - half}px`;
    });
    
    // 触摸移动事件监听（移动设备）
    document.addEventListener('touchmove', (e) => {
        if (e.touches.length > 0) {
            const { clientX, clientY } = e.touches[0];
            const half = 210;
            lightEffect.style.left = `${clientX - half}px`;
            lightEffect.style.top = `${clientY - half}px`;
        }
    });
}

// 初始化化工元素装饰
function initChemicalDecorations() {
    const app = document.getElementById('app');
    if (!app) return;
    
    // 创建原子装饰元素
    const atoms = [
        { top: '10%', left: '15%' },
        { top: '60%', left: '85%' },
        { top: '30%', left: '70%' },
        { top: '80%', left: '20%' }
    ];
    
    atoms.forEach((pos, index) => {
        const atom = document.createElement('div');
        atom.className = 'chemical-decoration atom';
        atom.style.top = pos.top;
        atom.style.left = pos.left;
        atom.style.animationDelay = `${index * 2}s`;
        app.appendChild(atom);
    });
    
    // 创建管道装饰元素
    const pipes = [
        { top: '25%', left: '10%', rotate: '0deg' },
        { top: '75%', left: '50%', rotate: '90deg' },
        { top: '45%', left: '80%', rotate: '45deg' }
    ];
    
    pipes.forEach((pos, index) => {
        const pipe = document.createElement('div');
        pipe.className = 'chemical-decoration pipe';
        pipe.style.top = pos.top;
        pipe.style.left = pos.left;
        pipe.style.transform = `rotate(${pos.rotate})`;
        pipe.style.animationDelay = `${index * 0.5}s`;
        app.appendChild(pipe);
    });
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('app');
    if (container) {
        // 初始化鼠标跟随光影效果
        initLightEffect();
        
        // 初始化化工元素装饰
        initChemicalDecorations();
        
        // 初始化仪表盘视图
        window.dashboard = new DashboardView(container);
        console.log('化工余热智能管理系统初始化完成');
    } else {
        console.error('未找到应用容器元素');
    }
});

