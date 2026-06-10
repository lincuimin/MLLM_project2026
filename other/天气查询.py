import json
import re
import time
import base64
import requests
from playwright.sync_api import sync_playwright
from config import get_vlm_config

vlm_config = get_vlm_config(default_model="qwen3.5-omni-plus-2026-03-15")
API_KEY = vlm_config.api_key
API_URL = vlm_config.api_url
MODEL_NAME = vlm_config.model_name

def encode_image_to_base64(image_path):
    """将截图转换为 Base64 编码，以便通过网络发送"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def ask_vlm_for_action(task, screenshot_path):
    """中枢大脑：直接通过 HTTP 与 VLM 视觉大模型通信"""
    print(f"🧠 [中枢] 正在将截图 {screenshot_path} 编码并发送给 VLM...")
    
    base64_image = encode_image_to_base64(screenshot_path)
    
    prompt = f"""
    任务目标: {task}
    请仔细观察提供的网页截图。基于当前状态，告诉我下一步该做什么。
    你必须严格输出 JSON 格式字典，不要包含任何废话或 Markdown 标记。
    支持的动作格式:
    1. {{"action": "click", "target_name": "你要点击的按钮或链接的精确纯文本"}}
    2. {{"action": "type", "text": "要输入的具体文字"}}
    3. {{"action": "press", "key": "Enter"}}
    4. {{"action": "stop", "reason": "完成任务或遇到问题"}}
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 300,
        "temperature": 0.0 
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
        response.raise_for_status() 
        
        result_json = response.json()
        output = result_json['choices'][0]['message']['content']
        
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return {"action": "error", "reason": "JSON 语法错误"}
        else:
            print(f"⚠️ [中枢警告] 模型回答了，但没给 JSON:\n{output}")
            return {"action": "error", "reason": "模型未遵循 JSON 格式"}
            
    except Exception as e:
        print(f"❌ [API 通信错误]: {e}")
        return {"action": "error", "reason": str(e)}

def run_integration_test(playwright):
    print("🚀 [评测台] 启动物理引擎 (Playwright)...")
    browser = playwright.chromium.launch(headless=False, slow_mo=1000)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    
    # 【修改点 1】：更新测试任务为查询天气
    task_instruction = "在页面的搜索框中输入 '湛江'，然后按回车键查询天气。如果跳转到了天气详情结果页面，说明任务成功，请输出 stop 结束任务。"
    print(f"📋 [评测台] 当前任务: {task_instruction}")
    
    print("🌐 [评测台] 正在加载中国天气网...")
    try:
        # 【修改点 2】：更换目标 URL
        page.goto("https://www.weather.com.cn/", wait_until="load", timeout=30000)
    except Exception as e:
        print(f"⚠️ [网络警告] 加载异常: {e}")
    
    for step in range(1, 6):
        print(f"\n--- 🔄 第 {step} 轮交互 ---")
        page.wait_for_timeout(2000) 
        
        screenshot_path = f"state_step_{step}.png"
        page.screenshot(path=screenshot_path)
        print(f"📸 [评测台] 已获取当前页面状态 ({screenshot_path})。")
        
        action = ask_vlm_for_action(task_instruction, screenshot_path)
        action_type = action.get("action")
        
        if action_type == "stop":
            print(f"🏁 [评测台] 大脑宣布结束。理由: {action.get('reason')}")
            break
            
        elif action_type == "click":
            target = action.get('target_name')
            print(f"⚡ [执行器] 点击文本 '{target}'")
            try:
                page.locator(f"text='{target}'").first.click(timeout=5000)
                print("✅ [执行器] 成功！")
            except Exception:
                print(f"❌ [执行失败] 找不到 '{target}'。")
                break
                
        elif action_type == "type":
            text_to_type = action.get('text')
            print(f"⚡ [执行器] 在搜索框打字 '{text_to_type}'")
            try:
                # 【修改点 3】：增强定位器，适配天气网的输入框 (天气网经典搜索框 ID 为 txtZip)
                search_box = page.locator('#txtZip, input[type="text"][placeholder*="城市"], input[type="text"]').locator('visible=true').first
                
                search_box.click(timeout=5000)
                search_box.fill(text_to_type, timeout=5000)
                print("✅ [执行器] 成功！")
            except Exception as e:
                print(f"❌ [执行失败] 无法定位搜索框。具体报错: {e}")
                break
                
        elif action_type == "press":
            key_name = action.get('key')
            print(f"⚡ [执行器] 敲击键盘 '{key_name}'")
            try:
                page.keyboard.press(key_name)
                print("✅ [执行器] 成功！")
            except Exception:
                print(f"❌ [执行失败] 按键异常。")
                break
                
        else:
            print(f"⚠️ [执行器] 异常指令 {action_type}，终止。")
            break

    print("\n📊 [评测台] 测试结束，稍后关闭浏览器。")
    page.wait_for_timeout(4000) 
    context.close()
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_integration_test(playwright)
