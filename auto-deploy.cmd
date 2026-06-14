@echo off
REM Web Multimodal Agent Skill - 自动部署脚本（Windows）
REM 用于快速部署到OpenClaw

setlocal enabledelayedexpansion

echo.
echo 🚀 开始部署 Web Multimodal Agent Skill...
echo.

REM 检查Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js 未安装
    echo 请访问 https://nodejs.org/ 安装 Node.js 18+版本
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node -v') do set NODE_VERSION=%%i
echo ✅ Node.js %NODE_VERSION%

REM 获取OpenClaw配置路径
if exist "%APPDATA%\.openclaw" (
    set "OPENCLAW_CONFIG_PATH=%APPDATA%\.openclaw"
) else if exist "%USERPROFILE%\.openclaw" (
    set "OPENCLAW_CONFIG_PATH=%USERPROFILE%\.openclaw"
) else (
    set /p OPENCLAW_CONFIG_PATH=请输入OpenClaw配置目录路径: 
)

echo ✅ OpenClaw配置目录: %OPENCLAW_CONFIG_PATH%

REM 安装依赖
echo.
echo 📦 安装依赖...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖安装完成

REM 安装浏览器
echo.
echo 🌐 安装Playwright浏览器驱动...
call npm run install-browsers
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  浏览器驱动安装可能失败，但通常可以继续
)
echo ✅ 浏览器驱动安装完成

REM 构建项目
echo.
echo 🔨 编译TypeScript...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 编译失败
    pause
    exit /b 1
)
echo ✅ 编译完成

REM 配置OpenClaw
echo.
echo ⚙️  配置OpenClaw...

REM 创建MCP配置目录
if not exist "%OPENCLAW_CONFIG_PATH%\mcp\servers" (
    mkdir "%OPENCLAW_CONFIG_PATH%\mcp\servers"
)

REM 复制Skill定义
if not exist "%OPENCLAW_CONFIG_PATH%\skills" (
    mkdir "%OPENCLAW_CONFIG_PATH%\skills"
)
xcopy /E /I /Y "skill-package\skills\*" "%OPENCLAW_CONFIG_PATH%\skills\" >nul 2>&1

echo ✅ Skill定义已复制

REM 获取当前路径（Windows格式，需要转义反斜杠）
for /f "delims=" %%i in ('cd') do set "PROJECT_PATH=%%i"

REM 生成MCP配置
(
    echo {
    echo   "name": "web-multimodal-agent",
    echo   "command": "node",
    echo   "args": ["%PROJECT_PATH%\dist\mcp-server.js"],
    echo   "env": {
    echo     "DEEPSEEK_API_KEY": "",
    echo     "QWEN_API_KEY": "",
    echo     "NODE_ENV": "production"
    echo   }
    echo }
) > "%OPENCLAW_CONFIG_PATH%\mcp\servers\web-multimodal-agent.json"

echo ✅ OpenClaw配置已生成

REM 最终提示
echo.
echo ================================================
echo ✨ 部署完成！
echo ================================================
echo.
echo ⚠️  下一步：配置API密钥
echo.
echo 1. 编辑 .env 文件或 OpenClaw 配置：
echo    - DEEPSEEK_API_KEY: https://platform.deepseek.com
echo    - QWEN_API_KEY: https://modelscope.cn
echo.
echo 2. 重启 OpenClaw
echo.
echo 3. 在OpenClaw中使用web-multimodal-agent skill
echo.
echo 📚 详见: skill-package\skills\SKILL.md
echo.

echo ✅ 部署脚本执行完成

pause
