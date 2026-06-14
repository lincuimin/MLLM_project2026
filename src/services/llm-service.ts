import axios from 'axios';

interface LLMPlan {
    steps: ActionStep[];
    reasoning: string;
    confidence: number;
    alternatives?: string[];
}

interface ActionStep {
    id: number;
    action: string; // 动作类型：click, fill, type, press, scroll等
    selector?: string; // CSS选择器
    value?: string; // 输入值
    description: string; // 动作描述
    expectedResult?: string; // 预期结果
    fallback?: ActionStep; // 备选方案
}

/**
 * DeepSeek LLM规划服务
 * 基于页面分析和用户指令生成浏览器操作序列
 */
export class LLMService {
    private apiKey: string;
    private baseURL: string;
    private model: string;

    constructor(options: { apiKey?: string; baseURL?: string; model?: string } = {}) {
        this.apiKey = options.apiKey || process.env.DEEPSEEK_API_KEY || '';
        this.baseURL = options.baseURL || process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com/v1';
        this.model = options.model || 'deepseek-chat';

        if (!this.apiKey) {
            console.warn('警告: DeepSeek API密钥未设置');
        }
    }

    /**
     * 生成行动计划
     * @param pageContext 页面上下文信息
     * @param userInstruction 用户指令
     * @param history 之前的操作历史
     */
    async generatePlan(
        pageContext: {
            url: string;
            title: string;
            structure?: any;
            interactiveElements?: any[];
            content?: string;
        },
        userInstruction: string,
        history: ActionStep[] = []
    ): Promise<LLMPlan> {
        const contextStr = this.buildContextPrompt(pageContext, userInstruction, history);

        try {
            const response = await axios.post(
                `${this.baseURL}/chat/completions`,
                {
                    model: this.model,
                    messages: [
                        {
                            role: 'system',
                            content: `你是一个网页自动化专家。你的任务是根据页面信息和用户指令，生成一系列精确的浏览器操作步骤。

要求：
1. 返回JSON格式的步骤序列
2. 每个步骤包含：action（动作类型）、selector（CSS选择器或文本）、value（输入值）、description（描述）
3. 动作类型包括：click、fill、type、press、scroll、waitFor、screenshot等
4. 提供reasoning（推理过程）和confidence（信心度0-1）
5. 对于不确定的步骤，提供fallback备选方案`,
                        },
                        {
                            role: 'user',
                            content: contextStr,
                        },
                    ],
                    temperature: 0.7,
                    max_tokens: 2000,
                },
                {
                    headers: {
                        Authorization: `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            const content = response.data.choices[0].message.content;
            return this.parsePlanResponse(content);
        } catch (error: any) {
            console.error('LLM规划错误:', error.message);
            return this.getFallbackPlan(userInstruction);
        }
    }

    /**
     * 分析失败原因并提供修复建议
     */
    async analyzeFailure(
        instruction: string,
        failedStep: ActionStep,
        pageContext: any,
        errorMessage: string
    ): Promise<{
        analysis: string;
        suggestions: ActionStep[];
        nextAction: ActionStep | null;
    }> {
        const prompt = `页面自动化出现失败。请分析原因并提供解决方案。

用户指令：${instruction}
失败步骤：${JSON.stringify(failedStep)}
错误信息：${errorMessage}
当前页面：${pageContext.url}

请返回JSON格式：{
  "analysis": "失败原因分析",
  "suggestions": [备选步骤数组],
  "nextAction": 推荐的下一步
}`;

        try {
            const response = await axios.post(
                `${this.baseURL}/chat/completions`,
                {
                    model: this.model,
                    messages: [
                        {
                            role: 'system',
                            content: '你是网页自动化调试专家。分析失败原因，提供具体的修复建议。',
                        },
                        {
                            role: 'user',
                            content: prompt,
                        },
                    ],
                    temperature: 0.5,
                    max_tokens: 1500,
                },
                {
                    headers: {
                        Authorization: `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            const content = response.data.choices[0].message.content;
            return this.parseFailureAnalysis(content);
        } catch (error: any) {
            console.error('失败分析错误:', error.message);
            return {
                analysis: '无法分析失败原因',
                suggestions: [],
                nextAction: null,
            };
        }
    }

    /**
     * 评估任务完成情况
     */
    async evaluateCompletion(
        instruction: string,
        pageState: {
            screenshot: string;
            url: string;
            content: string;
            title: string;
        },
        executedSteps: ActionStep[]
    ): Promise<{
        completed: boolean;
        confidence: number;
        evidence: string;
        nextSteps?: ActionStep[];
    }> {
        const prompt = `判断用户指令是否已完成。

用户指令：${instruction}
当前页面URL：${pageState.url}
当前页面标题：${pageState.title}
已执行步骤数：${executedSteps.length}

请返回JSON格式：{
  "completed": boolean,
  "confidence": 0-1,
  "evidence": "判断依据",
  "nextSteps": 如果未完成，建议的下一步
}`;

        try {
            const response = await axios.post(
                `${this.baseURL}/chat/completions`,
                {
                    model: this.model,
                    messages: [
                        {
                            role: 'system',
                            content: '你是任务评估专家。根据页面状态和已执行的步骤，判断用户指令是否已完成。',
                        },
                        {
                            role: 'user',
                            content: prompt,
                        },
                    ],
                    temperature: 0.3,
                    max_tokens: 1000,
                },
                {
                    headers: {
                        Authorization: `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            const content = response.data.choices[0].message.content;
            return this.parseEvaluationResponse(content);
        } catch (error: any) {
            console.error('完成度评估错误:', error.message);
            return {
                completed: false,
                confidence: 0,
                evidence: '无法评估',
            };
        }
    }

    /**
     * 构建上下文提示词
     */
    private buildContextPrompt(pageContext: any, userInstruction: string, history: ActionStep[]): string {
        let prompt = `请根据以下页面信息和用户指令，生成精确的操作步骤。

【用户指令】
${userInstruction}

【页面信息】
- URL: ${pageContext.url}
- 标题: ${pageContext.title}
- 可交互元素: ${pageContext.interactiveElements?.length || 0}个

【页面结构简述】
${pageContext.content?.slice(0, 500) || '无法获取'}

`;

        if (history.length > 0) {
            prompt += `【操作历史】\n`;
            history.slice(-5).forEach((step, i) => {
                prompt += `${i + 1}. ${step.action}: ${step.description}\n`;
            });
        }

        prompt += `

【要求】
1. 生成一个JSON对象，包含：
   - steps: 动作步骤数组
   - reasoning: 推理过程
   - confidence: 信心度（0-1）
   
2. 每个步骤包含：
   - action: 动作类型（click|fill|type|press|scroll|waitFor|screenshot）
   - selector: CSS选择器或元素文本（如果适用）
   - value: 输入值（如果适用）
   - description: 中文描述
   - expectedResult: 预期结果

3. 确保步骤清晰、可执行、有合理的等待和验证`;

        return prompt;
    }

    /**
     * 解析规划响应
     */
    private parsePlanResponse(content: string): LLMPlan {
        try {
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const parsed = JSON.parse(jsonMatch[0]);
                return {
                    steps: (parsed.steps || []).map((step: any, id: number) => ({
                        id,
                        action: step.action || 'click',
                        selector: step.selector,
                        value: step.value,
                        description: step.description || '',
                        expectedResult: step.expectedResult,
                        fallback: step.fallback,
                    })),
                    reasoning: parsed.reasoning || '无',
                    confidence: parsed.confidence || 0.5,
                    alternatives: parsed.alternatives,
                };
            }
        } catch (e) {
            console.error('JSON解析错误:', e);
        }

        // 降级方案
        return this.getFallbackPlan('');
    }

    /**
     * 解析失败分析响应
     */
    private parseFailureAnalysis(content: string): {
        analysis: string;
        suggestions: ActionStep[];
        nextAction: ActionStep | null;
    } {
        try {
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const parsed = JSON.parse(jsonMatch[0]);
                return {
                    analysis: parsed.analysis || '分析失败',
                    suggestions: parsed.suggestions || [],
                    nextAction: parsed.nextAction || null,
                };
            }
        } catch (e) {
            console.error('失败分析JSON解析错误:', e);
        }

        return {
            analysis: content.slice(0, 200),
            suggestions: [],
            nextAction: null,
        };
    }

    /**
     * 解析评估响应
     */
    private parseEvaluationResponse(content: string): {
        completed: boolean;
        confidence: number;
        evidence: string;
        nextSteps?: ActionStep[];
    } {
        try {
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const parsed = JSON.parse(jsonMatch[0]);
                return {
                    completed: parsed.completed || false,
                    confidence: parsed.confidence || 0,
                    evidence: parsed.evidence || '',
                    nextSteps: parsed.nextSteps,
                };
            }
        } catch (e) {
            console.error('评估JSON解析错误:', e);
        }

        return {
            completed: false,
            confidence: 0,
            evidence: '无法解析评估结果',
        };
    }

    /**
     * 降级方案：基础规划
     */
    private getFallbackPlan(instruction: string): LLMPlan {
        // 返回简单的步骤
        return {
            steps: [
                {
                    id: 1,
                    action: 'screenshot',
                    description: '获取当前页面截图以理解页面状态',
                },
                {
                    id: 2,
                    action: 'click',
                    description: `执行: ${instruction}`,
                },
            ],
            reasoning: '使用降级方案。提示：请配置DeepSeek API密钥以获得完整的规划能力。',
            confidence: 0.3,
            alternatives: ['考虑简化任务', '逐步执行每个操作'],
        };
    }
}

export type { LLMPlan, ActionStep };
