#!/usr/bin/env node

/**
 * 示例2：表单填写和提交
 * 展示如何使用Agent填写表单
 */

import { MultimodalWebAgent } from '../dist/index.js';

async function example2_FormFilling() {
    console.log('📌 示例2：表单填写和提交\n');

    const agent = new MultimodalWebAgent({
        deepseekApiKey: process.env.DEEPSEEK_API_KEY,
        qwenApiKey: process.env.QWEN_API_KEY,
    });

    // 使用本地测试表单（如果可用）或真实网站
    const result = await agent.executeTask(
        'https://example.com',
        '填写页面上的联系表单：' +
        '名称: John Doe, ' +
        '邮箱: john@example.com, ' +
        '消息: 我想了解更多信息, ' +
        '然后点击提交按钮'
    );

    console.log('📊 执行结果:');
    console.log(`   成功: ${result.success}`);
    console.log(`   执行步骤: ${result.stepsExecuted.length}`);
    console.log(`   失败数: ${result.failures.length}`);
    console.log(`   总结: ${result.summary}\n`);

    // 打印失败记录（如有）
    if (result.failures.length > 0) {
        console.log('❌ 失败记录:');
        result.failures.forEach((f) => {
            console.log(`   - 步骤${f.stepId}: ${f.action} - ${f.error}`);
            console.log(`     已恢复: ${f.recovered}`);
        });
    }
}

export { example2_FormFilling };

if (import.meta.url === `file://${process.argv[1]}`) {
    example2_FormFilling().catch(console.error);
}
