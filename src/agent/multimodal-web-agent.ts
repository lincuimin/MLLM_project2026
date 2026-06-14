import { BrowserAutomation } from '../core/browser-automation.js';
import { VLMService } from '../services/vlm-service.js';
import { LLMService, type ActionStep, type LLMPlan } from '../services/llm-service.js';

export interface ExecutionResult {
    success: boolean;
    taskDescription: string;
    stepsExecuted: ActionStep[];
    totalSteps: number;
    finalURL: string;
    finalScreenshot?: string;
    summary: string;
    failures: FailureRecord[];
    duration: number;
    confidence: number;
}

export interface FailureRecord {
    stepId: number;
    action: string;
    error: string;
    timestamp: number;
    recovered: boolean;
}

/**
 * 网页多模态Agent协调引擎
 * 协调VLM、LLM、浏览器自动化完成复杂任务
 */
export class MultimodalWebAgent {
    private browser: BrowserAutomation;
    private vlmService: VLMService;
    private llmService: LLMService;
    private executionHistory: ActionStep[] = [];
    private failureRecords: FailureRecord[] = [];
    private maxIterations: number;
    private timeout: number;

    constructor(options: {
        deepseekApiKey?: string;
        qwenApiKey?: string;
        maxIterations?: number;
        timeout?: number;
    } = {}) {
        this.browser = new BrowserAutomation();
        this.vlmService = new VLMService({
            apiKey: options.qwenApiKey || process.env.QWEN_API_KEY || '',
        });
        this.llmService = new LLMService({
            apiKey: options.deepseekApiKey || process.env.DEEPSEEK_API_KEY || '',
        });
        this.maxIterations = options.maxIterations || 10;
        this.timeout = options.timeout || 30000;
    }

    /**
     * 执行用户指令（主执行函数）
     */
    async executeTask(url: string, instruction: string, options: { headless?: boolean } = {}): Promise<ExecutionResult> {
        const startTime = Date.now();
        const result: ExecutionResult = {
            success: false,
            taskDescription: instruction,
            stepsExecuted: [],
            totalSteps: 0,
            finalURL: url,
            summary: '',
            failures: [],
            duration: 0,
            confidence: 0,
        };

        try {
            console.log(`🚀 开始执行任务: ${instruction}`);

            // 1. 启动浏览器
            console.log('📱 启动浏览器...');
            await this.browser.launch({
                headless: options.headless !== false,
            });

            // 2. 导航到URL
            console.log(`🌐 导航到: ${url}`);
            await this.browser.goto(url);
            await this.sleep(2000); // 等待页面加载

            // 3. 主循环：规划和执行
            let iteration = 0;
            while (iteration < this.maxIterations) {
                iteration++;
                console.log(`\n📋 迭代 ${iteration}/${this.maxIterations}`);

                try {
                    // 3.1 获取页面状态（VLM视觉理解）
                    console.log('📸 分析页面视觉...');
                    const screenshot = await this.browser.screenshot();
                    const html = await this.browser.getPageHTML();
                    const interactiveElements = await this.browser.getInteractiveElements();
                    const pageTitle = await this.browser.getPageTitle();
                    const currentURL = await this.browser.getCurrentURL();

                    // 3.2 生成行动计划（LLM规划）
                    console.log('🧠 生成行动计划...');
                    const plan = await this.llmService.generatePlan(
                        {
                            url: currentURL,
                            title: pageTitle,
                            interactiveElements,
                            content: html.slice(0, 2000),
                        },
                        instruction,
                        this.executionHistory
                    );

                    result.totalSteps = plan.steps.length;
                    console.log(`💡 计划步骤数: ${plan.steps.length}`);
                    console.log(`📊 信心度: ${(plan.confidence * 100).toFixed(0)}%`);

                    // 3.3 执行计划的第一步
                    if (plan.steps.length > 0) {
                        const step = plan.steps[0];
                        console.log(`\n⚙️  执行步骤 ${step.id}: ${step.action}`);
                        console.log(`   描述: ${step.description}`);

                        const stepSuccess = await this.executeStep(step, screenshot);

                        if (stepSuccess) {
                            result.stepsExecuted.push(step);
                            this.executionHistory.push(step);
                            console.log('✅ 步骤执行成功');

                            // 等待页面稳定
                            await this.sleep(1000);

                            // 3.4 评估任务是否完成
                            console.log('🔍 评估任务完成情况...');
                            const evaluation = await this.llmService.evaluateCompletion(
                                instruction,
                                {
                                    screenshot,
                                    url: currentURL,
                                    content: html,
                                    title: pageTitle,
                                },
                                result.stepsExecuted
                            );

                            if (evaluation.completed) {
                                console.log('🎉 任务已完成！');
                                result.success = true;
                                result.confidence = evaluation.confidence;
                                result.summary = `成功完成任务。执行了 ${result.stepsExecuted.length} 个步骤。`;
                                break;
                            }
                        } else {
                            // 步骤执行失败，记录并尝试恢复
                            console.log('❌ 步骤执行失败，尝试恢复...');
                            const failureRecord: FailureRecord = {
                                stepId: step.id,
                                action: step.action,
                                error: '执行失败',
                                timestamp: Date.now(),
                                recovered: false,
                            };

                            // 尝试使用备选方案
                            if (step.fallback) {
                                console.log('🔄 尝试备选方案...');
                                const fallbackSuccess = await this.executeStep(step.fallback, screenshot);
                                if (fallbackSuccess) {
                                    console.log('✅ 备选方案成功');
                                    result.stepsExecuted.push(step.fallback);
                                    this.executionHistory.push(step.fallback);
                                    failureRecord.recovered = true;
                                }
                            }

                            this.failureRecords.push(failureRecord);
                            result.failures.push(failureRecord);
                        }
                    } else {
                        console.log('⚠️  计划没有步骤');
                        break;
                    }
                } catch (iterationError: any) {
                    console.error(`迭代 ${iteration} 出错:`, iterationError.message);

                    if (iteration >= this.maxIterations) {
                        result.summary = `任务执行失败，已达到最大迭代次数。错误: ${iterationError.message}`;
                    }
                }

                // 检查超时
                if (Date.now() - startTime > this.timeout) {
                    console.warn('⏱️  执行超时');
                    result.summary = '任务执行超时';
                    break;
                }
            }

            // 4. 最终截图
            result.finalScreenshot = await this.browser.screenshot();
            result.finalURL = await this.browser.getCurrentURL();

            if (!result.success && !result.summary) {
                result.summary =
                    `任务未完成。执行了 ${result.stepsExecuted.length} 个步骤，` +
                    `失败 ${result.failures.length} 次。`;
            }
        } catch (error: any) {
            console.error('任务执行出错:', error.message);
            result.summary = `任务执行出错: ${error.message}`;
        } finally {
            // 关闭浏览器
            console.log('🔌 关闭浏览器...');
            await this.browser.close();

            result.duration = Date.now() - startTime;
            console.log(`⏱️  总耗时: ${result.duration}ms`);
            console.log(`✨ 最终结果: ${result.success ? '成功' : '失败'}\n`);
        }

        return result;
    }

