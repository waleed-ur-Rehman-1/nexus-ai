import asyncio
import os
import subprocess
import sys
from playwright.async_api import async_playwright
from agents.base_agent import BaseAgent

class BrowserAgent(BaseAgent):
    name = "browser_agent"

    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self._ensure_browser_installed()

    def _ensure_browser_installed(self):
        """Install Playwright browser if missing (works on Render)."""
        browser_path = "/opt/render/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"
        if os.path.exists(browser_path):
            print("✅ Browser already exists.")
            return
        print("⚠️ Installing Playwright browser...")
        try:
            # Try with subprocess
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Playwright installed successfully.")
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            # Fallback: try without capture output
            try:
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            except Exception as e2:
                print(f"❌ Second attempt failed: {e2}")

    # ---------- Rest of your agent code ----------
    async def _ensure_browser(self):
        if self.browser is None:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                self.page = await self.browser.new_page()
                print("✅ Browser launched successfully")
            except Exception as e:
                print(f"❌ Browser launch failed: {e}")
                raise

    async def open_page(self, url: str) -> dict:
        try:
            await self._ensure_browser()
            await self.page.goto(url, wait_until="domcontentloaded")
            title = await self.page.title()
            return {
                "success": True,
                "agent": self.name,
                "action": "open_page",
                "url": url,
                "title": title
            }
        except Exception as e:
            return {
                "success": False,
                "agent": self.name,
                "action": "open_page",
                "message": f"Failed to open page: {str(e)}"
            }

    async def click(self, selector: str) -> dict:
        try:
            await self._ensure_browser()
            await self.page.click(selector)
            return {"success": True, "agent": self.name, "action": "click", "selector": selector}
        except Exception as e:
            return {"success": False, "agent": self.name, "action": "click", "message": str(e)}

    async def fill(self, selector: str, text: str) -> dict:
        try:
            await self._ensure_browser()
            await self.page.fill(selector, text)
            return {"success": True, "agent": self.name, "action": "fill", "selector": selector, "text": text}
        except Exception as e:
            return {"success": False, "agent": self.name, "action": "fill", "message": str(e)}

    async def screenshot(self, path: str = "screenshot.png") -> dict:
        try:
            await self._ensure_browser()
            await self.page.screenshot(path=path)
            return {"success": True, "agent": self.name, "action": "screenshot", "path": path}
        except Exception as e:
            return {"success": False, "agent": self.name, "action": "screenshot", "message": str(e)}

    async def close(self) -> dict:
        try:
            if self.browser:
                await self.browser.close()
                await self.playwright.stop()
                self.browser = self.page = self.playwright = None
            return {"success": True, "agent": self.name, "action": "close", "message": "Browser closed."}
        except Exception as e:
            return {"success": False, "agent": self.name, "action": "close", "message": str(e)}

    async def play_youtube(self, query: str) -> dict:
        try:
            await self._ensure_browser()
            await self.page.goto("https://www.youtube.com", wait_until="domcontentloaded")
            try:
                await self.page.click("button:has-text('Accept all'), button:has-text('Accept')", timeout=3000)
            except:
                pass
            search_input = await self.page.wait_for_selector("input#search, input[name='search_query']", timeout=10000)
            await search_input.fill(query)
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_selector("ytd-video-renderer, ytd-rich-item-renderer", state="attached", timeout=15000)
            video = await self.page.query_selector("ytd-video-renderer a#thumbnail, ytd-rich-item-renderer a#thumbnail")
            if not video:
                video = await self.page.query_selector("a#thumbnail")
            if not video:
                return {"success": False, "agent": self.name, "message": "No video thumbnail found."}
            await video.click()
            await self.page.wait_for_load_state("networkidle")
            title_elem = await self.page.query_selector("h1.title yt-formatted-string, h1>yt-formatted-string")
            title = await title_elem.text_content() if title_elem else query
            return {
                "success": True,
                "agent": self.name,
                "action": "play_youtube",
                "query": query,
                "video_title": title,
                "message": f"Now playing '{title}'."
            }
        except Exception as e:
            return {"success": False, "agent": self.name, "action": "play_youtube", "message": str(e)}

    def execute(self, command: str) -> dict:
        cmd = command.lower().strip()

        if cmd.startswith("play "):
            query = command[5:].strip()
            if not query:
                return {"success": False, "agent": self.name, "message": "What would you like to play?"}
            return asyncio.run(self.play_youtube(query))

        if "open" in cmd and "youtube" in cmd and "http" not in cmd:
            return asyncio.run(self.open_page("https://www.youtube.com"))

        if "open" in cmd and "http" in cmd:
            for word in command.split():
                if word.startswith("http"):
                    return asyncio.run(self.open_page(word))
            return {"success": False, "agent": self.name, "message": "No URL found."}

        if cmd.startswith("open "):
            query = command[5:].strip()
            if query and query not in ["youtube", "the browser", "browser"]:
                return asyncio.run(self.play_youtube(query))
            else:
                return asyncio.run(self.open_page("https://www.youtube.com"))

        if "click" in cmd:
            selector = command.split("click", 1)[1].strip()
            return asyncio.run(self.click(selector))
        if "fill" in cmd:
            parts = command.split("fill", 1)[1].strip().split(" ", 1)
            if len(parts) == 2:
                return asyncio.run(self.fill(parts[0], parts[1]))
            return {"success": False, "agent": self.name, "message": "Use: fill <selector> <text>"}
        if "screenshot" in cmd:
            return asyncio.run(self.screenshot())
        if "close" in cmd and "browser" in cmd:
            return asyncio.run(self.close())

        return {"success": False, "agent": self.name, "message": "Command not understood."}