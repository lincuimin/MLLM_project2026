import { MultimodalWebAgent } from './agent/multimodal-web-agent.js';
import { BrowserAutomation } from './core/browser-automation.js';
import { VLMService } from './services/vlm-service.js';
import { LLMService } from './services/llm-service.js';

let browser: BrowserAutomation | null = null;
let vlm: VLMService | null = null;
let llm: LLMService | null = null;

export async function handleToolCall(agent: MultimodalWebAgent, name: string, args: any) {
    switch (name) {
        // ==================== Agent任务执行 ====================
        case 'web_agent_execute_task': {
            const { url, instruction, headless } = args;
            const result = await agent.executeTask(url, instruction, { headless });
            return result;
        }

        case 'web_agent_execute_batch': {
            const { url, tasks } = args;
            const results = await agent.executeBatch(url, tasks);
            return { results, successRate: `${((results.filter((r) => r.success).length / results.length) * 100).toFixed(1)}%` };
        }

        case 'web_agent_get_summary': {
            return agent.getExecutionSummary();
        }

        // ==================== 浏览器控制 ====================
        case 'browser_launch': {
            if (!browser) {
                browser = new BrowserAutomation();
            }
            const result = await browser.launch(args);
            return result;
        }

        case 'browser_close': {
            if (browser) {
                const result = await browser.close();
                browser = null;
                return result;
            }
            return { success: false, message: '浏览器未启动' };
        }

        case 'browser_goto': {
            if (!browser) throw new Error('浏览器未启动');
            return await browser.goto(args.url);
        }

        case 'browser_screenshot': {
            if (!browser) throw new Error('浏览器未启动');
            const base64 = await browser.screenshot();
            return { screenshot: `data:image/png;base64,${base64}`, size: base64.length };
        }

        case 'browser_get_page_html': {
            if (!browser) throw new Error('浏览器未启动');
            const html = await browser.getPageHTML();
            return { html, size: html.length };
        }

        // ==================== 视觉理解 ====================
        case 'vlm_analyze_screenshot': {
            if (!vlm) {
                vlm = new VLMService({ apiKey: process.env.QWEN_API_KEY });
            }
            const { screenshot, prompt } = args;
            // 移除data:image/...;base64, 前缀
            const base64 = screenshot.includes('base64,') ? screenshot.split('base64,')[1] : screenshot;
            return await vlm.analyzeScreenshot(base64, prompt);
        }

        case 'vlm_extract_text': {
            if (!vlm) {
                vlm = new VLMService({ apiKey: process.env.QWEN_API_KEY });
            }
            const { screenshot } = args;
            const base64 = screenshot.includes('base64,') ? screenshot.split('base64,')[1] : screenshot;
            return await vlm.extractText(base64);
        }

        case 'vlm_identify_clickable_elements': {
            if (!vlm) {
                vlm = new VLMService({ apiKey: process.env.QWEN_API_KEY });
            }
            const { screenshot } = args;
            const base64 = screenshot.includes('base64,') ? screenshot.split('base64,')[1] : screenshot;
            return await vlm.identifyClickableElements(base64);
        }

        // ==================== LLM规划 ====================
        case 'llm_generate_plan': {
            if (!llm) {
                llm = new LLMService({ apiKey: process.env.DEEPSEEK_API_KEY });
            }
            const { pageContext, instruction } = args;
            return await llm.generatePlan(pageContext || {}, instruction);
        }

        case 'llm_analyze_failure': {
            if (!llm) {
                llm = new LLMService({ apiKey: process.env.DEEPSEEK_API_KEY });
            }
            const { instruction, failedAction, error } = args;
            return await llm.analyzeFailure(
                instruction,
                { id: 0, action: failedAction, description: error },
                {},
                error
            );
        }

        case 'llm_evaluate_completion': {
            if (!llm) {
                llm = new LLMService({ apiKey: process.env.DEEPSEEK_API_KEY });
            }
            const { instruction, pageUrl, pageTitle } = args;
            return await llm.evaluateCompletion(instruction, {
                screenshot: '',
                url: pageUrl || 'unknown',
                content: '',
                title: pageTitle || '',
            }, []);
        }

        default:
            throw new Error(`未知工具: ${name}`);
    }
}
