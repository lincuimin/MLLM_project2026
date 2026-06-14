#!/usr/bin/env node

/**
 * 示例3：批量任务执行和统计
 * 展示如何执行多个任务并获得统计数据
 */

import { MultimodalWebAgent } from '../dist/index.js';

async function example3_BatchTasks() {
    console.log('📌 示例3：批量任务执行和统计\n');

    const agent = new MultimodalWebAgent({
        deepseekApiKey: process.env.DEEPSEEK_API_KEY,
        qwenApiKey: process.env.QWEN_API_KEY,
        maxIterations: 8,
    });

    // 定义多个测试任务
    const tasks = [
        {
            description: '任务1：搜索Python',
            instruction: '在搜索框输入"Python编程"并搜索',
        },
        {
            description: '任务2：导航和返回',
            instruction: '点击第一个搜索结果，然后点击返回按钮',
        },
        {
            description: '任务3：页面信息提取',
            instruction: '获取当前页面的标题和URL',
        },
    ];

    console.log(`执行 ${tasks.length} 个任务...\n`);

    const results = await agent.executeBatch('https://www.google.com', tasks);

    // 统计结果
    const successCount = results.filter((r) => r.success).length;
    const successRate = ((successCount / results.length) * 100).toFixed(1);

    console.log('═'.repeat(60));
    console.log('📊 批量执行统计');
    console.log('═'.repeat(60));
    console.log(`总任务数: ${results.length}`);
    console.log(`成功数: ${successCount}`);
    console.log(`失败数: ${results.length - successCount}`);
    console.log(`成功率: ${successRate}%\n`);

    // 详细结果
    console.log('详细结果:');
    results.forEach((result, index) => {
        const status = result.success ? '✅' : '❌';
        console.log(`${status} ${tasks[index].description}`);
        console.log(`   耗时: ${result.duration}ms`);
        console.log(`   步骤: ${result.stepsExecuted.length}/${result.totalSteps}`);
        console.log(`   总结: ${result.summary}`);
    });

    console.log('\n' + '═'.repeat(60));
    console.log(`整体成功率: ${successRate}%`);
    console.log('═'.repeat(60) + '\n');
}

export { example3_BatchTasks };

if (import.meta.url === `file://${process.argv[1]}`) {
    example3_BatchTasks().catch(console.error);
}
