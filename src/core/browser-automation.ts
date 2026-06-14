import { chromium, firefox, webkit, Browser, Page, BrowserContext } from 'playwright';

/**
 * Playwright浏览器自动化核心类
 * 提供浏览器操作、页面管理、内容提取等功能
 */
export class BrowserAutomation {
    private browser: Browser | null = null;
    private context: BrowserContext | null = null;
    private page: Page | null = null;
    private pages: Page[] = [];

    /**
     * 启动浏览器
     */
    async launch(options: {
        browserType?: 'chromium' | 'firefox' | 'webkit';
        headless?: boolean;
        viewport?: { width: number; height: number };
        slowMo?: number;
    } = {}) {
        const {
            browserType = 'chromium',
            headless = true,
            viewport = { width: 1280, height: 720 },
            slowMo = 0,
        } = options;

        const browserEngine = browserType === 'firefox' ? firefox : browserType === 'webkit' ? webkit : chromium;

        this.browser = await browserEngine.launch({
            headless,
            slowMo,
        });

        this.context = await this.browser.newContext({
            viewport,
        });

        this.page = await this.context.newPage();
        this.pages.push(this.page);

        return { success: true, message: `${browserType} 浏览器已启动` };
    }

    /**
     * 关闭浏览器
     */
    async close() {
        if (this.browser) {
            await this.browser.close();
            this.browser = null;
            this.context = null;
            this.page = null;
            this.pages = [];
        }
        return { success: true, message: '浏览器已关闭' };
    }

    /**
     * 导航到URL
     */
    async goto(url: string) {
        if (!this.page) throw new Error('浏览器未启动');
        await this.page.goto(url, { waitUntil: 'networkidle' });
        return { success: true, url, title: await this.page.title() };
    }

    /**
     * 获取页面截图
     */
    async screenshot(filename?: string): Promise<string> {
        if (!this.page) throw new Error('浏览器未启动');
        const buffer = await this.page.screenshot();
        return buffer.toString('base64');
    }

    /**
     * 获取页面完整HTML
     */
    async getPageHTML(): Promise<string> {
        if (!this.page) throw new Error('浏览器未启动');
        return await this.page.content();
    }

    /**
     * 获取所有可交互元素的信息
     */
    async getInteractiveElements() {
        if (!this.page) throw new Error('浏览器未启动');
        const elements = await this.page.evaluate(() => {
            const allElements = document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="link"]');
            return Array.from(allElements).map((el: any) => ({
                tag: el.tagName.toLowerCase(),
                id: el.id || '',
                class: el.className || '',
                text: el.innerText?.slice(0, 100) || el.textContent?.slice(0, 100) || '',
                placeholder: el.placeholder || '',
                type: el.type || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                role: el.getAttribute('role') || '',
                visible: el.offsetWidth > 0 && el.offsetHeight > 0,
            }));
        });
        return elements;
    }

    /**
     * 获取页面结构信息（用于VLM理解）
     */
    async getPageStructure() {
        if (!this.page) throw new Error('浏览器未启动');

        const structure = await this.page.evaluate(() => {
            const getElementInfo = (el: any, maxDepth = 3, depth = 0): any => {
                if (depth > maxDepth || !el) return null;

                const isVisible = el.offsetWidth > 0 && el.offsetHeight > 0;
                const rect = el.getBoundingClientRect();

                return {
                    tag: el.tagName.toLowerCase(),
                    id: el.id || undefined,
                    class: el.className || undefined,
                    text: el.innerText?.slice(0, 50) || el.textContent?.slice(0, 50) || undefined,
                    bbox: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                    },
                    visible: isVisible,
                    ariaLabel: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    children: depth < maxDepth
                        ? Array.from(el.children)
                            .map(child => getElementInfo(child as HTMLElement, maxDepth, depth + 1))
                            .filter(Boolean)
                        : undefined,
                };
            };

            return getElementInfo(document.body);
        });

        return structure;
    }

    /**
     * 点击元素
     */
    async click(selector: string) {
        if (!this.page) throw new Error('浏览器未启动');

        // 尝试多种选择器方式
        try {
            // 先尝试CSS选择器
            if (await this.page.$(selector)) {
                await this.page.click(selector);
                return { success: true, message: `已点击: ${selector}` };
            }
        } catch (e) {
            // 尝试文本匹配
            try {
                await this.page.click(`text="${selector}"`);
                return { success: true, message: `已点击文本: ${selector}` };
            } catch (e2) {
                throw new Error(`无法点击: ${selector}`);
            }
        }
    }

    /**
     * 填充输入框
     */
    async fill(selector: string, value: string) {
        if (!this.page) throw new Error('浏览器未启动');
        await this.page.fill(selector, value);
        return { success: true, message: `已填充: ${selector}` };
    }

    /**
     * 在输入框中输入文本（逐个字符）
     */
    async type(selector: string, text: string) {
        if (!this.page) throw new Error('浏览器未启动');
        await this.page.type(selector, text);
        return { success: true, message: `已输入: ${text}` };
    }

    /**
     * 按下键
     */
    async press(selector: string, key: string) {
        if (!this.page) throw new Error('浏览器未启动');
        await this.page.press(selector, key);
        return { success: true, message: `已按下: ${key}` };
    }

    /**
     * 滚动到元素
     */
    async scrollIntoView(selector: string) {
        if (!this.page) throw new Error('浏览器未启动');
        await this.page.locator(selector).scrollIntoViewIfNeeded();
        return { success: true, message: `已滚动到: ${selector}` };
    }

    /**
     * 等待元素出现
     */
    async waitForSelector(selector: string, timeout = 5000) {
        if (!this.page) throw new Error('浏览器未启动');
        await this.page.waitForSelector(selector, { timeout });
        return { success: true, message: `元素已出现: ${selector}` };
    }

    /**
     * 获取当前URL
     */
    async getCurrentURL(): Promise<string> {
        if (!this.page) throw new Error('浏览器未启动');
        return this.page.url();
    }

    /**
     * 获取页面标题
     */
    async getPageTitle(): Promise<string> {
        if (!this.page) throw new Error('浏览器未启动');
        return this.page.title();
    }

    /**
     * 检查元素是否可见
     */
    async isElementVisible(selector: string): Promise<boolean> {
        if (!this.page) throw new Error('浏览器未启动');
        return (await this.page.$(selector)) !== null;
    }

    /**
     * 执行JavaScript代码
     */
    async executeScript(script: string, args?: any[]) {
        if (!this.page) throw new Error('浏览器未启动');
        return await this.page.evaluate(
            ({ script, args }) => eval(`(${script})`)(args),
            { script, args }
        );
    }

    /**
     * 获取表单数据
     */
    async getFormData() {
        if (!this.page) throw new Error('浏览器未启动');

        const formData = await this.page.evaluate(() => {
            const data: any = {};
            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach((input: any) => {
                const name = input.name || input.id;
                if (name) {
                    data[name] = input.value;
                }
            });
            return data;
        });

        return formData;
    }

    /**
     * 等待导航完成
     */
    async waitForNavigation() {
        if (!this.page) throw new Error('浏览器未启动');
        await this.page.waitForLoadState('networkidle');
        return { success: true, url: this.page.url() };
    }
}
