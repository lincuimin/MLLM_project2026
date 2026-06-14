#!/usr/bin/env node

/**
 * 示例1：简单搜索任务
 * 展示如何使用MultimodalWebAgent执行简单的Google搜索
 */

import { MultimodalWebAgent } from '../dist/index.js';

async function example1_SimpleSearch() {
    console.log('📌 示例1：简单搜索任务\n');

    const agent = new MultimodalWebAgent({
        deepseekApiKey: process.env.DEEPSEEK_API_KEY,
        qwenApiKey: process.env.QWEN_API_KEY,
    });

    const result = await agent.executeTask(
        'https://www.google.com',
        '在搜索框输入"Playwright自动化"，按Enter搜索，等待结果加载'
    );

    console.log('📊 执行结果:');
    console.log(`   成功: ${result.success}`);
    console.log(`   执行时间: ${result.duration}ms`);
    console.log(`   执行步骤: ${result.stepsExecuted.length}`);
    console.log(`   最终URL: ${result.finalURL}`);
    console.log(`   总结: ${result.summary}\n`);
}

export { example1_SimpleSearch };

// 如果直接运行此文件
if (import.meta.url === `file://${process.argv[1]}`) {
    example1_SimpleSearch().catch(console.error);
}
