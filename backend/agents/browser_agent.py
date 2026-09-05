import asyncio
from playwright.async_api import async_playwright
from agents.base_agent import BaseAgent

class BrowserAgent(BaseAgent):
    name = "browser_agent"

    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None

    async def _close_browser(self):
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
        finally:
            self.browser = None
            self.page = None
            self.playwright = None

    async def _ensure_browser(self):
        if self.page is not None:
            try:
                await self.page.evaluate("1 + 1")
                return
            except Exception:
                print("🔄 Page is dead, re‑launching...")
                await self._close_browser()

        if self.browser is None:
            print("🚀 Launching browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            self.page = await self.browser.new_page()
            print("✅ Browser launched")

    # ---------- Core ----------
    async def open_page(self, url: str, timeout: int = 60000) -> dict:
        try:
            await self._ensure_browser()
            if not url.startswith("http"):
                url = f"https://{url}"
            await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            title = await self.page.title()
            return {"success": True, "agent": self.name, "action": "open_page", "url": url, "title": title}
        except Exception as e:
            print(f"⚠️ Open failed: {e}. Retrying once...")
            await self._close_browser()
            await self._ensure_browser()
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                title = await self.page.title()
                return {"success": True, "agent": self.name, "action": "open_page", "url": url, "title": title}
            except Exception as e2:
                return {"success": False, "agent": self.name, "action": "open_page", "message": f"Failed: {str(e2)}"}

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
        await self._close_browser()
        return {"success": True, "agent": self.name, "action": "close", "message": "Browser closed."}

    # ---------- YouTube ----------
    async def search_youtube(self, query: str) -> dict:
        try:
            await self._ensure_browser()
            result = await self.open_page("https://www.youtube.com", timeout=60000)
            if not result["success"]:
                return result
            try:
                await self.page.click("button:has-text('Accept all'), button:has-text('Accept')", timeout=3000)
            except:
                pass
            search_input = await self.page.wait_for_selector("input#search, input[name='search_query']", timeout=10000)
            await search_input.fill(query)
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_selector("ytd-video-renderer, ytd-rich-item-renderer", timeout=10000)
            return {
                "success": True,
                "agent": self.name,
                "action": "search_youtube",
                "query": query,
                "message": f"Search results for '{query}' displayed."
            }
        except Exception as e:
            return {"success": False, "agent": self.name, "action": "search_youtube", "message": str(e)}

    async def play_youtube(self, query: str) -> dict:
        try:
            await self._ensure_browser()
            result = await self.open_page("https://www.youtube.com", timeout=60000)
            if not result["success"]:
                return result
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

    # ---------- Execute ----------
    def execute(self, command: str) -> dict:
        cmd = command.lower().strip()

        # 1. Play command
        if cmd.startswith("play "):
            query = command[5:].strip()
            if not query:
                return {"success": False, "agent": self.name, "message": "What would you like to play?"}
            return asyncio.run(self.play_youtube(query))

        # 2. Search command
        if cmd.startswith("search "):
            query = command[7:].strip()
            if not query:
                return {"success": False, "agent": self.name, "message": "What would you like to search?"}
            return asyncio.run(self.search_youtube(query))

        # 3. "open" handling – smart domain detection
        if cmd.startswith("open "):
            rest = command[5:].strip()
            # If rest contains a space, split into tokens to find a valid URL/domain
            tokens = rest.split()
            # Try to find a token that is a valid URL or domain
            for token in tokens:
                # If token looks like a domain (contains '.' and no spaces)
                if "." in token and not token.startswith("."):
                    return asyncio.run(self.open_page(token))
                # If token starts with http
                if token.startswith("http"):
                    return asyncio.run(self.open_page(token))
            # If no token looks like a domain, treat the whole rest as a play query
            if rest:
                return asyncio.run(self.play_youtube(rest))
            else:
                # Just open YouTube
                return asyncio.run(self.open_page("https://www.youtube.com"))

        # 4. Direct YouTube open (without "open" but containing "youtube")
        if "youtube" in cmd and "http" not in cmd:
            return asyncio.run(self.open_page("https://www.youtube.com"))

        # 5. Direct URL if it contains http
        if "http" in cmd:
            for word in command.split():
                if word.startswith("http"):
                    return asyncio.run(self.open_page(word))
            return {"success": False, "agent": self.name, "message": "No URL found."}

        # 6. Other commands
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