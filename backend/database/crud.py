from sqlalchemy.orm import Session
from .models import Task, Approval, ActivityLog
from datetime import datetime

def create_task(db: Session, title: str, command: str, agent: str, risk_level: str, status="pending"):
    task = Task(
        title=title,
        command=command,
        agent=agent,
        risk_level=risk_level,
        status=status
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def update_task_status(db: Session, task_id: int, status: str, result: str = None):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = status
        if status == "completed":
            task.completed_at = datetime.utcnow()
        if result is not None:
            task.result = result
        db.commit()
        db.refresh(task)
    return task

def create_approval(db: Session, task_id: int, action: str, risk_level: str, approval_id: str):
    approval = Approval(
        task_id=task_id,
        action=action,
        risk_level=risk_level,
        approval_id=approval_id,
        status="pending"
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval

def approve_approval(db: Session, approval_id: str):
    approval = db.query(Approval).filter(Approval.approval_id == approval_id).first()
    if approval:
        approval.status = "approved"
        approval.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(approval)
    return approval

def reject_approval(db: Session, approval_id: str):
    approval = db.query(Approval).filter(Approval.approval_id == approval_id).first()
    if approval:
        approval.status = "rejected"
        db.commit()
        db.refresh(approval)
    return approval

def create_log(db: Session, task_id: int, agent: str, action: str, status: str, message: str = None):
    log = ActivityLog(
        task_id=task_id,
        agent=agent,
        action=action,
        status=status,
        message=message
    )
    db.add(log)
    db.commit()
    return log

def get_recent_tasks(db: Session, limit: int = 10):
    return db.query(Task).order_by(Task.created_at.desc()).limit(limit).all()

def get_task_stats(db: Session):
    total = db.query(Task).count()
    completed = db.query(Task).filter(Task.status == "completed").count()
    pending = db.query(Task).filter(Task.status.in_(["pending", "in_progress", "pending_approval"])).count()
    pending_approval = db.query(Task).filter(Task.status == "pending_approval").count()
    failed = db.query(Task).filter(Task.status == "failed").count()
    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "pending_approval": pending_approval,
        "failed": failed
    }

def get_pending_approvals(db: Session):
    return db.query(Approval).filter(Approval.status == "pending").all()

def get_task_by_approval_id(db: Session, approval_id: str):
    approval = db.query(Approval).filter(Approval.approval_id == approval_id).first()
    if approval:
        return db.query(Task).filter(Task.id == approval.task_id).first()
    return None