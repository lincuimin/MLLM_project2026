from playwright.sync_api import sync_playwright
import time

def run(playwright):
    print("🚀 启动浏览器中 (注入反爬虫伪装)...")
    
    # 1. 启动参数伪装：抹除 webdriver 痕迹，并放慢手速
    browser = playwright.chromium.launch(
        headless=False, 
        slow_mo=1500,  # 模拟人类慢速操作
        args=['--disable-blink-features=AutomationControlled'] # 核心反爬参数
    )
    
    # 2. Context 伪装：设置真实的 Windows + Chrome User-Agent
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    page = context.new_page()
    
    # 3. 彻底隐藏 webdriver 属性 (JS 注入)
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    print("1. 正在打开豆瓣电影...")
    page.goto("https://movie.douban.com/")

    print("2. 正在定位搜索框并输入电影名称...")
    page.locator("#inp-query").fill("流浪地球2")

    print("3. 点击搜索按钮...")
    page.locator(".inp-btn input").click()

    print("4. 等待搜索结果加载，并点击第一个搜索结果...")
    page.wait_for_selector(".item-root a") 
    page.locator(".item-root a").first.click()

    print("5. 正在进入电影详情页，准备提取信息...")
    page.wait_for_selector('h1 span[property="v:itemreviewed"]')

    # 提取网页文本 (未来对应 Agent 获取页面状态并反馈给 LLM)
    title = page.locator('h1 span[property="v:itemreviewed"]').inner_text()
    rating = page.locator('strong[property="v:average"]').inner_text()
    summary = page.locator('span[property="v:summary"]').inner_text()

    print("\n================ 提取结果 ================")
    print(f"🎬 电影名称: {title}")
    print(f"⭐ 豆瓣评分: {rating}")
    print(f"📝 内容简介: {summary[:80]}...") # 截取前80个字符
    print("==========================================\n")

    print("6. 截取最终状态作为记录...")
    page.screenshot(path="result_screenshot.png")

    print("测试完毕，3秒后自动关闭浏览器...")
    time.sleep(3)
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)