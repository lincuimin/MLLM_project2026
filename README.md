# 多模态 Agent 网页自动化项目

本项目目标是实现一个基于视觉语言模型的浏览器自动化 Agent。系统接收自然语言任务，打开目标网页，观察带编号标注的网页截图和可操作元素列表，由 VLM 决策下一步动作，再通过 Playwright 执行点击、输入、滚动、按键等操作。

当前重构后的主线代码位于 `app/` 目录。旧的单文件脚本保留为早期实验 demo，后续开发建议优先围绕 `app/` 扩展。

## 项目结构

```text
MLLM_project/
  app/
    main.py
    agent.py
    browser_env.py
    vlm_client.py
    actions.py
    observation.py
    evaluation.py
    config.py
  tasks/
    douban.json
    github.json
    weather.json
    task_template.json
  outputs/
    screenshots/
    logs/
    evaluations/
  requirements.txt
  .env.example
  .gitignore
  README.md
```

## 核心文件说明

| 文件 | 作用 |
| --- | --- |
| `app/main.py` | 新版运行入口。读取 `tasks/*.json` 任务文件，创建 Agent 并启动浏览器自动化流程。后续 FastAPI 后端可以从这里继续扩展。 |
| `app/agent.py` | Agent 主循环。负责“观察页面 -> 调用 VLM -> 解析动作 -> 执行动作 -> 写入日志”的多轮执行流程，并在日志中记录每轮元素列表。 |
| `app/browser_env.py` | Playwright 浏览器环境封装。负责启动 Chromium、创建页面、打开网址和关闭浏览器。 |
| `app/vlm_client.py` | VLM 调用模块。负责组织提示词、编码截图、请求视觉语言模型，并解析模型返回的 JSON 动作。 |
| `app/actions.py` | 动作定义与执行模块。支持 `click`、`type`、`press`、`scroll`、`wait`、`finish`，优先通过 `element_id` 定位元素。 |
| `app/observation.py` | 页面观察模块。负责提取当前视口内的可操作元素、分配 `element_id`，并生成带彩色编号框的截图。 |
| `app/evaluation.py` | 评测记录模块。每次任务结束后自动把运行摘要追加到 `outputs/evaluations/runs.jsonl` 和 `runs.csv`。 |
| `app/config.py` | 新版配置模块。读取 `.env.example` 或系统环境变量，管理模型配置、浏览器配置和输出目录。 |
| `config.py` | 兼容旧 demo 的配置入口。新代码优先使用 `app/config.py`。 |
| `tasks/douban.json` | 豆瓣电影搜索示例任务。 |
| `tasks/github.json` | GitHub 仓库搜索示例任务。 |
| `tasks/weather.json` | 中国天气网城市天气查询示例任务。 |
| `tasks/task_template.json` | 新任务模板。复制后修改即可加入新的评测任务。 |
| `outputs/screenshots/` | 每次任务运行的截图输出目录。 |
| `outputs/logs/` | 每次任务运行的 JSON 日志输出目录。 |
| `outputs/evaluations/` | 自动评测结果输出目录。包含可累积的 JSONL 和 CSV 结果表。 |
| `requirements.txt` | Python 依赖列表。 |
| `.env.example` | 本地环境变量配置文件。填写自己的模型 API Key 后即可运行。 |
| `.gitignore` | 忽略本地密钥、缓存文件、运行截图和日志。 |

## 早期实验脚本

| 文件 | 作用 |
| --- | --- |
| `agent_join.py` | 早期多轮 VLM + Playwright 原型。 |
| `github查询.py` | 早期 GitHub 搜索任务 demo。 |
| `天气查询.py` | 早期天气查询任务 demo。 |
| `try1.py` | 早期豆瓣电影信息提取 demo。 |
| `try2.py` | 早期书店网页信息提取 demo。 |
| `try3.py` | 早期 Playwright 截图验证 demo。 |
| `多模态agent网页自动化开题报告.pdf` | 项目开题报告。 |

## 配置方式

先安装依赖：

```bash
pip install -r requirements.txt
playwright install
```

然后在 `.env.example` 中填入自己的模型配置：

```env
VLM_API_KEY=your_real_api_key
VLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
VLM_MODEL_NAME=qwen3.5-omni-plus-2026-03-15
VLM_REQUEST_TIMEOUT_SECONDS=40
AGENT_MAX_STEPS=8
BROWSER_HEADLESS=false
BROWSER_SLOW_MO_MS=400
BROWSER_CHANNEL=
BROWSER_CDP_URL=
BROWSER_CLOSE_PAGE_ON_FINISH=true
BROWSER_VIEWPORT_WIDTH=1280
BROWSER_VIEWPORT_HEIGHT=800
OBSERVATION_MAX_ELEMENTS=80
```

## 使用 Google Chrome

默认情况下，Playwright 会使用自带的 Chromium。如果只想改成系统安装的 Google Chrome，可以在 `.env.example` 中设置：

```env
BROWSER_CHANNEL=chrome
```

这种方式会启动一个受 Playwright 控制的 Chrome 实例，任务结束后仍然会关闭这个受控浏览器。

如果希望复用已经打开的 Chrome，让 Agent 每次只新开页面、任务结束后只关页面、不关闭整个浏览器，可以使用 Chrome DevTools Protocol：

```text
1. 先手动启动一个带远程调试端口的 Chrome。
2. 在 `.env.example` 中配置 BROWSER_CDP_URL。
3. 运行任务时，Agent 会连接这个已有 Chrome。
```

