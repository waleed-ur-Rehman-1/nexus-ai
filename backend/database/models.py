from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class TaskStatus(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    pending_approval = "pending_approval"
    rejected = "rejected"

class TaskPriority(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)          # placeholder for multi-user
    title = Column(String(255))
    description = Column(Text, nullable=True)
    agent = Column(String(100))
    command = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium)
    risk_level = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    action = Column(String(255))
    risk_level = Column(String(20))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approval_id = Column(String(50), unique=True, index=True)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    agent = Column(String(100))
    action = Column(String(255))
    status = Column(String(20))
    message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ========== NEW: Reasoning Steps ==========
class ReasoningStep(Base):
    __tablename__ = "reasoning_steps"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    step_order = Column(Integer, nullable=False)      # order in the plan
    action = Column(String(255), nullable=False)      # e.g., "find_file", "open_portal"
    reason = Column(Text, nullable=True)              # human‑readable explanation
    timestamp = Column(DateTime, default=datetime.utcnow)