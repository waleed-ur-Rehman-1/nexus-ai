import asyncio
import os
import re
from playwright.async_api import async_playwright
from agents.base_agent import BaseAgent
from dotenv import load_dotenv

load_dotenv()

class UniversityAgent(BaseAgent):
    name = "university_agent"

    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.logged_in = False

        self.username = os.getenv("UNI_USERNAME", "16330")
        self.password = os.getenv("UNI_PASSWORD", "waleedkhan123321!")
        self.login_url = os.getenv("UNI_LOGIN_URL", "https://cu.edu.pk/login.php")
        self.base_url = self.login_url.replace("login.php", "")
        self.mycourses_url = self.base_url + "mycourses.php"

    # ---------- Browser Management ----------
    async def _ensure_browser(self):
        if self.browser is None:
            print("🚀 Launching browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
            print("✅ Browser launched")
        else:
            try:
                await self.page.evaluate("1 + 1")
            except Exception:
                print("🔄 Page is dead, re‑launching browser...")
                await self._close_browser()
                self.browser = None
                self.page = None
                self.playwright = None
                await self._ensure_browser()

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
            self.logged_in = False

    async def _ensure_login(self) -> bool:
        await self._ensure_browser()
        current_url = self.page.url
        if "login.php" not in current_url:
            try:
                if await self.page.locator(".user-menu, #logout").count() > 0:
                    self.logged_in = True
                    return True
            except Exception:
                pass

        print("🔐 Logging in...")
        await self.page.goto(self.login_url, wait_until="networkidle")
        await self.page.fill("#user", self.username)
        print("✅ Filled registration number")

        password_selectors = ["#password", "input[name='password']", "input[type='password']"]
        filled = False
        for sel in password_selectors:
            if await self.page.locator(sel).count() > 0:
                await self.page.fill(sel, self.password)
                filled = True
                print(f"✅ Filled password using '{sel}'")
                break
        if not filled:
            print("❌ Password field not found")
            return False

        login_clicked = False
        login_selectors = ["input[name='login']", "input[value='Login']", "button[type='submit']"]
        for sel in login_selectors:
            if await self.page.locator(sel).count() > 0:
                await self.page.click(sel)
                login_clicked = True
                print(f"✅ Clicked login using '{sel}'")
                break
        if not login_clicked:
            print("⚠️ Login button not found, pressing Enter")
            await self.page.keyboard.press("Enter")

        await self.page.wait_for_load_state("networkidle", timeout=15000)
        await asyncio.sleep(2)

        if await self.page.locator(".user-menu, #logout, a:has-text('Sign out')").count() > 0:
            self.logged_in = True
            print("✅ Login successful")
            return True
        else:
            print("❌ Login failed")
            return False

    # ---------- 1. Courses (with session selection) ----------
    async def fetch_courses(self) -> dict:
        if not await self._ensure_login():
            return {"success": False, "message": "Login failed."}

        await self.page.goto(self.mycourses_url, wait_until="networkidle")

        # Select session
        session_select = await self.page.query_selector("select[name='selectSession']")
        if not session_select:
            return {"success": False, "message": "Session dropdown not found."}

        await session_select.select_option(value="2026 Fall")
        print("✅ Selected session: 2026 Fall")

        # Click "Show Data"
        show_button = await self.page.query_selector("input[name='sessionWise'][value='Show Data']")
        if show_button:
            await show_button.click()
            print("✅ Clicked Show Data")
        else:
            await self.page.click("input[type='submit']")
            print("⚠️ Clicked generic submit")

        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Parse table
        table = await self.page.query_selector("table.table-bordered.table-stripped")
        if not table:
            table = await self.page.query_selector("table.table-bordered")
        if not table:
            return {"success": False, "message": "Courses table not found after session selection."}

        rows = await table.query_selector_all("tbody tr")
        courses = []
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) >= 5:
                course_id_elem = await cols[0].query_selector("a")
                title_elem = await cols[1].query_selector("a")
                email_elem = await cols[2].query_selector("a")
                section_elem = await cols[3].text_content()
                teacher_elem = await cols[4].text_content()
                href = await course_id_elem.get_attribute("href") if course_id_elem else None
                title = await title_elem.text_content() if title_elem else None
                email = await email_elem.text_content() if email_elem else None
                section = section_elem.strip() if section_elem else None
                teacher = teacher_elem.strip() if teacher_elem else None
                params = {}
                if href:
                    qs = href.split('?', 1)[1] if '?' in href else ''
                    params = dict(re.findall(r'([^=&]+)=([^&]*)', qs))
                courses.append({
                    "course_id": params.get("courseid", ""),
                    "title": title,
                    "email": email,
                    "section": params.get("section", ""),
                    "teacher": teacher,
                    "teacher_id": params.get("teacherID", ""),
                    "session": params.get("sess", ""),
                    "cpsess": params.get("cpsess", "")
                })

        return {
            "success": True,
            "agent": self.name,
            "action": "fetch_courses",
            "count": len(courses),
            "courses": courses
        }

    # ---------- 2. Attendance (reads link from sidebar) ----------
    async def fetch_attendance(self) -> dict:
        if not await self._ensure_login():
            return {"success": False, "message": "Login failed."}

        # Navigate to mycourses to get the sidebar
        await self.page.goto(self.mycourses_url, wait_until="networkidle")

        # Find the "Attendance Record" link in the sidebar
        link = await self.page.query_selector("a:has-text('Attendance Record')")
        if not link:
            link = await self.page.query_selector("a[href*='attendance']")
        if not link:
            return {"success": False, "message": "Could not find Attendance Record link."}

        href = await link.get_attribute("href")
        if not href:
            return {"success": False, "message": "Attendance link has no href."}

        print(f"🔗 Found attendance link: {href}")

        # Navigate to that URL (relative, Playwright handles it)
        await self.page.goto(href, wait_until="networkidle")
        await asyncio.sleep(1)

        # Find the table
        table = await self.page.query_selector("table.table-bordered")
        if not table:
            table = await self.page.query_selector("table")
        if not table:
            return {"success": False, "message": "Attendance table not found."}

        rows = await table.query_selector_all("tbody tr")
        records = []
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) >= 5:
                course_id = await cols[0].text_content()
                course_title = await cols[1].text_content()
                total = await cols[2].text_content()
                presents = await cols[3].text_content()
                percent = await cols[4].text_content()
                records.append({
                    "course_id": course_id.strip(),
                    "course_title": course_title.strip(),
                    "total_classes": total.strip(),
                    "presents": presents.strip(),
                    "percentage": percent.strip()
                })

        note_elem = await self.page.query_selector(".alert-danger")
        note = await note_elem.text_content() if note_elem else ""

        return {
            "success": True,
            "agent": self.name,
            "action": "fetch_attendance",
            "count": len(records),
            "attendance": records,
            "note": note.strip()
        }

    # ---------- 3. Timetable (reads link from sidebar) ----------
    async def fetch_timetable(self) -> dict:
        if not await self._ensure_login():
            return {"success": False, "message": "Login failed."}
        await self.page.goto(self.mycourses_url, wait_until="networkidle")

        link = await self.page.query_selector("a:has-text('Time Table')")
        if not link:
            link = await self.page.query_selector("a[href*='timetable']")
        if not link:
            return {"success": False, "message": "Could not find Time Table link."}

        href = await link.get_attribute("href")
        if href:
            await self.page.goto(href, wait_until="networkidle")
            await asyncio.sleep(1)

        table = await self.page.query_selector("table.table-bordered")
        if not table:
            table = await self.page.query_selector("table")
        if not table:
            return {"success": False, "message": "Timetable table not found."}

        rows = await table.query_selector_all("tbody tr")
        timetable = []
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) >= 1:
                row_data = []
                for col in cols:
                    text = await col.text_content()
                    row_data.append(text.strip() if text else "")
                timetable.append(row_data)

        thead = await table.query_selector("thead")
        headers = []
        if thead:
            header_cells = await thead.query_selector_all("th")
            for cell in header_cells:
                text = await cell.text_content()
                headers.append(text.strip() if text else "")

        return {
            "success": True,
            "agent": self.name,
            "action": "fetch_timetable",
            "headers": headers,
            "rows": timetable
        }

    # ---------- 4. Internal Marks (reads link from sidebar) ----------
    async def fetch_internal_marks(self) -> dict:
        if not await self._ensure_login():
            return {"success": False, "message": "Login failed."}
        await self.page.goto(self.mycourses_url, wait_until="networkidle")

        link = await self.page.query_selector("a:has-text('Internal Marks')")
        if not link:
            link = await self.page.query_selector("a[href*='evalinternal']")
        if not link:
            return {"success": False, "message": "Could not find Internal Marks link."}

        href = await link.get_attribute("href")
        if href:
            await self.page.goto(href, wait_until="networkidle")
            await asyncio.sleep(1)

        table = await self.page.query_selector("table.table-bordered")
        if not table:
            return {"success": False, "message": "Internal marks table not found."}

        rows = await table.query_selector_all("tbody tr")
        marks = []
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) >= 6:
                course_id = await cols[0].text_content()
                title = await cols[1].text_content()
                deadline = await cols[2].text_content()
                submitted = await cols[3].text_content()
                total = await cols[4].text_content()
                status = await cols[5].text_content()
                marks.append({
                    "course_id": course_id.strip(),
                    "title": title.strip(),
                    "deadline": deadline.strip(),
                    "submitted": submitted.strip(),
                    "total_assignments": total.strip(),
                    "status": status.strip()
                })

        return {
            "success": True,
            "agent": self.name,
            "action": "fetch_internal_marks",
            "count": len(marks),
            "marks": marks
        }

    # ---------- 5. Notifications ----------
    async def fetch_notifications(self) -> dict:
        if not await self._ensure_login():
            return {"success": False, "message": "Login failed."}
        await self.page.goto(self.mycourses_url, wait_until="networkidle")

        sms_items = await self.page.query_selector_all(".dropdown.notifications-menu:first-child .menu a")
        sms_list = []
        for item in sms_items:
            href = await item.get_attribute("href")
            text = await item.text_content()
            small = await item.query_selector("small")
            date = await small.text_content() if small else ""
            sms_list.append({"text": text.strip(), "date": date.strip(), "link": href})

        bell_dropdown = await self.page.query_selector("li.dropdown.notifications-menu:has(i.fa-bell-o)")
        dicamp_list = []
        if bell_dropdown:
            bell_items = await bell_dropdown.query_selector_all(".menu a")
            for item in bell_items:
                href = await item.get_attribute("href")
                text = await item.text_content()
                dicamp_list.append({"text": text.strip(), "link": href})

        return {
            "success": True,
            "agent": self.name,
            "action": "fetch_notifications",
            "sms_notifications": sms_list,
            "dicamp_notifications": dicamp_list
        }

    # ---------- Helper: Login ----------
    async def login_university(self) -> dict:
        try:
            success = await self._ensure_login()
            return {"success": success, "agent": self.name, "action": "login", "message": "Login successful" if success else "Login failed."}
        except Exception as e:
            return {"success": False, "agent": self.name, "action": "login", "message": f"Login error: {str(e)}"}

    # ---------- Synchronous execute ----------
    def execute(self, command: str) -> dict:
        command_lower = command.lower()

        if "login" in command_lower and "university" in command_lower:
            return asyncio.run(self.login_university())

        elif "check" in command_lower and "course" in command_lower:
            return asyncio.run(self.fetch_courses())

        elif "check" in command_lower and "attendance" in command_lower:
            return asyncio.run(self.fetch_attendance())

        elif "check" in command_lower and "timetable" in command_lower:
            return asyncio.run(self.fetch_timetable())

        elif "check" in command_lower and "marks" in command_lower:
            return asyncio.run(self.fetch_internal_marks())

        elif "check" in command_lower and "notification" in command_lower:
            return asyncio.run(self.fetch_notifications())

        else:
            return {"success": False, "agent": self.name, "message": "University Agent: Command not understood."}