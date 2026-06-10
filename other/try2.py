from playwright.sync_api import sync_playwright
import time

def run(playwright):
    print("🚀 启动慢速视觉模式浏览器...")
    # slow_mo=1000 依然保留基础缓冲
    browser = playwright.chromium.launch(headless=False, slow_mo=1000) 
    context = browser.new_context()
    page = context.new_page()

    print("1. 正在打开模拟书店主页...")
    try:
        page.goto("http://books.toscrape.com/", wait_until="commit", timeout=15000)
    except Exception as e:
        print(f"⚠️ 捕获到加载超时，无视报错继续执行...")

    print("2. 等待商品列表渲染...")
    # 确保商品卡片（article.product_pod）已经加载出来
    page.wait_for_selector("article.product_pod", timeout=10000)

    # 找到页面上所有的书本卡片元素 (首页刚好20本)
    books = page.locator("article.product_pod").all()
    print(f"✅ 成功找到 {len(books)} 本书！准备开始逐一提取...\n")

    print("================ 提取结果 ================")
    
    # 遍历这 20 本书
    for index, book in enumerate(books):
        # 【视觉高光时刻】：模拟人类目光，将当前正在处理的这本书滚动到屏幕中央！
        book.scroll_into_view_if_needed()
        
        # 强制停顿 0.8 秒，让你能清楚地看到屏幕滚动和它的处理进度
        page.wait_for_timeout(800)

        # 从当前这本书的卡片内部提取信息
        # 1. 提取书名 (书名太长时页面会省略号，所以直接抓取 a 标签的 title 属性最准)
        title = book.locator("h3 a").get_attribute("title")
        
        # 2. 提取价格
        price = book.locator("p.price_color").inner_text()
        
        # 3. 提取库存状态 (消除多余的回车和空格)
        stock = book.locator("p.instock.availability").inner_text().strip()

        print(f"[{index + 1}/20] 📖: {title[:25]:<25} | 💰: {price} | 📦: {stock}")

    print("==========================================\n")

    print("3. 截取完整长图作为记录...")
    # full_page=True 会把整个网页从头到尾截成一张长图
    page.screenshot(path="20_books_full.png", full_page=True)

    print("测试完毕，5秒后自动关闭浏览器...")
    time.sleep(5)
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)