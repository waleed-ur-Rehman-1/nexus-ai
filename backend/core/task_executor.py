from agents.file_agent import FileAgent
from agents.browser_agent import BrowserAgent
from agents.university_agent import UniversityAgent
from agents.system_agent import SystemAgent
from agents.email_agent import EmailAgent

class TaskExecutor:
    def __init__(self):
        self.agents = {
            "file_agent": FileAgent(),
            "browser_agent": BrowserAgent(),
            "university_agent": UniversityAgent(),
            "system_agent": SystemAgent(),
            "email_agent": EmailAgent(),
        }

        # Try to add Calendar Agent; skip if it fails (e.g., missing credentials.json)
        try:
            from agents.calendar_agent import CalendarAgent
            self.agents["calendar_agent"] = CalendarAgent()
            print("✅ Calendar Agent initialized successfully.")
        except Exception as e:
            print(f"⚠️ Calendar Agent could not be initialized: {e}. Skipping.")
            # Optionally add a dummy agent that returns a friendly message
            # But we can just leave it out.

    def execute(self, agent_name: str, command: str) -> dict:
        agent = self.agents.get(agent_name)
        if not agent:
            return {"success": False, "message": f"Agent '{agent_name}' not found."}
        try:
            return agent.execute(command)
        except Exception as e:
            return {"success": False, "message": f"Agent execution failed: {str(e)}"}