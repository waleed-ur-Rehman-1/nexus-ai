from agents.file_agent import FileAgent
from agents.browser_agent import BrowserAgent
from agents.university_agent import UniversityAgent
from agents.system_agent import SystemAgent
from agents.email_agent import EmailAgent
from agents.calendar_agent import CalendarAgent   # <-- NEW

class TaskExecutor:
    def __init__(self):
        self.agents = {
            "file_agent": FileAgent(),
            "browser_agent": BrowserAgent(),
            "university_agent": UniversityAgent(),
            "system_agent": SystemAgent(),
            "email_agent": EmailAgent(),
            "calendar_agent": CalendarAgent()   # <-- NEW
        }

    def execute(self, agent_name: str, command: str) -> dict:
        agent = self.agents.get(agent_name)
        if not agent:
            return {"success": False, "message": f"Agent '{agent_name}' not found."}
        try:
            return agent.execute(command)
        except Exception as e:
            return {"success": False, "message": f"Agent execution failed: {str(e)}"}