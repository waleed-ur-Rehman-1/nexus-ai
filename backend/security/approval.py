import uuid

class ApprovalManager:
    def __init__(self):
        self.pending_approvals = {}

    def create_approval_request(self, command: str, risk_level: str, agent_name: str):
        approval_id = str(uuid.uuid4())
        approval_data = {
            "approval_id": approval_id,
            "command": command,
            "risk_level": risk_level,
            "agent_name": agent_name,
            "status": "pending"
        }
        self.pending_approvals[approval_id] = approval_data
        return {
            "approval_required": True,
            "status": "pending_approval",
            "approval_id": approval_id,
            "command": command,
            "risk_level": risk_level,
            "message": "User approval is required before this action can continue."
        }

    def approve(self, approval_id: str):
        approval = self.pending_approvals.get(approval_id)
        if not approval:
            return None
        approval["status"] = "approved"
        return approval

    def reject(self, approval_id: str):
        approval = self.pending_approvals.get(approval_id)
        if not approval:
            return None
        approval["status"] = "rejected"
        return approval