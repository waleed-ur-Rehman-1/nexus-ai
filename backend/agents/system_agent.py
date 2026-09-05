import os
import platform
import subprocess
from agents.base_agent import BaseAgent

class SystemAgent(BaseAgent):
    name = "system_agent"

    def execute(self, command: str) -> dict:
        command_lower = command.lower()

        if "shutdown" in command_lower:
            return self.shutdown()
        elif "restart" in command_lower:
            return self.restart()
        elif "lock" in command_lower:
            return self.lock()
        else:
            return {"success": False, "agent": self.name, "message": "System Agent: Command not understood."}

    def shutdown(self) -> dict:
        try:
            os_type = platform.system()
            if os_type == "Windows":
                subprocess.run(["shutdown", "/s", "/t", "5"], check=True)  # 5 sec delay
            elif os_type == "Linux" or os_type == "Darwin":
                subprocess.run(["shutdown", "-h", "+1"], check=True)  # 1 min delay
            else:
                return {"success": False, "agent": self.name, "message": f"Unsupported OS: {os_type}"}
            return {"success": True, "agent": self.name, "action": "shutdown", "message": "Shutdown initiated."}
        except Exception as e:
            return {"success": False, "agent": self.name, "message": f"Shutdown failed: {str(e)}"}

    def restart(self) -> dict:
        try:
            os_type = platform.system()
            if os_type == "Windows":
                subprocess.run(["shutdown", "/r", "/t", "5"], check=True)
            elif os_type == "Linux" or os_type == "Darwin":
                subprocess.run(["shutdown", "-r", "+1"], check=True)
            else:
                return {"success": False, "agent": self.name, "message": f"Unsupported OS: {os_type}"}
            return {"success": True, "agent": self.name, "action": "restart", "message": "Restart initiated."}
        except Exception as e:
            return {"success": False, "agent": self.name, "message": f"Restart failed: {str(e)}"}

    def lock(self) -> dict:
        try:
            os_type = platform.system()
            if os_type == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            else:
                return {"success": False, "agent": self.name, "message": f"Lock not implemented for {os_type}"}
            return {"success": True, "agent": self.name, "action": "lock", "message": "Workstation locked."}
        except Exception as e:
            return {"success": False, "agent": self.name, "message": f"Lock failed: {str(e)}"}