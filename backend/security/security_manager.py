class SecurityManager:
    def __init__(self):
        # Define trusted patterns (lambda functions)
        self.trusted_patterns = [
            # Auto-approve arrange folder for specific directory
            lambda cmd: "arrange folder" in cmd and "C:/Users/waleed/Desktop/Trusted" in cmd,
            # Example: auto-approve scan/downloads
            lambda cmd: "scan" in cmd and "download" in cmd,
            # You can add more
        ]

    def analyze_risk(self, command: str):
        command_lower = command.lower()

        high_risk_words = [
            "send email", "submit assignment", "publish",
            "delete", "payment", "transfer money",
            "submit", "sign in", "purchase", "order",
            "upload assignment", "submit assignment",
            "shutdown", "restart", "delete folder",
            "send email"  # already included
        ]
        medium_risk_words = [
            "upload", "start", "install",
            "organize", "fill", "click",
            "download assignment", "check assignment",
            "arrange folder"
        ]

        if any(word in command_lower for word in high_risk_words):
            return "high"
        elif any(word in command_lower for word in medium_risk_words):
            return "medium"
        return "low"

    def is_auto_approved(self, command: str) -> bool:
        for pattern in self.trusted_patterns:
            if pattern(command):
                return True
        return False

    def requires_approval(self, risk_level: str, command: str = "") -> bool:
        if self.is_auto_approved(command):
            return False
        return risk_level in ["medium", "high"]