# 示例说明

这个目录包含4个完整的使用示例，展示如何使用Web Multimodal Agent Skill。

## 示例列表

### 示例1: 简单搜索任务 (example1-simple-search.js)

**功能**: 在Google搜索框输入内容并搜索

**使用场景**:
- 简单的网页交互
- 基础的搜索功能测试
- VLM识别和LLM规划的演示

**运行方式**:
```bash
node dist/examples/example1-simple-search.js
```

**预期结果**:
```
✅ 成功在Google搜索"Playwright自动化"
执行时间: ~3秒
执行步骤: 3-4步
```

---

### 示例2: 表单填写和提交 (example2-form-filling.js)

**功能**: 填写并提交网页表单

**使用场景**:
- 表单字段识别
- 多字段填写
- 提交按钮点击
- 错误恢复演示

**运行方式**:
```bash
node dist/examples/example2-form-filling.js
```

**预期结果**:
```
✅ 成功填写并提交表单
执行步骤: 5-6步
包括错误恢复的演示
```

**注意**: 需要有可用的表单网页

---

### 示例3: 批量任务执行 (example3-batch-tasks.js)

**功能**: 执行多个相关任务并获取统计数据

**使用场景**:
- 完成验收要求的60+测试
- 获取成功率统计
- 性能对比分析

**运行方式**:
```bash
node dist/examples/example3-batch-tasks.js
```

**预期结果**:
```
总任务数: 3
成功数: 2-3
成功率: 66-100%
（具体结果取决于网站状态）
```

**特点**:
- 自动统计成功/失败
- 详细的执行报告
- 支持扩展到任意数量的任务

---

### 示例4: 低级工具使用 (example4-low-level-tools.js)

**功能**: 直接使用浏览器、VLM、LLM工具

**使用场景**:
- 自定义工作流
- 调试和测试
- 学习API使用

**运行方式**:
```bash
node dist/examples/example4-low-level-tools.js
```

**特点**:
- 展示BrowserAutomation API
- 展示VLMService API
- 展示LLMService API
- 适合开发和调试

---

## 运行示例的完整步骤

```bash
# 1. 进入项目目录
cd web-multimodal-agent-skill

# 2. 配置环境变量
cp .env.example .env
# 编辑.env，填入API密钥

# 3. 安装依赖
npm install

# 4. 编译
npm run build

# 5. 运行选择的示例
# 选项A: 运行所有示例
npm run examples

# 选项B: 运行特定示例
node dist/examples/example1-simple-search.js
node dist/examples/example2-form-filling.js
node dist/examples/example3-batch-tasks.js
node dist/examples/example4-low-level-tools.js
```

## 课题验证示例

### 适用于60+测试的示例配置

```javascript
// 生成60个测试用例的配置
const testSites = [
  'https://www.wikipedia.org',
  'https://www.github.com',
];

const tasksPerSite = 10; // 每个网站10个不同的任务
const repeatCount = 3;   // 每个任务重复3次

// 总测试数: 2 * 10 * 3 = 60个测试
```

### 错误分类统计示例

```typescript
// 在example3-batch-tasks.js基础上添加：

interface TestStatistics {
  totalTests: number;
  successfulTests: number;
  failedTests: number;
  
  // 错误分类
  visionErrors: number;        // VLM视觉识别失败
  planningErrors: number;      // LLM规划失败
  executionErrors: number;     // 浏览器执行失败
  evaluationErrors: number;    // 完成度评估失败
  
  // 恢复统计
  recoveredErrors: number;     // 自动恢复的错误
  
  // 性能指标
  averageExecutionTime: number; // 平均执行时间
  averageSteps: number;         // 平均步数
}
```

## 自定义示例

### 创建你自己的示例

```javascript
// new-example.js
import { MultimodalWebAgent } from '../dist/index.js';

async function myCustomExample() {
  const agent = new MultimodalWebAgent({
    deepseekApiKey: process.env.DEEPSEEK_API_KEY,
    qwenApiKey: process.env.QWEN_API_KEY,
  });

  const result = await agent.executeTask(
    'https://your-website.com',
    '你的具体指令'
  );

  console.log('结果:', result);
}

myCustomExample();
```

## 调试技巧

### 启用详细日志
```bash
DEBUG=true node dist/examples/example1-simple-search.js
```

### 保存截图用于分析
```javascript
// 在example中添加
if (result.finalScreenshot) {
  const fs = require('fs');
  fs.writeFileSync(
    'screenshot.png',
    Buffer.from(result.finalScreenshot, 'base64')
  );
}
```

### 检查执行历史
```javascript
const summary = agent.getExecutionSummary();
console.log('执行历史:', summary.executionHistory);
console.log('失败记录:', summary.failureRecords);
```

## 性能测试

### 基准测试（Benchmark）
```bash
# 运行3次相同任务，比较性能
npm run benchmark
```

### 并发测试
```javascript
// 同时执行多个Agent
const agents = [
  new MultimodalWebAgent(),
  new MultimodalWebAgent(),
  new MultimodalWebAgent(),
];

await Promise.all(
  agents.map(agent => 
    agent.executeTask(url, instruction)
  )
);
```

## 常见问题

**Q: 示例运行失败**
A: 检查：
1. 环境变量是否正确设置
2. 网络连接是否正常
3. API密钥是否有效
4. Node.js版本是否>=18

**Q: 浏览器超时**
A: 尝试：
1. 增加超时时间
2. 简化任务指令
3. 检查网络速度

**Q: API调用失败**
A: 检查：
1. API密钥是否正确
2. API额度是否足够
3. 服务是否在线

---

更多问题请查看 [README.md](../README.md) 和 [QUICK_START.md](../QUICK_START.md)
