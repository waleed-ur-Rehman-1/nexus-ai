class AgentRouter:
    def route(self, command: str) -> str:
        command_lower = command.lower()

        # File Agent
        if any(w in command_lower for w in ["organize", "scan", "downloads", "arrange folder", "delete folder"]):
            return "file_agent"

        # Browser Agent
        if any(w in command_lower for w in ["open", "browser", "website", "click", "fill", "screenshot", "close", "play", "search"]):
            return "browser_agent"

        # Email Agent
        if any(w in command_lower for w in ["email", "send email", "check email", "read email"]):
            return "email_agent"

        # University Agent
        if any(w in command_lower for w in [
            "university", "assignment", "assignments", "login", "lecture", "lectures",
            "course", "courses", "notification", "notifications", "attendance",
            "timetable", "marks", "internal marks", "upload assignment",
            "check assignment", "check assignments"
        ]):
            return "university_agent"

        # System Agent
        if any(w in command_lower for w in ["shutdown", "restart", "lock"]):
            return "system_agent"

        # Calendar Agent
        if any(w in command_lower for w in ["calendar", "schedule", "meeting", "event", "appointment"]):
            return "calendar_agent"

        # Default fallback
        return "file_agent"