#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { MultimodalWebAgent } from './agent/multimodal-web-agent.js';
import { toolsRegistry } from './tools-registry.js';
import { handleToolCall } from './tool-handlers.js';

// 创建MCP服务器
const server = new Server(
    {
        name: 'web-multimodal-agent-skill',
        version: '1.0.0',
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// Agent实例
const agent = new MultimodalWebAgent({
    deepseekApiKey: process.env.DEEPSEEK_API_KEY,
    qwenApiKey: process.env.QWEN_API_KEY,
});

// 注册工具列表处理器
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools: toolsRegistry };
});

// 注册工具调用处理器
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        const result = await handleToolCall(agent, name, args || {});

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify(result, null, 2),
                },
            ],
        };
    } catch (error: any) {
        return {
            content: [
                {
                    type: 'text',
                    text: `错误: ${error.message}`,
                },
            ],
            isError: true,
        };
    }
});

// 启动服务器
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('Web Multimodal Agent MCP Server v1.0 已启动');
    console.error(`已注册 ${toolsRegistry.length} 个工具`);
}

main().catch((error) => {
    console.error('服务器启动失败:', error);
    process.exit(1);
});
