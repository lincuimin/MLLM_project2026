from __future__ import annotations

import json
import mimetypes
import sys
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.config import PROJECT_ROOT
    from app.main import run_command
else:
    from .config import PROJECT_ROOT
    from .main import run_command


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


class WebAgentHandler(BaseHTTPRequestHandler):
    server_version = "WebAgentHTTP/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return

        if parsed.path.startswith("/outputs/"):
            self._serve_output_file(parsed.path)
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run":
            self._send_json({"error": "Not found"}, status=404)
            return

        try:
            payload = self._read_json_body()
            command = str(payload.get("command") or "").strip()
            if not command:
                self._send_json({"error": "请输入任务请求"}, status=400)
                return

            summary = run_command(command)
            self._send_json(_summary_response(summary))
        except Exception as exc:
            self._send_json(
                {
                    "status": "failed",
                    "error": str(exc),
                },
                status=500,
            )

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format % args))

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        if not raw_body:
            return {}
        return json.loads(raw_body.decode("utf-8"))

    def _serve_output_file(self, request_path: str) -> None:
        relative_path = unquote(request_path).lstrip("/")
        file_path = (PROJECT_ROOT / relative_path).resolve()
        output_root = (PROJECT_ROOT / "outputs").resolve()

        if not _is_relative_to(file_path, output_root) or not file_path.is_file():
            self._send_json({"error": "File not found"}, status=404)
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, html: str, status: int = 200) -> None:
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _summary_response(summary: dict[str, Any]) -> dict[str, Any]:
    evaluation = summary.get("evaluation", {})
    record = evaluation.get("record", {})

    return {
        "run_id": summary.get("run_id"),
        "task_name": summary.get("task_name"),
        "status": summary.get("status"),
        "answer": summary.get("answer"),
        "final_url": summary.get("final_url"),
        "final_title": summary.get("final_title"),
        "elapsed_seconds": summary.get("elapsed_seconds"),
        "step_count": len(summary.get("steps", [])),
        "failure_type": record.get("failure_type") or "",
        "error_analysis": record.get("error_analysis") or "",
        "generated_task_file": _to_output_url(summary.get("generated_task_file")),
        "log_url": _to_output_url(summary.get("log_path")),
        "report_url": _to_output_url(record.get("report_path")),
        "jsonl_url": _to_output_url(evaluation.get("jsonl_path")),
        "csv_url": _to_output_url(evaluation.get("csv_path")),
    }


