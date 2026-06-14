# 快速开始指南

## 5分钟快速部署

### 前置检查
- [ ] 已安装Node.js 18+
- [ ] 已安装Git
- [ ] 获取DeepSeek API密钥
- [ ] 获取Qwen API密钥

### 部署步骤

#### 第1步：获取项目
```bash
# 如果有Git
git clone https://github.com/your-repo/web-multimodal-agent-skill.git
cd web-multimodal-agent-skill

# 或者直接解压下载的zip文件
unzip web-multimodal-agent-skill.zip
cd web-multimodal-agent-skill
```

#### 第2步：配置API密钥
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的API密钥
# Windows: 用记事本或VS Code打开
# macOS/Linux: nano .env 或 vim .env
```

文件内容示例：
```env
DEEPSEEK_API_KEY=sk-your-actual-key-here
QWEN_API_KEY=sk-your-actual-key-here
```

#### 第3步：自动部署

**Windows用户**:
```bash
# 在命令行或PowerShell中运行
auto-deploy.cmd

# 按照脚本提示完成配置
# 脚本会自动：
#   - 安装npm依赖
#   - 安装Playwright浏览器
#   - 编译TypeScript
#   - 配置OpenClaw
#   - 拷贝Skill定义文件
```

**macOS/Linux用户**:
```bash
# 赋予执行权限
chmod +x auto-deploy.sh

# 运行脚本
./auto-deploy.sh

# 脚本会自动完成所有配置步骤
```

#### 第4步：重启OpenClaw
```bash
# 完全关闭OpenClaw
# 然后重新启动

# 在OpenClaw中应该能看到web-multimodal-agent skill已加载
```

#### 第5步：开始使用
```
在OpenClaw中发送指令：

用户: 访问Google并搜索"Python机器学习"

OpenClaw会自动使用web-multimodal-agent来完成这个任务
```

## 验证部署

### 方式1：检查文件是否存在
```bash
# 检查编译后的代码
ls dist/  # 应该有mcp-server.js, agent/, core/, services/等

# 检查Skill是否复制
ls ~/.openclaw/skills/  # 应该包含web-multimodal-agent相关文件
```

### 方式2：运行测试
```bash
# 编译
npm run build

# 运行基础测试
npm run test:basic

# 运行Agent测试
npm run test:agent
```

### 方式3：启动MCP服务器（调试）
```bash
npm start

# 应该看到类似输出：
# Web Multimodal Agent MCP Server v1.0 已启动
# 已注册 XX 个工具
```

## 常见问题

### Q: 部署脚本卡住了怎么办？
**A**: 
```bash
# 按Ctrl+C停止脚本

# 手动执行步骤：
npm install
npm run install-browsers  # 这一步可能需要5-10分钟
npm run build
```

### Q: 无法找到OpenClaw配置目录
**A**: 
- Windows: 通常在 `C:\Users\YourName\AppData\Roaming\.openclaw`
- macOS: `~/.openclaw`
- Linux: `~/.openclaw`

如果找不到，运行脚本时会提示输入路径。

### Q: API密钥配置不生效
**A**:
1. 检查.env文件是否保存成功
2. 确保密钥格式正确（不包含引号）
3. 重启OpenClaw
4. 检查API服务是否正常

### Q: npm install 失败
**A**:
```bash
# 清空npm缓存
npm cache clean --force

# 重新安装
npm install

# 如果还是失败，尝试用yarn
yarn install
```

## 验证示例

### 示例1：基础浏览器操作
```python
# 在OpenClaw中执行：
用户: 打开Google首页并获取页面标题

# Agent应该返回：
# ✅ 成功
# 页面标题: Google
```

### 示例2：搜索任务
```
用户: 在Google搜索"Artificial Intelligence"

期望结果:
✅ 成功
执行步骤: 3
- 点击搜索框
- 输入查询词
- 按Enter搜索
```

### 示例3：表单填写
```
用户: 在表单中输入用户名admin和密码123456，然后点击提交按钮

期望结果:
✅ 成功
执行步骤: 4
- 点击用户名输入框
- 输入admin
- 点击密码输入框
- 输入123456
- 点击提交按钮
```

## 获取API密钥

### DeepSeek
1. 访问: https://platform.deepseek.com/
2. 点击注册（支持邮箱、GitHub等方式）
3. 创建API密钥
4. 获得初始¥5余额用于测试
5. 成本非常低（¥0.00014/1K输入tokens）

### Qwen (推荐)
1. 访问: https://modelscope.cn/
2. 免费注册账户
3. 创建API密钥
4. **完全免费** 使用

## 下一步

1. **阅读完整文档**: [SKILL.md](skill-package/skills/SKILL.md)
2. **运行示例**: [examples/](examples/)
3. **查看源代码**: [src/](src/)
4. **阅读课题指南**: [COURSEWORK_GUIDE.md](COURSEWORK_GUIDE.md)

## 遇到问题？

1. 查看项目README：[README.md](README.md)
2. 查看Skill文档：[SKILL.md](skill-package/skills/SKILL.md)
3. 检查日志输出
4. 提交GitHub Issue

---

🎉 祝你使用愉快！
