from __future__ import annotations

from typing import Any

from playwright.sync_api import sync_playwright

from .config import Settings


class BrowserEnv:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.playwright: Any = None
        self.browser: Any = None
        self.context: Any = None
        self.page: Any = None
        self.connected_to_existing_browser = False

    def __enter__(self) -> "BrowserEnv":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def start(self) -> None:
        self.playwright = sync_playwright().start()

        if self.settings.browser_cdp_url:
            self.browser = self.playwright.chromium.connect_over_cdp(
                self.settings.browser_cdp_url
            )
            self.connected_to_existing_browser = True
            self.context = self.browser.contexts[0] if self.browser.contexts else None
        else:
            launch_options = {
                "headless": self.settings.browser_headless,
                "slow_mo": self.settings.browser_slow_mo_ms,
            }
            if self.settings.browser_channel:
                launch_options["channel"] = self.settings.browser_channel

            self.browser = self.playwright.chromium.launch(**launch_options)
            self.context = None

        if self.context is None:
            self.context = self.browser.new_context(**self._context_options())

        self.page = self.context.new_page()
        self.page.set_viewport_size(
            {
                "width": self.settings.viewport_width,
                "height": self.settings.viewport_height,
            }
        )

    def _context_options(self) -> dict[str, Any]:
        return {
            "viewport": {
                "width": self.settings.viewport_width,
                "height": self.settings.viewport_height,
            },
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

    def goto(self, url: str, timeout_ms: int = 40000) -> None:
        self.page.goto(url, wait_until="load", timeout=timeout_ms)

    def close(self) -> None:
        if self.page is not None and self.settings.browser_close_page_on_finish:
            self.page.close()

        if self.connected_to_existing_browser:
            if self.playwright is not None:
                self.playwright.stop()
            return

        if self.context is not None:
            self.context.close()
        if self.browser is not None:
            self.browser.close()
        if self.playwright is not None:
            self.playwright.stop()
