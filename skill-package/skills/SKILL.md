---
name: "web-multimodal-agent"
description: "网页多模态Agent - 整合VLM视觉理解、LLM规划和浏览器自动化的完整解决方案"
version: "1.0.0"
author: "Your Name"
tags: ["web-automation", "multimodal", "vlm", "llm", "agent", "playwright"]
---

# 网页多模态Agent Skill

## 概述

这是一个强大的网页自动化skill，整合了：

- **VLM视觉理解** (Qwen): 分析网页截图，识别UI元素和布局
- **LLM规划** (DeepSeek): 基于用户指令生成精确的操作序列
- **浏览器自动化** (Playwright): 执行点击、输入、滚动等操作
- **Agent协调引擎**: 自适应执行，失败自动恢复

## 核心功能

### 1. 智能任务执行
```
用户指令 → VLM视觉分析 → LLM生成计划 → 浏览器执行 → 完成度评估
                ↑                                      ↓
                └──── 失败恢复和迭代 ────────────────┘
```

**工具**: `web_agent_execute_task`

**参数**:
- `url` (string, 必需): 目标网页URL
- `instruction` (string, 必需): 用户任务指令（自然语言）
- `headless` (boolean, 可选): 是否以无头模式运行（默认: true）

**示例指令**:
- "在搜索框输入'机器学习'，点击搜索按钮"
- "填写登录表单：用户名为admin，密码为123456"
- "找到价格最低的商品并加入购物车"
- "导航到关于我们页面，收集联系信息"

**返回结果**:
```json
{
  "success": true,
  "taskDescription": "用户指令",
  "stepsExecuted": [
    {
      "id": 1,
      "action": "click",
      "selector": "#search-button",
      "description": "已点击搜索按钮"
    }
  ],
  "totalSteps": 5,
  "finalURL": "https://...",
  "finalScreenshot": "base64编码的最终截图",
  "summary": "任务执行摘要",
  "failures": [],
  "duration": 5000,
  "confidence": 0.95
}
```

### 2. 批量任务执行
批量执行多个相关任务，获取统计数据。

**工具**: `web_agent_execute_batch`

**参数**:
- `url` (string): 目标网页URL
- `tasks` (array): 任务列表
  - `description` (string): 任务描述
  - `instruction` (string): 具体指令

**示例**:
```json
{
  "url": "https://example.com",
  "tasks": [
    {
      "description": "测试场景1: 简单搜索",
      "instruction": "搜索'测试'"
    },
    {
      "description": "测试场景2: 复杂表单",
      "instruction": "填写并提交注册表单"
    }
  ]
}
```

### 3. 执行摘要
获取最近执行的详细信息。

**工具**: `web_agent_get_summary`

**返回**:
```json
{
  "executionHistory": [执行的步骤列表],
  "failureRecords": [失败记录],
  "statistics": {
    "totalSteps": 10,
    "successfulSteps": 9,
    "failedSteps": 1,
    "recoveredFailures": 1
  }
}
```

## 视觉理解工具

### VLM 分析截图
使用Qwen VLM分析网页截图。

**工具**: `vlm_analyze_screenshot`

**参数**:
- `screenshot` (string): Base64编码的截图或data URL
- `prompt` (string, 可选): 自定义分析提示词

**默认分析内容**:
- 页面的主要内容和布局
- 所有可交互的元素
- 元素的位置和大小
- 推荐的交互动作

### VLM 提取文本
从截图中提取所有可见文本。

**工具**: `vlm_extract_text`

**返回**: 文本列表

### VLM 识别可点击元素
识别所有可以点击的按钮、链接等元素。

**工具**: `vlm_identify_clickable_elements`

**返回**: 可交互区域列表，包含位置和推荐动作

## LLM 规划工具

### 生成行动计划
基于页面状态和用户指令生成精确的操作序列。

**工具**: `llm_generate_plan`

**参数**:
- `pageContext` (object): 页面上下文
  - `url` (string): 当前URL
  - `title` (string): 页面标题
  - `interactiveElements` (array): 可交互元素列表
- `instruction` (string): 用户指令

**返回计划格式**:
```json
{
  "steps": [
    {
      "id": 1,
      "action": "click",
      "selector": "#button-id",
      "description": "点击搜索按钮",
      "expectedResult": "打开搜索页面",
      "fallback": {
        "action": "click",
        "selector": "text=Search"
      }
    }
  ],
  "reasoning": "推理过程",
  "confidence": 0.95,
  "alternatives": ["备选方案1", "备选方案2"]
}
```

**支持的动作类型**:
- `click`: 点击元素
- `fill`: 填充输入框（会清空）
- `type`: 逐字输入（用于特殊输入法）
- `press`: 按下键盘键
- `scroll`: 滚动页面
- `waitFor`: 等待元素出现
- `screenshot`: 获取截图

### 分析失败原因
当步骤失败时，分析原因并提供修复建议。

**工具**: `llm_analyze_failure`

**参数**:
- `instruction` (string): 原始指令
- `failedAction` (string): 失败的动作
- `error` (string): 错误信息

### 评估任务完成情况
判断用户指令是否已完成。

**工具**: `llm_evaluate_completion`

**参数**:
- `instruction` (string): 用户指令
- `pageUrl` (string, 可选): 当前页面URL
- `pageTitle` (string, 可选): 当前页面标题

**返回**:
```json
{
  "completed": true,
  "confidence": 0.95,
  "evidence": "判断依据",
  "nextSteps": []
}
```

## 浏览器控制工具

### 启动浏览器
```
工具: browser_launch
参数: { headless, browserType }
```

