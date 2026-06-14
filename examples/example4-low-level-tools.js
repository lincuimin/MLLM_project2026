#!/usr/bin/env node

/**
 * 示例4：低级工具使用
 * 展示如何直接使用浏览器、VLM和LLM工具
 */

import {
    BrowserAutomation,
    VLMService,
    LLMService,
} from '../dist/index.js';

async function example4_LowLevelTools() {
    console.log('📌 示例4：低级工具使用\n');

    const browser = new BrowserAutomation();
    const vlm = new VLMService({ apiKey: process.env.QWEN_API_KEY });
    const llm = new LLMService({ apiKey: process.env.DEEPSEEK_API_KEY });

    try {
        // 1. 使用浏览器工具
        console.log('1️⃣  使用浏览器工具');
        console.log('   启动浏览器...');
        await browser.launch({ headless: true });

        console.log('   导航到Wikipedia...');
        await browser.goto('https://www.wikipedia.org');

        console.log('   获取页面信息...');
        const title = await browser.getPageTitle();
        const url = await browser.getCurrentURL();
        console.log(`   标题: ${title}`);
        console.log(`   URL: ${url}\n`);

        // 2. 使用VLM工具
        console.log('2️⃣  使用VLM工具');
        console.log('   获取截图...');
        const screenshot = await browser.screenshot();
        console.log(`   截图大小: ${screenshot.length} bytes`);

        console.log('   分析截图...');
        const analysis = await vlm.analyzeScreenshot(
            screenshot,
            '分析这个网页的主要内容和可交互元素'
        );
        console.log(`   分析结果: ${analysis.description.substring(0, 100)}...\n`);

        // 3. 使用LLM工具
        console.log('3️⃣  使用LLM工具');
        console.log('   生成行动计划...');
        const plan = await llm.generatePlan(
            {
                url,
                title,
                content: 'Wikipedia主页',
            },
            '搜索Artificial Intelligence'
        );
        console.log(`   计划步骤数: ${plan.steps.length}`);
        console.log(`   信心度: ${(plan.confidence * 100).toFixed(0)}%`);
        plan.steps.slice(0, 3).forEach((step) => {
            console.log(`   - ${step.action}: ${step.description}`);
        });
        console.log('');

        // 4. 执行计划的第一步
        console.log('4️⃣  执行计划');
        if (plan.steps.length > 0) {
            const firstStep = plan.steps[0];
            console.log(`   执行: ${firstStep.action} - ${firstStep.description}`);

            if (firstStep.action === 'click' && firstStep.selector) {
                try {
                    await browser.click(firstStep.selector);
                    console.log('   ✅ 步骤执行成功\n');
                } catch (e) {
                    console.log('   ⚠️  步骤执行失败（这是正常的示例）\n');
                }
            }
        }

        console.log('🎉 示例完成！\n');
    } catch (error: any) {
        console.error('❌ 错误:', error.message);
    } finally {
        await browser.close();
    }
}

export { example4_LowLevelTools };

if (import.meta.url === `file://${process.argv[1]}`) {
    example4_LowLevelTools().catch(console.error);
}
