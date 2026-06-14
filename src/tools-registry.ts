// MCP 工具注册表

export const toolsRegistry = [
    // ==================== Agent任务执行 ====================
    {
        name: 'web_agent_execute_task',
        description: '执行网页自动化任务。基于VLM视觉理解+LLM规划+浏览器自动化',
        inputSchema: {
            type: 'object',
            properties: {
                url: { type: 'string', description: '目标网页URL' },
                instruction: { type: 'string', description: '用户任务指令（中文）' },
                headless: { type: 'boolean', description: '是否以无头模式运行浏览器' },
            },
            required: ['url', 'instruction'],
        },
    },
    {
        name: 'web_agent_execute_batch',
        description: '批量执行多个网页自动化任务',
        inputSchema: {
            type: 'object',
            properties: {
                url: { type: 'string', description: '目标网页URL' },
                tasks: {
                    type: 'array',
                    items: {
                        type: 'object',
                        properties: {
                            description: { type: 'string' },
                            instruction: { type: 'string' },
                        },
                    },
                    description: '任务列表',
                },
            },
            required: ['url', 'tasks'],
        },
    },
    {
        name: 'web_agent_get_summary',
        description: '获取最近一次执行的摘要',
        inputSchema: {
            type: 'object',
            properties: {},
        },
    },

    // ==================== 浏览器控制 ====================
    {
        name: 'browser_launch',
        description: '启动浏览器',
        inputSchema: {
            type: 'object',
            properties: {
                headless: { type: 'boolean' },
                browserType: { type: 'string', enum: ['chromium', 'firefox', 'webkit'] },
            },
        },
    },
    {
        name: 'browser_close',
        description: '关闭浏览器',
        inputSchema: {
            type: 'object',
            properties: {},
        },
    },
    {
        name: 'browser_goto',
        description: '导航到指定URL',
        inputSchema: {
            type: 'object',
            properties: {
                url: { type: 'string' },
            },
            required: ['url'],
        },
    },
    {
        name: 'browser_screenshot',
        description: '获取页面截图',
        inputSchema: {
            type: 'object',
            properties: {},
        },
    },
    {
        name: 'browser_get_page_html',
        description: '获取页面HTML',
        inputSchema: {
            type: 'object',
            properties: {},
        },
    },

    // ==================== 视觉理解 ====================
    {
        name: 'vlm_analyze_screenshot',
        description: '用Qwen VLM分析网页截图',
        inputSchema: {
            type: 'object',
            properties: {
                screenshot: { type: 'string', description: 'Base64编码的截图' },
                prompt: { type: 'string', description: '分析提示词' },
            },
            required: ['screenshot'],
        },
    },
    {
        name: 'vlm_extract_text',
        description: '从截图中提取所有可见文本',
        inputSchema: {
            type: 'object',
            properties: {
                screenshot: { type: 'string' },
            },
            required: ['screenshot'],
        },
    },
    {
        name: 'vlm_identify_clickable_elements',
        description: '识别截图中的可点击元素',
        inputSchema: {
            type: 'object',
            properties: {
                screenshot: { type: 'string' },
            },
            required: ['screenshot'],
        },
    },

    // ==================== LLM规划 ====================
    {
        name: 'llm_generate_plan',
        description: '用DeepSeek LLM生成行动计划',
        inputSchema: {
            type: 'object',
            properties: {
                pageContext: {
                    type: 'object',
                    description: '页面上下文信息',
                },
                instruction: { type: 'string', description: '用户指令' },
            },
            required: ['instruction'],
        },
    },
    {
        name: 'llm_analyze_failure',
        description: '分析失败原因并提供修复建议',
        inputSchema: {
            type: 'object',
            properties: {
                instruction: { type: 'string' },
                failedAction: { type: 'string' },
                error: { type: 'string' },
            },
            required: ['instruction', 'failedAction', 'error'],
        },
    },
    {
        name: 'llm_evaluate_completion',
        description: '评估任务是否完成',
        inputSchema: {
            type: 'object',
            properties: {
                instruction: { type: 'string' },
                pageUrl: { type: 'string' },
                pageTitle: { type: 'string' },
            },
            required: ['instruction'],
        },
    },
];

export const toolCount = toolsRegistry.length;
