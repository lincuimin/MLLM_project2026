#!/usr/bin/env node

/**
 * Agent集成测试 - 测试完整的多模态Agent流程
 */

import { MultimodalWebAgent } from '../dist/agent/multimodal-web-agent.js';

async function runAgentTest() {
    const agent = new MultimodalWebAgent({
        deepseekApiKey: process.env.DEEPSEEK_API_KEY || 'test-key',
        qwenApiKey: process.env.QWEN_API_KEY || 'test-key',
    });

    console.log('🧪 开始Agent集成测试\n');

    // 测试任务
    const testTasks = [
        {
            url: 'https://www.wikipedia.org',
            instruction: '搜索"Artificial Intelligence"',
            description: '搜索测试',
        },
        {
            url: 'https://www.example.com',
            instruction: '获取页面标题和当前URL',
            description: '页面信息提取',
        },
    ];

    for (const task of testTasks) {
        console.log(`📌 任务: ${task.description}`);
        console.log(`   指令: ${task.instruction}`);
        console.log('');

        try {
            const result = await agent.executeTask(task.url, task.instruction, { headless: true });

            console.log(`📊 执行结果:`);
            console.log(`   成功: ${result.success}`);
            console.log(`   执行步骤数: ${result.stepsExecuted.length}`);
            console.log(`   失败数: ${result.failures.length}`);
            console.log(`   信心度: ${(result.confidence * 100).toFixed(0)}%`);
            console.log(`   耗时: ${result.duration}ms`);
            console.log(`   总结: ${result.summary}`);
            console.log('');
        } catch (error: any) {
            console.error(`❌ 任务失败: ${error.message}\n`);
        }
    }

    console.log('🎉 Agent集成测试完成！\n');
}

runAgentTest();