    /**
     * 执行单个步骤
     */
    private async executeStep(step: ActionStep, currentScreenshot?: string): Promise<boolean> {
        try {
            switch (step.action) {
                case 'click':
                    if (step.selector) {
                        await this.browser.click(step.selector);
                        return true;
                    }
                    return false;

                case 'fill':
                    if (step.selector && step.value) {
                        await this.browser.fill(step.selector, step.value);
                        return true;
                    }
                    return false;

                case 'type':
                    if (step.selector && step.value) {
                        await this.browser.type(step.selector, step.value);
                        return true;
                    }
                    return false;

                case 'press':
                    if (step.selector && step.value) {
                        await this.browser.press(step.selector, step.value);
                        return true;
                    }
                    return false;

                case 'scroll':
                    await this.sleep(500);
                    return true;

                case 'waitFor':
                    if (step.selector) {
                        await this.browser.waitForSelector(step.selector, 5000);
                        return true;
                    }
                    return false;

                case 'screenshot':
                    await this.browser.screenshot();
                    return true;

                default:
                    console.warn(`未知动作: ${step.action}`);
                    return false;
            }
        } catch (error: any) {
            console.error(`步骤执行错误 [${step.action}]:`, error.message);
            return false;
        }
    }

    /**
     * 执行多个任务（用于批量测试）
     */
    async executeBatch(
        url: string,
        tasks: { description: string; instruction: string }[]
    ): Promise<ExecutionResult[]> {
        console.log(`🚀 开始批量执行 ${tasks.length} 个任务`);

        const results: ExecutionResult[] = [];

        for (let i = 0; i < tasks.length; i++) {
            const task = tasks[i];
            console.log(`\n[${'═'.repeat(60)}]`);
            console.log(`📌 任务 ${i + 1}/${tasks.length}: ${task.description}`);
            console.log(`[${'═'.repeat(60)}]\n`);

            try {
                const result = await this.executeTask(url, task.instruction);
                results.push(result);

                // 清理执行状态
                this.executionHistory = [];
                this.failureRecords = [];
            } catch (error: any) {
                console.error(`任务 ${i + 1} 执行失败:`, error.message);
                results.push({
                    success: false,
                    taskDescription: task.description,
                    stepsExecuted: [],
                    totalSteps: 0,
                    finalURL: url,
                    summary: `执行失败: ${error.message}`,
                    failures: [],
                    duration: 0,
                    confidence: 0,
                });
            }
        }

        // 统计结果
        const successCount = results.filter((r) => r.success).length;
        const successRate = ((successCount / results.length) * 100).toFixed(1);
        console.log(`\n${'═'.repeat(60)}`);
        console.log(`📊 批量执行统计:`);
        console.log(`   总任务数: ${results.length}`);
        console.log(`   成功数: ${successCount}`);
        console.log(`   失败数: ${results.length - successCount}`);
        console.log(`   成功率: ${successRate}%`);
        console.log(`${'═'.repeat(60)}\n`);

        return results;
    }

    /**
     * 工具函数：睡眠
     */
    private sleep(ms: number): Promise<void> {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    /**
     * 获取执行摘要
     */
    getExecutionSummary(): {
        executionHistory: ActionStep[];
        failureRecords: FailureRecord[];
        statistics: {
            totalSteps: number;
            successfulSteps: number;
            failedSteps: number;
            recoveredFailures: number;
        };
    } {
        return {
            executionHistory: this.executionHistory,
            failureRecords: this.failureRecords,
            statistics: {
                totalSteps: this.executionHistory.length,
                successfulSteps: this.executionHistory.length - this.failureRecords.length,
                failedSteps: this.failureRecords.length,
                recoveredFailures: this.failureRecords.filter((f) => f.recovered).length,
            },
        };
    }
}
