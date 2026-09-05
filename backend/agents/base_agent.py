class BaseAgent:

    name = "base_agent"

    def execute(self, command: str):

        raise NotImplementedError(
            "Each agent must implement its own execute method."
        )