### 关闭浏览器
```
工具: browser_close
```

### 导航到URL
```
工具: browser_goto
参数: { url }
```

### 获取页面截图
```
工具: browser_screenshot
返回: { screenshot: "base64", size: number }
```

### 获取页面HTML
```
工具: browser_get_page_html
返回: { html, size }
```

## 使用示例

### 示例1: 简单搜索任务
```
使用: web_agent_execute_task
参数:
  url: "https://www.google.com"
  instruction: "搜索'OpenAI GPT-4'，查看第一个结果的标题"

结果: Agent会自动：
  1. 在搜索框输入'OpenAI GPT-4'
  2. 点击搜索按钮
  3. 等待结果加载
  4. 截图并提取第一个结果标题
  5. 返回执行结果
```

### 示例2: 表单填写和提交
```
使用: web_agent_execute_task
参数:
  url: "https://example.com/register"
  instruction: "完成注册表单：用户名=test123，邮箱=test@example.com，密码=Pass@123，然后提交"

结果: Agent会自动：
  1. 识别表单字段
  2. 填充用户名、邮箱、密码
  3. 点击提交按钮
  4. 等待提交完成
  5. 返回注册结果
```

### 示例3: 电商购物流程
```
使用: web_agent_execute_batch
参数:
  url: "https://shop.example.com"
  tasks: [
    {
      description: "搜索笔记本电脑",
      instruction: "在搜索框输入'笔记本'，按Enter搜索"
    },
    {
      description: "选择第一个商品",
      instruction: "点击第一个商品进入详情页"
    },
    {
      description: "加入购物车",
      instruction: "点击'加入购物车'按钮"
    }
  ]

结果: 获得所有任务的成功率和详细日志
```

## 配置说明

### 环境变量 (.env)

```bash
# DeepSeek LLM配置
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Qwen VLM配置
QWEN_API_KEY=sk-your-key
QWEN_MODEL=qwen-vl-plus
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# 浏览器配置
BROWSER_TYPE=chromium
HEADLESS=true
VIEWPORT_WIDTH=1280
VIEWPORT_HEIGHT=720

# Agent配置
MAX_ITERATIONS=10
TIMEOUT=30000
DEBUG=false
```

### 配置API密钥

#### DeepSeek
1. 访问 https://platform.deepseek.com
2. 注册账户并获取API密钥
3. 设置 `DEEPSEEK_API_KEY` 环境变量

#### Qwen (推荐使用ModelScope免费方案)
1. 访问 https://modelscope.cn
2. 注册账户（完全免费）
3. 获取API密钥
4. 设置 `QWEN_API_KEY` 环境变量

## 错误处理和恢复

### 自动恢复机制
- **选择器失败**: 尝试文本匹配、ARIA标签等替代方式
- **超时**: 自动重试或使用备选方案
- **页面变化**: 重新分析页面结构并调整选择器
- **网络错误**: 自动重试，带有指数退避

### 失败分类
系统自动记录失败类型：
1. **视觉识别失败**: VLM无法识别元素
2. **规划失败**: LLM生成的计划不可执行
3. **执行失败**: 浏览器执行出错
4. **完成度评估失败**: 无法确定任务是否完成

## 性能指标

- **平均响应时间**: 2-5秒/任务
- **成功率**: 85-95%（取决于网站复杂度）
- **错误恢复率**: 70%（自动修复失败）
- **支持网站**: 大多数现代网站

## 限制和注意事项

1. **JavaScript动态内容**: 支持，需要适当等待时间
2. **验证码**: 不支持自动解决（需要手动处理）
3. **登录认证**: 支持Cookie/Session存储
4. **PDF下载**: 支持但需要指定文件夹
5. **弹窗和模态框**: 自动处理

## 故障排除

### API连接错误
```
问题: "无法连接到Qwen/DeepSeek API"
解决:
  1. 检查网络连接
  2. 验证API密钥是否正确
  3. 检查API额度是否足够
  4. 查看API服务状态
```

### 选择器不匹配
```
问题: "无法找到元素"
解决:
  1. 使用VLM识别元素位置
  2. 尝试多种选择器方式（ID、Class、Text）
  3. 检查元素是否在iframe内
  4. 确认元素是否可见
```

### 超时问题
```
问题: "页面加载超时"
解决:
  1. 增加等待时间
  2. 检查网络速度
  3. 简化任务（分解为多个小任务）
  4. 检查网站是否正常运行
```

## 最佳实践

1. **指令清晰**: 使用具体的动作词，避免模糊表述
2. **分解复杂任务**: 将大任务分解为多个小任务
3. **添加验证**: 在关键步骤后验证结果
4. **记录失败**: 保存失败的截图用于调试
5. **监控成本**: 定期检查API使用量和成本

## API成本估算

### DeepSeek
- 输入: ¥0.00014/1K tokens
- 输出: ¥0.0006/1K tokens
- 平均任务成本: ¥0.0001-0.001

### Qwen (ModelScope免费方案)
- 完全免费（每月有额度限制，通常足够个人开发）

## 更多资源

- [Playwright官方文档](https://playwright.dev/)
- [DeepSeek API文档](https://platform.deepseek.com/docs)
- [Qwen视觉模型文档](https://help.aliyun.com/document_detail/2248186.html)
- [OpenClaw文档](https://github.com/your-repo/openclaw)

## 支持和反馈

如有问题或建议，请：
1. 查看日志文件
2. 在GitHub提Issue
3. 提交详细的错误报告（包括截图和指令）

---

**最后更新**: 2024年6月
**版本**: 1.0.0
**维护者**: Your Name
