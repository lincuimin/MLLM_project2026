from playwright.sync_api import sync_playwright
import os

def run(playwright):
    print("🚀 1. 启动纯净后台浏览器 (Headless模式)...")
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    print("🌐 2. 正在访问百度首页 (确保网络秒连)...")
    page.goto("https://www.baidu.com")

    # 获取当前运行目录的绝对路径，确保知道图存在哪了
    save_path = os.path.abspath("test_baidu.png")
    
    print(f"📸 3. 正在执行截图操作...")
    page.screenshot(path=save_path)
    
    print("\n================ 验证成功 ================")
    print("✅ 截图已成功保存！")
    print(f"📁 它的绝对路径是: {save_path}")
    print("==========================================")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)