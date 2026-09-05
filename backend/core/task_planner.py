import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Try to import the chosen LLM library
try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    HAS_OPENAI = bool(openai.api_key)
except ImportError:
    HAS_OPENAI = False

try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    HAS_GEMINI = bool(os.getenv("GEMINI_API_KEY"))
except ImportError:
    HAS_GEMINI = False


class TaskPlanner:
    def create_plan(self, command: str, agent: str) -> dict:
        """
        Generate a step‑by‑step plan with reasoning using an LLM.
        Falls back to mock reasoning if no LLM is available.
        """
        if HAS_OPENAI:
            return self._plan_with_openai(command, agent)
        elif HAS_GEMINI:
            return self._plan_with_gemini(command, agent)
        else:
            return self._mock_plan(command, agent)

    # ---------- Shared Prompt Builder ----------
    def _build_system_prompt(self, agent: str) -> str:
        """Build a fine‑tuned system prompt that lists all available actions."""
        return f"""
You are a task planning assistant for NEXUS AI.

The user gives a command. The system has selected the agent: **{agent}**.

Your job is to break the command into a sequence of atomic steps.
For each step, provide:
- "action": a short, machine‑readable action name (MUST be from the list below for this agent)
- "reason": a brief human‑readable explanation of why this step is needed.

Return ONLY valid JSON with a "steps" array. No extra text.

**Available actions by agent:**

- file_agent: scan_downloads, organize_downloads, arrange_folder, delete_folder, list_files
- browser_agent: open_page, search_youtube, play_youtube, click, fill, screenshot, close_browser
- email_agent: fetch_emails, send_email
- system_agent: shutdown, restart, lock
- university_agent: fetch_courses, fetch_attendance, fetch_timetable, fetch_internal_marks, fetch_notifications, login_university
- calendar_agent: get_events, add_event, delete_event

**Examples:**

User: "open youtube"
Agent: browser_agent
Response:
{{
  "steps": [
    {{"action": "open_page", "reason": "User wants to open YouTube."}}
  ]
}}

User: "play despacito"
Agent: browser_agent
Response:
{{
  "steps": [
    {{"action": "search_youtube", "reason": "Search for the song 'despacito'."}},
    {{"action": "play_youtube", "reason": "Click the first video result to start playing."}}
  ]
}}

User: "organize my downloads"
Agent: file_agent
Response:
{{
  "steps": [
    {{"action": "scan_downloads", "reason": "Identify all files in the Downloads folder."}},
    {{"action": "organize_downloads", "reason": "Move files into subfolders by file type (Documents, Images, etc.)."}}
  ]
}}

User: "check email"
Agent: email_agent
Response:
{{
  "steps": [
    {{"action": "fetch_emails", "reason": "Connect to the email server and retrieve recent messages."}}
  ]
}}

User: "shutdown my PC"
Agent: system_agent
Response:
{{
  "steps": [
    {{"action": "shutdown", "reason": "User requested to shut down the computer."}}
  ]
}}

User: "what's my schedule today?"
Agent: calendar_agent
Response:
{{
  "steps": [
    {{"action": "get_events", "reason": "Retrieve today's events from Google Calendar."}}
  ]
}}

User: "add a meeting at 3 PM tomorrow with John"
Agent: calendar_agent
Response:
{{
  "steps": [
    {{"action": "add_event", "reason": "User wants to add a meeting at 3 PM tomorrow with John."}}
  ]
}}

Now generate a plan for the user's command.
"""

    # ---------- OpenAI ----------
    def _plan_with_openai(self, command: str, agent: str) -> dict:
        try:
            client = openai.OpenAI()
            system_prompt = self._build_system_prompt(agent)
            user_prompt = f"Command: {command}\nAgent: {agent}"

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            content = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found")
            data = json.loads(json_match.group())
            if "steps" not in data:
                data["steps"] = [{"action": "execute", "reason": "LLM did not return steps."}]
            return {
                "command": command,
                "agent": agent,
                "steps": data["steps"]
            }
        except Exception as e:
            print(f"⚠️ OpenAI planning failed: {e}. Using mock.")
            return self._mock_plan(command, agent)

    # ---------- Google Gemini ----------
    def _plan_with_gemini(self, command: str, agent: str) -> dict:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            system_prompt = self._build_system_prompt(agent)
            full_prompt = f"{system_prompt}\n\nCommand: {command}\nAgent: {agent}\n\nOutput ONLY valid JSON:"
            response = model.generate_content(full_prompt)
            content = response.text.strip()
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found")
            data = json.loads(json_match.group())
            if "steps" not in data:
                data["steps"] = [{"action": "execute", "reason": "Gemini did not return steps."}]
            return {
                "command": command,
                "agent": agent,
                "steps": data["steps"]
            }
        except Exception as e:
            print(f"⚠️ Gemini planning failed: {e}. Using mock.")
            return self._mock_plan(command, agent)

    # ---------- Mock Fallback ----------
    def _mock_plan(self, command: str, agent: str) -> dict:
        steps = []
        if agent == "file_agent":
            if "organize" in command:
                steps = [
                    {"action": "scan_downloads", "reason": "User wants to organize Downloads folder."},
                    {"action": "organize_downloads", "reason": "Move files by type."}
                ]
            elif "scan" in command:
                steps = [{"action": "scan_downloads", "reason": "List files in Downloads."}]
            elif "arrange" in command:
                steps = [
                    {"action": "scan_folder", "reason": "Scan custom folder."},
                    {"action": "arrange_folder", "reason": "Organize by type."}
                ]
            else:
                steps = [{"action": "execute_file_command", "reason": "Generic file operation."}]
        elif agent == "browser_agent":
            if "youtube" in command or "play" in command:
                steps = [
                    {"action": "open_page", "reason": "Open YouTube."},
                    {"action": "search_youtube", "reason": f"Search for '{command}'"},
                    {"action": "play_youtube", "reason": "Play first video."}
                ]
            elif "open" in command:
                steps = [
                    {"action": "open_page", "reason": f"Open: {command}"}
                ]
            else:
                steps = [{"action": "browser_default", "reason": "Default browser action."}]
        elif agent == "email_agent":
            if "check" in command:
                steps = [{"action": "fetch_emails", "reason": "Retrieve emails."}]
            elif "send" in command:
                steps = [
                    {"action": "compose_email", "reason": "Prepare email."},
                    {"action": "send_email", "reason": "Deliver email."}
                ]
            else:
                steps = [{"action": "email_default", "reason": "Default email operation."}]
        elif agent == "system_agent":
            if "shutdown" in command:
                steps = [{"action": "shutdown", "reason": "Shut down PC."}]
            elif "restart" in command:
                steps = [{"action": "restart", "reason": "Restart PC."}]
            elif "lock" in command:
                steps = [{"action": "lock", "reason": "Lock workstation."}]
            else:
                steps = [{"action": "system_command", "reason": "System operation."}]
        elif agent == "university_agent":
            if "login" in command:
                steps = [{"action": "login_university", "reason": "Log into university portal."}]
            elif "attendance" in command:
                steps = [{"action": "fetch_attendance", "reason": "Fetch attendance records."}]
            elif "marks" in command:
                steps = [{"action": "fetch_internal_marks", "reason": "Fetch internal marks."}]
            elif "timetable" in command:
                steps = [{"action": "fetch_timetable", "reason": "Fetch timetable."}]
            elif "course" in command:
                steps = [{"action": "fetch_courses", "reason": "Fetch enrolled courses."}]
            elif "notification" in command:
                steps = [{"action": "fetch_notifications", "reason": "Fetch notifications."}]
            else:
                steps = [{"action": "university_command", "reason": "University operation."}]
        elif agent == "calendar_agent":
            if "add" in command and ("meeting" in command or "event" in command or "appointment" in command):
                steps = [
                    {"action": "add_event", "reason": "User wants to add an event to the calendar."}
                ]
            else:
                steps = [
                    {"action": "get_events", "reason": "Retrieve calendar events."}
                ]
        else:
            steps = [{"action": "execute_command", "reason": f"Execute via {agent}"}]

        return {
            "command": command,
            "agent": agent,
            "steps": steps
        }