Windows 示例：

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\大三下\多模态大模型\MLLM_project\.chrome-profile"
```

然后配置：

```env
BROWSER_CDP_URL=http://127.0.0.1:9222
BROWSER_CLOSE_PAGE_ON_FINISH=true
```

建议使用单独的 `--user-data-dir`，不要直接复用日常浏览器账号资料。远程调试端口只应该绑定本机，不要暴露到公网。

## 运行新版 Agent

推荐从项目根目录运行：

```bash
python -m app.main --task-file tasks/douban.json
```

也可以运行其他任务：

```bash
python -m app.main --task-file tasks/github.json
python -m app.main --task-file tasks/weather.json
```

也可以直接输入自然语言命令。程序会先调用同一个 VLM API，把命令转换成
`tasks/task_template.json` 对应的任务 JSON，保存到 `outputs/generated_tasks/`，
然后继续调用原来的 Agent 流程：

```bash
python -m app.main --command "把 在https://movie.douban.com/explore搜索流浪地球"
```

如果命令里不写网址，任务生成器会让模型根据目标自己推断起始网站：

```bash
python -m app.main --command "搜索电影流浪地球"
python -m app.main --command "在 GitHub 页面上搜索开源项目 Qwen-VL"
```

运行结束后会生成：

```text
outputs/screenshots/<run_id>/step_01.png
outputs/screenshots/<run_id>/step_02.png
outputs/logs/<run_id>.json
outputs/reports/<run_id>.html
outputs/evaluations/runs.jsonl
outputs/evaluations/runs.csv
outputs/generated_tasks/<task_name>.json
```

日志中会记录任务状态、每一步截图、模型决策、执行结果和最终回答。HTML 报告会把截图序列、动作序列和错误分析放在同一个页面里，适合人工复盘。

## 任务日志和评测集

完整任务日志保存在：

```text
outputs/logs/<run_id>.json
```

它适合用来复盘单次任务，包含每一步：

```text
当前 URL
页面标题
编号截图路径
可操作元素列表
模型决策
执行动作
执行结果
动作后的 URL 和标题
```

评测集结果会自动追加到：

```text
outputs/evaluations/runs.jsonl
outputs/evaluations/runs.csv
```

`runs.jsonl` 适合后续用程序统计，`runs.csv` 适合直接用 Excel 查看。每条记录包含：

```text
任务名称
任务类型
难度
期望结果
成功标准
最终状态
是否成功
步数
耗时
最终 URL
最终回答
失败类型
错误分析
完整日志路径
HTML 轨迹报告路径
首张和末张截图路径
模型名称
浏览器模式
```

失败类型会被归为三类：

```text
识别失败：模型输出无法和当前页面元素稳定对应，例如 element_id 不存在、动作 JSON 不合法。
规划失败：模型没有在最大步数内完成任务，或反复执行无效动作、页面长时间停留不前。
执行失败：浏览器动作、页面跳转、Playwright 调用或模型 API 调用失败，例如 429、403、timeout、导航中断。
```

HTML 轨迹报告保存在：

```text
outputs/reports/<run_id>.html
```

报告包含：

```text
运行摘要
失败类型
错误分析
每一步截图
每一步模型决策 JSON
每一步实际执行动作和执行结果
动作前后的 URL 和标题
```

新增任务时，可以复制 `tasks/task_template.json`，然后修改：

```json
{
  "name": "example_task_name",
  "start_url": "https://example.com/",
  "instruction": "用一句话写清楚希望 Agent 完成什么任务，以及什么情况下算完成。",
  "max_steps": 8,
  "evaluation": {
    "suite": "basic_web_tasks",
    "task_type": "search",
    "difficulty": "easy",
    "expected_result": "描述理想情况下最终页面或最终回答应该是什么。",
    "success_criteria": [
      "页面达到目标状态",
      "模型输出 finish",
      "最终状态为 success"
    ]
  }
}
```

## 截图 + 页面元素观察

新版 Agent 不再只把普通网页截图交给模型，而是每轮同时提供两种信息：

```text
1. 带编号标注的截图：页面上的可操作元素会被彩色方框圈出，并显示 #1、#2、#3 等编号。
2. 可操作元素列表：每个元素包含 id、标签类型、文本、placeholder、位置、是否可输入等信息。
```

模型需要根据截图上的编号和元素列表输出动作，例如点击 `#3` 对应的按钮：

```json
{"action": "click", "element_id": 3}
```

每轮日志都会保存当时的 `elements`，如果任务失败，可以通过 `outputs/logs/<run_id>.json` 检查是模型选错了元素，还是元素提取没有覆盖目标控件。

## 模型输出格式

新版 Agent 要求模型使用 `element_id` 操作页面元素，避免直接输出坐标或模糊文本。动作格式如下：

```json
{"action": "click", "element_id": 1}
```

```json
{"action": "type", "element_id": 2, "text": "Qwen-VL"}
```

```json
{"action": "press", "key": "Enter"}
```

```json
{"action": "scroll", "direction": "down"}
```

```json
{"action": "finish", "answer": "已经进入搜索结果页面"}
```

## 后续开发建议

1. 优先完善 `observation.py`，让页面元素提取更稳定。
2. 在 `actions.py` 中补充更多动作校验和失败重试。
3. 基于 `agent.py` 的日志格式做评测统计。
4. Agent 稳定后，再接 FastAPI 后端和前端页面。
5. 本地完整跑通后，再准备服务器部署和模型部署。

## 安全提醒

真实 API Key 当前会从 `.env.example` 读取；如果这个项目会提交到公开仓库，建议不要提交包含真实密钥的 `.env.example`，或改回使用本地 `.env`。历史密钥如果曾经出现在代码中，建议到模型服务平台重置。
