import axios from 'axios';

interface VLMAnalysisResult {
    description: string;
    elements: ElementAnalysis[];
    interactiveAreas: InteractiveArea[];
    pageLayout: string;
    suggestions: string[];
}

interface ElementAnalysis {
    type: string;
    description: string;
    position?: { x: number; y: number };
    importance: 'high' | 'medium' | 'low';
}

interface InteractiveArea {
    type: string; // button, input, link, etc
    description: string;
    position?: { x: number; y: number };
    action: string; // 推荐的动作
}

/**
 * Qwen VLM视觉理解服务
 * 分析网页截图并提取视觉信息
 */
export class VLMService {
    private apiKey: string;
    private baseURL: string;
    private model: string;

    constructor(options: { apiKey?: string; baseURL?: string; model?: string } = {}) {
        this.apiKey = options.apiKey || process.env.QWEN_API_KEY || '';
        this.baseURL = options.baseURL || process.env.QWEN_BASE_URL || 'https://api.modelscope.cn/api/v1';
        this.model = options.model || 'qwen-vl-plus';

        if (!this.apiKey) {
            console.warn('警告: Qwen API密钥未设置');
        }
    }

    /**
     * 分析页面截图
     * @param screenshotBase64 截图的base64编码
     * @param prompt 分析提示词
     */
    async analyzeScreenshot(screenshotBase64: string, prompt: string = ''): Promise<VLMAnalysisResult> {
        const defaultPrompt = `分析这个网页截图，识别：
1. 页面的主要内容和布局
2. 所有可交互的元素（按钮、输入框、链接等）
3. 元素的位置和大小
4. 推荐的交互动作
5. 页面的主要目的

请返回JSON格式的结构化分析结果。`;

        try {
            const response = await axios.post(
                `${this.baseURL}/messages`,
                {
                    model: this.model,
                    messages: [
                        {
                            role: 'user',
                            content: [
                                {
                                    type: 'image',
                                    image: `data:image/jpeg;base64,${screenshotBase64}`,
                                },
                                {
                                    type: 'text',
                                    text: prompt || defaultPrompt,
                                },
                            ],
                        },
                    ],
                    max_tokens: 2000,
                },
                {
                    headers: {
                        Authorization: `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            const content = response.data.output.choices[0].message.content[0]?.text || '';
            return this.parseVLMResponse(content);
        } catch (error: any) {
            console.error('VLM分析错误:', error.message);
            // 降级方案：返回基础分析
            return this.getFallbackAnalysis();
        }
    }

    /**
     * 识别页面中的文本区域
     */
    async extractText(screenshotBase64: string): Promise<string[]> {
        const prompt = '提取这个网页截图中的所有可见文本，按照出现的顺序列出。';

        try {
            const response = await axios.post(
                `${this.baseURL}/messages`,
                {
                    model: this.model,
                    messages: [
                        {
                            role: 'user',
                            content: [
                                {
                                    type: 'image',
                                    image: `data:image/jpeg;base64,${screenshotBase64}`,
                                },
                                {
                                    type: 'text',
                                    text: prompt,
                                },
                            ],
                        },
                    ],
                    max_tokens: 1500,
                },
                {
                    headers: {
                        Authorization: `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            const content = response.data.output.choices[0].message.content[0]?.text || '';
            return content.split('\n').filter((line: string) => line.trim().length > 0);
        } catch (error: any) {
            console.error('文本提取错误:', error.message);
            return [];
        }
    }

    /**
     * 识别按钮和可点击元素
     */
    async identifyClickableElements(screenshotBase64: string): Promise<InteractiveArea[]> {
        const prompt = `分析这个网页截图，识别所有可点击的按钮、链接和可交互的元素。
对于每个元素，提供：
1. 元素类型（按钮、链接、输入框等）
2. 元素上的文本
3. 大致位置（相对于窗口）
4. 推荐的交互动作

返回JSON数组格式。`;

        try {
            const response = await axios.post(
                `${this.baseURL}/messages`,
                {
                    model: this.model,
                    messages: [
                        {
                            role: 'user',
                            content: [
                                {
                                    type: 'image',
                                    image: `data:image/jpeg;base64,${screenshotBase64}`,
                                },
                                {
                                    type: 'text',
                                    text: prompt,
                                },
                            ],
                        },
                    ],
                    max_tokens: 2000,
                },
                {
                    headers: {
                        Authorization: `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            const content = response.data.output.choices[0].message.content[0]?.text || '';
            return this.parseInteractiveElements(content);
        } catch (error: any) {
            console.error('元素识别错误:', error.message);
            return [];
        }
    }

    /**
     * 验证元素是否存在
     */
    async verifyElementPresence(screenshotBase64: string, description: string): Promise<boolean> {
        const prompt = `这个网页上是否存在以下描述的元素: "${description}"? 回答 "是" 或 "否"。`;

        try {
            const response = await axios.post(
                `${this.baseURL}/messages`,
                {
                    model: this.model,
                    messages: [
                        {
                            role: 'user',
                            content: [
                                {
                                    type: 'image',
                                    image: `data:image/jpeg;base64,${screenshotBase64}`,
                                },
                                {
                                    type: 'text',
                                    text: prompt,
                                },
                            ],
                        },
                    ],
                    max_tokens: 10,
                },
                {
                    headers: {
                        Authorization: `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            const content = response.data.output.choices[0].message.content[0]?.text || '';
            return content.includes('是') || content.includes('yes');
        } catch (error: any) {
            console.error('验证错误:', error.message);
            return false;
        }
    }

    /**
     * 理解页面的目的和内容
     */
    async understandPageContent(screenshotBase64: string, pageHTML?: string): Promise<string> {
        const prompt = `这个网页的主要内容和目的是什么？请用一句话总结。${pageHTML ? '我也提供了网页HTML供参考。' : ''
            }`;

        try {
            const messages: any[] = [
                {
                    role: 'user',
                    content: [
                        {
                            type: 'image',
                            image: `data:image/jpeg;base64,${screenshotBase64}`,
                        },
                        {
                            type: 'text',
                            text: prompt,
                        },
                    ],
                },
            ];

            if (pageHTML) {
                messages[0].content.push({
                    type: 'text',
                    text: `HTML内容: ${pageHTML.slice(0, 1000)}...`,
                });
            }

            const response = await axios.post(
                `${this.baseURL}/messages`,
                {
                    model: this.model,
                    messages,
                    max_tokens: 200,
                },
                {
                    headers: {
                        Authorization: `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            return response.data.output.choices[0].message.content[0]?.text || '无法理解页面';
        } catch (error: any) {
            console.error('内容理解错误:', error.message);
            return '无法理解页面';
        }
    }

    /**
     * 解析VLM响应
     */
    private parseVLMResponse(content: string): VLMAnalysisResult {
        try {
            // 尝试提取JSON
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const parsed = JSON.parse(jsonMatch[0]);
                return {
                    description: parsed.description || '页面分析',
                    elements: parsed.elements || [],
                    interactiveAreas: parsed.interactive_areas || parsed.interactiveAreas || [],
                    pageLayout: parsed.page_layout || parsed.pageLayout || '',
                    suggestions: parsed.suggestions || [],
                };
            }
        } catch (e) {
            // 继续使用文本解析
        }

        return {
            description: content.slice(0, 200),
            elements: [],
            interactiveAreas: [],
            pageLayout: '无法解析',
            suggestions: ['请检查VLM API连接'],
        };
    }

    /**
     * 解析可交互元素
     */
    private parseInteractiveElements(content: string): InteractiveArea[] {
        try {
            const jsonMatch = content.match(/\[[\s\S]*\]/);
            if (jsonMatch) {
                const parsed = JSON.parse(jsonMatch[0]);
                return parsed.map((item: any) => ({
                    type: item.type || 'element',
                    description: item.description || item.text || '',
                    position: item.position,
                    action: item.action || 'click',
                }));
            }
        } catch (e) {
            // 继续
        }

        return [];
    }

    /**
     * 降级方案：基础分析
     */
    private getFallbackAnalysis(): VLMAnalysisResult {
        return {
            description: '使用降级分析方案。提示：请配置Qwen API密钥以获得完整的视觉理解能力。',
            elements: [],
            interactiveAreas: [],
            pageLayout: '无法分析',
            suggestions: ['配置Qwen API密钥', '使用DOM结构代替'],
        };
    }
}

export type { VLMAnalysisResult, ElementAnalysis, InteractiveArea };
