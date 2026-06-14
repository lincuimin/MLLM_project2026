#!/bin/bash

# Web Multimodal Agent Skill - 自动部署脚本（macOS/Linux）
# 用于快速部署到OpenClaw

set -e

echo "🚀 开始部署 Web Multimodal Agent Skill..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 未安装${NC}"
    echo "请访问 https://nodejs.org/ 安装 Node.js 18+版本"
    exit 1
fi

NODE_VERSION=$(node -v)
echo -e "${GREEN}✅ Node.js ${NODE_VERSION}${NC}"

# 获取OpenClaw配置路径
if [ -n "$OPENCLAW_PATH" ]; then
    OPENCLAW_CONFIG_PATH="$OPENCLAW_PATH"
else
    # 尝试自动检测
    if [ -d "$HOME/.openclaw" ]; then
        OPENCLAW_CONFIG_PATH="$HOME/.openclaw"
    elif [ -d "$HOME/AppData/Roaming/.openclaw" ]; then
        OPENCLAW_CONFIG_PATH="$HOME/AppData/Roaming/.openclaw"
    else
        read -p "请输入OpenClaw配置目录路径: " OPENCLAW_CONFIG_PATH
    fi
fi

echo -e "${GREEN}✅ OpenClaw配置目录: ${OPENCLAW_CONFIG_PATH}${NC}"

# 安装依赖
echo ""
echo "📦 安装依赖..."
npm install
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# 安装浏览器
echo ""
echo "🌐 安装Playwright浏览器驱动..."
npm run install-browsers
echo -e "${GREEN}✅ 浏览器驱动安装完成${NC}"

# 构建项目
echo ""
echo "🔨 编译TypeScript..."
npm run build
echo -e "${GREEN}✅ 编译完成${NC}"

# 配置OpenClaw
echo ""
echo "⚙️  配置OpenClaw..."

# 创建MCP配置目录
mkdir -p "${OPENCLAW_CONFIG_PATH}/mcp/servers"

# 复制Skill定义
mkdir -p "${OPENCLAW_CONFIG_PATH}/skills"
cp -r skill-package/skills/* "${OPENCLAW_CONFIG_PATH}/skills/" 2>/dev/null || true
echo -e "${GREEN}✅ Skill定义已复制${NC}"

# 生成MCP服务器配置
cat > "${OPENCLAW_CONFIG_PATH}/mcp/servers/web-multimodal-agent.json" << 'EOF'
{
  "name": "web-multimodal-agent",
  "command": "node",
  "args": ["${PROJECT_PATH}/dist/mcp-server.js"],
  "env": {
    "DEEPSEEK_API_KEY": "",
    "QWEN_API_KEY": "",
    "NODE_ENV": "production"
  }
}
EOF

# 获取当前项目路径
PROJECT_PATH=$(pwd)
# 更新配置中的项目路径
sed -i "s|\${PROJECT_PATH}|${PROJECT_PATH}|g" "${OPENCLAW_CONFIG_PATH}/mcp/servers/web-multimodal-agent.json"

echo -e "${GREEN}✅ OpenClaw配置已生成${NC}"

# 提示配置API密钥
echo ""
echo "📋 ================================================"
echo "✨ 部署完成！"
echo "================================================"
echo ""
echo -e "${YELLOW}⚠️  下一步：配置API密钥${NC}"
echo ""
echo "1. 编辑 .env 文件或 OpenClaw 配置："
echo "   - DEEPSEEK_API_KEY: https://platform.deepseek.com"
echo "   - QWEN_API_KEY: https://modelscope.cn"
echo ""
echo "2. 重启 OpenClaw"
echo ""
echo "3. 在OpenClaw中使用web-multimodal-agent skill"
echo ""
echo "📚 详见: skill-package/skills/SKILL.md"
echo ""

echo -e "${GREEN}✅ 部署脚本执行完成${NC}"
