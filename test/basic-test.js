#!/usr/bin/env node

/**
 * 基础测试 - 验证浏览器自动化功能
 */

import { BrowserAutomation } from '../dist/core/browser-automation.js';

async function runBasicTest() {
    const browser = new BrowserAutomation();

    try {
        console.log('🧪 启动浏览器基础测试\n');

        // 1. 启动浏览器
        console.log('1️⃣  启动浏览器...');
        await browser.launch({ headless: true });
        console.log('✅ 浏览器已启动\n');

        // 2. 导航到Google
        console.log('2️⃣  导航到Google...');
        await browser.goto('https://www.google.com');
        console.log('✅ 导航成功\n');

        // 3. 获取页面标题
        console.log('3️⃣  获取页面标题...');
        const title = await browser.getPageTitle();
        console.log(`✅ 页面标题: ${title}\n`);

        // 4. 获取页面URL
        console.log('4️⃣  获取当前URL...');
        const url = await browser.getCurrentURL();
        console.log(`✅ 当前URL: ${url}\n`);

        // 5. 获取截图
        console.log('5️⃣  获取页面截图...');
        const screenshot = await browser.screenshot();
        console.log(`✅ 截图成功 (${screenshot.length} bytes)\n`);

        // 6. 获取交互元素
        console.log('6️⃣  获取可交互元素...');
        const elements = await browser.getInteractiveElements();
        console.log(`✅ 找到 ${elements.length} 个可交互元素\n`);

        // 7. 在搜索框输入
        console.log('7️⃣  在搜索框输入文本...');
        await browser.fill('input[name="q"]', 'Playwright automation');
        console.log('✅ 输入成功\n');

        // 8. 获取输入值
        console.log('8️⃣  验证输入值...');
        const formData = await browser.getFormData();
        console.log('✅ 表单数据:', formData);
        console.log('');

        console.log('🎉 所有基础测试通过！\n');
    } catch (error: any) {
        console.error('❌ 测试失败:', error.message);
    } finally {
        await browser.close();
    }
}

runBasicTest();
