from core.agent_router import AgentRouter
from core.task_planner import TaskPlanner
from core.task_executor import TaskExecutor

from security.security_manager import SecurityManager
from security.approval import ApprovalManager

from database.database import SessionLocal
from database import crud
from database.models import ReasoningStep   # <-- new import


class AIBrain:
    def __init__(self):
        self.router = AgentRouter()
        self.planner = TaskPlanner()
        self.executor = TaskExecutor()

        self.security = SecurityManager()
        self.approval_manager = ApprovalManager()

    def process_command(self, command: str):
        """
        Process a user command:
        - Route to appropriate agent
        - Analyze risk
        - Create task plan with reasoning
        - Save task & reasoning steps in DB
        - Request approval if needed, else execute
        """
        db = SessionLocal()
        try:
            # 1. Select agent
            selected_agent = self.router.route(command)

            # 2. Analyze risk
            risk_level = self.security.analyze_risk(command)

            # 3. Create task plan (with reasoning steps)
            task_plan = self.planner.create_plan(command, selected_agent)   # returns dict with 'steps'
            task_plan["risk_level"] = risk_level

            # --- DB: create task record ---
            title = command[:255]
            task = crud.create_task(
                db,
                title=title,
                command=command,
                agent=selected_agent,
                risk_level=risk_level
            )
            task_id = task.id

            # --- Save reasoning steps ---
            steps = task_plan.get("steps", [])
            for idx, step in enumerate(steps):
                reasoning = ReasoningStep(
                    task_id=task_id,
                    step_order=idx,
                    action=step.get("action", "unknown"),
                    reason=step.get("reason", "")
                )
                db.add(reasoning)
            db.commit()   # commit steps separately

            # 4. Check if approval is required
            if self.security.requires_approval(risk_level):
                approval = self.approval_manager.create_approval_request(
                    command=command,
                    risk_level=risk_level,
                    agent_name=selected_agent
                )
                # Save approval in DB
                crud.create_approval(
                    db,
                    task_id=task_id,
                    action=command,
                    risk_level=risk_level,
                    approval_id=approval["approval_id"]
                )
                crud.update_task_status(db, task_id, "pending_approval")
                crud.create_log(
                    db,
                    task_id=task_id,
                    agent=selected_agent,
                    action="approval_requested",
                    status="info",
                    message="Approval required"
                )
                db.commit()
                return {
                    "status": "pending_approval",
                    "task_plan": task_plan,
                    "approval": approval,
                    "task_id": task_id
                }
            else:
                # 5. Execute low-risk command
                execution_result = self.executor.execute(selected_agent, command)
                status = "completed" if execution_result.get("success") else "failed"
                crud.update_task_status(db, task_id, status, str(execution_result))
                crud.create_log(
                    db,
                    task_id=task_id,
                    agent=selected_agent,
                    action=status,
                    status="info",
                    message=execution_result.get("message", "")
                )
                db.commit()
                return {
                    "status": "completed",
                    "task_plan": task_plan,
                    "execution_result": execution_result,
                    "task_id": task_id
                }
        finally:
            db.close()

    # ... (approve_task and reject_task remain unchanged)
    # (keep them as they are)