def _to_output_url(path_value: Any) -> str:
    if not path_value:
        return ""
    path = Path(str(path_value)).resolve()
    output_root = (PROJECT_ROOT / "outputs").resolve()
    if not _is_relative_to(path, output_root):
        return ""
    return "/" + path.relative_to(PROJECT_ROOT).as_posix()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the WebAgent browser UI.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind.")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), WebAgentHandler)
    print(f"WebAgent UI running at http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WebAgent 控制台</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --line: #d7dee8;
      --text: #172033;
      --muted: #667085;
      --accent: #1f6feb;
      --accent-dark: #1758bd;
      --danger-bg: #fde8e8;
      --danger: #9b1c1c;
      --success-bg: #def7ec;
      --success: #03543f;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      background: var(--bg);
      color: var(--text);
    }

    header {
      background: #172033;
      color: #fff;
      padding: 22px 28px;
    }

    header h1 {
      margin: 0;
      font-size: 24px;
      line-height: 1.25;
      letter-spacing: 0;
    }

    header p {
      margin: 8px 0 0;
      color: #cbd5e1;
      font-size: 14px;
    }

    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }

    .workspace {
      display: grid;
      grid-template-columns: minmax(320px, 430px) minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }

    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }

    h2 {
      margin: 0 0 14px;
      font-size: 18px;
      letter-spacing: 0;
    }

    label {
      display: block;
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 14px;
    }

    textarea {
      width: 100%;
      min-height: 132px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      color: var(--text);
      font: inherit;
      line-height: 1.5;
      outline: none;
    }

    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.12);
    }

    button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 40px;
      margin-top: 12px;
      padding: 0 16px;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      font: inherit;
      cursor: pointer;
    }

    button:hover { background: var(--accent-dark); }
    button:disabled { cursor: not-allowed; opacity: 0.65; }

    .examples {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }

    .example {
      min-height: 32px;
      margin: 0;
      padding: 0 10px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      font-size: 13px;
    }

    .example:hover { background: #f8fafc; }

    .status-line {
      min-height: 22px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 14px;
    }

    .result-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px 18px;
    }

    .field {
      min-width: 0;
    }

    .field.full {
      grid-column: 1 / -1;
    }

    .name {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 3px;
    }

    .value {
      word-break: break-word;
      line-height: 1.45;
    }

    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #e9eef7;
      font-size: 13px;
    }

    .badge.success {
      background: var(--success-bg);
      color: var(--success);
    }

    .badge.failed {
      background: var(--danger-bg);
      color: var(--danger);
    }

    .links {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }

    .links a {
      display: inline-flex;
      align-items: center;
      min-height: 36px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      color: var(--accent);
      text-decoration: none;
      background: #fff;
    }

    .links a.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }

    iframe {
      width: 100%;
      height: 720px;
      margin-top: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .placeholder {
      color: var(--muted);
      line-height: 1.6;
    }

    @media (max-width: 900px) {
      main { padding: 16px; }
      .workspace { grid-template-columns: 1fr; }
      .result-grid { grid-template-columns: 1fr; }
      iframe { height: 560px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>WebAgent 控制台</h1>
    <p>输入自然语言任务，后端会生成任务 JSON、调用浏览器自动化，并返回操作轨迹报告。</p>
  </header>
  <main>
    <div class="workspace">
      <section>
        <h2>提交任务</h2>
        <label for="command">自然语言请求</label>
        <textarea id="command" spellcheck="false">搜索电影流浪地球</textarea>
        <button id="runButton" type="button">▶ 运行任务</button>
        <div class="status-line" id="statusLine"></div>
        <div class="examples">
          <button class="example" type="button" data-command="搜索电影流浪地球">电影搜索</button>
          <button class="example" type="button" data-command="在 GitHub 页面上搜索开源项目 Qwen-VL">GitHub 搜索</button>
          <button class="example" type="button" data-command="查询湛江天气">天气查询</button>
        </div>
      </section>

      <section>
        <h2>运行结果</h2>
        <div id="result" class="placeholder">任务完成后，这里会显示状态、失败类型、错误分析和轨迹报告入口。</div>
      </section>
    </div>

    <iframe id="reportFrame" title="操作轨迹报告" hidden></iframe>
  </main>

  <script>
    const commandInput = document.getElementById('command');
    const runButton = document.getElementById('runButton');
    const statusLine = document.getElementById('statusLine');
    const result = document.getElementById('result');
    const reportFrame = document.getElementById('reportFrame');

    document.querySelectorAll('.example').forEach((button) => {
      button.addEventListener('click', () => {
        commandInput.value = button.dataset.command;
        commandInput.focus();
      });
    });

    runButton.addEventListener('click', async () => {
      const command = commandInput.value.trim();
      if (!command) {
        statusLine.textContent = '请输入任务请求。';
        return;
      }

      runButton.disabled = true;
      statusLine.textContent = '任务运行中：正在调用模型并控制浏览器，请等待。';
      result.className = 'placeholder';
      result.textContent = '运行中...';
      reportFrame.hidden = true;
      reportFrame.removeAttribute('src');

      try {
        const response = await fetch('/api/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || '任务运行失败');
        }
        renderResult(data);
        statusLine.textContent = '任务已结束。';
      } catch (error) {
        statusLine.textContent = '任务运行失败。';
        result.className = '';
        result.innerHTML = `<div class="result-grid"><div class="field full"><div class="name">错误</div><div class="value">${escapeHtml(error.message)}</div></div></div>`;
      } finally {
        runButton.disabled = false;
      }
    });

    function renderResult(data) {
      const statusClass = data.status === 'success' ? 'success' : 'failed';
      result.className = '';
      result.innerHTML = `
        <div class="result-grid">
          <div class="field"><div class="name">状态</div><div class="value"><span class="badge ${statusClass}">${escapeHtml(data.status || '')}</span></div></div>
          <div class="field"><div class="name">失败类型</div><div class="value">${escapeHtml(data.failure_type || '无')}</div></div>
          <div class="field"><div class="name">任务名称</div><div class="value">${escapeHtml(data.task_name || '')}</div></div>
          <div class="field"><div class="name">步数 / 耗时</div><div class="value">${escapeHtml(String(data.step_count || 0))} 步 / ${escapeHtml(String(data.elapsed_seconds || ''))} 秒</div></div>
          <div class="field full"><div class="name">最终 URL</div><div class="value">${escapeHtml(data.final_url || '')}</div></div>
          <div class="field full"><div class="name">最终回答</div><div class="value">${escapeHtml(data.answer || '')}</div></div>
          <div class="field full"><div class="name">错误分析</div><div class="value">${escapeHtml(data.error_analysis || '无')}</div></div>
        </div>
        <div class="links">
          ${data.report_url ? `<a class="primary" href="${escapeAttr(data.report_url)}" target="_blank" rel="noreferrer">打开操作轨迹</a>` : ''}
          ${data.log_url ? `<a href="${escapeAttr(data.log_url)}" target="_blank" rel="noreferrer">查看日志 JSON</a>` : ''}
          ${data.generated_task_file ? `<a href="${escapeAttr(data.generated_task_file)}" target="_blank" rel="noreferrer">查看任务 JSON</a>` : ''}
          ${data.csv_url ? `<a href="${escapeAttr(data.csv_url)}" target="_blank" rel="noreferrer">评测 CSV</a>` : ''}
        </div>
      `;

      if (data.report_url) {
        reportFrame.src = data.report_url;
        reportFrame.hidden = false;
      }
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function escapeAttr(value) {
      return escapeHtml(value).replaceAll('`', '&#096;');
    }
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
