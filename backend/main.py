from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
import tempfile
from datetime import datetime
from core.ai_brain import AIBrain
from services.voice_service import VoiceService
from database.database import SessionLocal
from database import crud
from database.models import ReasoningStep

app = FastAPI(
    title="NEXUS AI",
    description="Personal Autonomous Digital Agent",
    version="1.0.0"
)

# ========== CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Pydantic Models ==========
class CommandRequest(BaseModel):
    command: str

class ApprovalRequest(BaseModel):
    approval_id: str

# ========== Services ==========
ai_brain = AIBrain()
voice_service = VoiceService()

# ========== Health & Root ==========
@app.get("/")
def home():
    return {"message": "Welcome to NEXUS AI", "status": "online"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "system": "NEXUS AI"}

# ========== Text Command ==========
@app.post("/agent/command")
def process_command(request: CommandRequest):
    return ai_brain.process_command(request.command)

# ========== Approvals ==========
@app.post("/approval/approve")
def approve_task(request: ApprovalRequest):
    return ai_brain.approve_task(request.approval_id)

@app.post("/approval/reject")
def reject_task(request: ApprovalRequest):
    return ai_brain.reject_task(request.approval_id)

# ========== Voice Command ==========
@app.post("/voice/command")
async def voice_command(audio: UploadFile = File(...)):
    temp_dir = tempfile.gettempdir()
    temp_audio_path = os.path.join(temp_dir, audio.filename)
    with open(temp_audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    command_text = voice_service.speech_to_text(temp_audio_path)
    if not command_text:
        return {"success": False, "message": "Could not understand audio."}

    result = ai_brain.process_command(command_text)

    if result.get("status") == "pending_approval":
        response_text = (
            f"The command '{command_text}' requires your approval. "
            f"Risk level: {result['approval']['risk_level']}. Do you approve?"
        )
    elif result.get("status") == "completed":
        exec_result = result.get("execution_result", {})
        if exec_result.get("success"):
            # ---- Email summary ----
            if exec_result.get("action") == "fetch_emails":
                emails = exec_result.get("emails", [])
                count = exec_result.get("count", 0)
                if count == 0:
                    response_text = "You have no new emails."
                else:
                    subjects = [e["subject"] for e in emails[:3]]
                    subject_list = ", ".join(subjects)
                    if count > 3:
                        response_text = f"You have {count} emails. The latest subjects are: {subject_list}."
                    else:
                        response_text = f"You have {count} email(s): {subject_list}."
            # ---- Calendar events summary ----
            elif exec_result.get("action") == "get_events":
                events = exec_result.get("events", [])
                count = exec_result.get("count", 0)
                if count == 0:
                    response_text = "You have no upcoming events."
                else:
                    event_list = []
                    for e in events[:3]:
                        start_str = e.get("start", "")
                        try:
                            dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                            local_time = dt.astimezone().strftime("%I:%M %p")
                        except:
                            local_time = start_str
                        event_list.append(f"{e['summary']} at {local_time}")
                    event_text = ", ".join(event_list)
                    if count > 3:
                        response_text = f"You have {count} upcoming events. The next ones are: {event_text}."
                    else:
                        response_text = f"You have {count} event(s): {event_text}."
            else:
                response_text = f"Task completed. {exec_result.get('message', '')}"
        else:
            response_text = f"Task failed: {exec_result.get('message', 'Unknown error')}"
    else:
        response_text = "I processed your command but something went wrong."

    tts_file = voice_service.text_to_speech(response_text)
    return {
        "success": True,
        "command": command_text,
        "result": result,
        "response_text": response_text,
        "tts_file": f"/voice/tts/{os.path.basename(tts_file)}"
    }

# ========== Voice Approval ==========
@app.post("/voice/approve")
async def voice_approve(audio: UploadFile = File(...), approval_id: str = Form(...)):
    temp_dir = tempfile.gettempdir()
    temp_audio_path = os.path.join(temp_dir, audio.filename)
    with open(temp_audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    spoken = voice_service.speech_to_text(temp_audio_path)
    if not spoken:
        return {"success": False, "message": "Could not hear you."}

    positive = ["yes", "approve", "ok", "sure", "go ahead", "proceed"]
    negative = ["no", "cancel", "reject", "stop"]
    spoken_lower = spoken.lower()

    if any(word in spoken_lower for word in positive):
        result = ai_brain.approve_task(approval_id)
        response_text = result.get("message", "Task approved and executed.")
    elif any(word in spoken_lower for word in negative):
        result = ai_brain.reject_task(approval_id)
        response_text = result.get("message", "Task rejected.")
    else:
        response_text = "Please say 'yes' or 'no'."

    tts_file = voice_service.text_to_speech(response_text)
    return {
        "success": True,
        "response_text": response_text,
        "tts_file": f"/voice/tts/{os.path.basename(tts_file)}"
    }

# ========== TTS File Serving ==========
@app.get("/voice/tts/{filename}")
async def get_tts(filename: str):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    if not os.path.exists(file_path) or not file_path.endswith('.wav'):
        return {"error": "File not found"}
    return FileResponse(file_path, media_type="audio/wav", filename=filename)

# ========== Dashboard APIs ==========
@app.get("/dashboard/stats")
def dashboard_stats():
    db = SessionLocal()
    try:
        return crud.get_task_stats(db)
    finally:
        db.close()

@app.get("/dashboard/recent_tasks")
def recent_tasks(limit: int = 10):
    db = SessionLocal()
    try:
        tasks = crud.get_recent_tasks(db, limit)
        return [{"id": t.id, "command": t.command, "agent": t.agent, "status": t.status, "created_at": t.created_at.isoformat()} for t in tasks]
    finally:
        db.close()

@app.get("/dashboard/pending_approvals")
def pending_approvals():
    db = SessionLocal()
    try:
        approvals = crud.get_pending_approvals(db)
        return [{"id": a.id, "action": a.action, "risk_level": a.risk_level, "created_at": a.created_at.isoformat()} for a in approvals]
    finally:
        db.close()

@app.get("/dashboard/emails")
def dashboard_emails(limit: int = 5):
    result = ai_brain.executor.execute("email_agent", "check email")
    if result.get("success"):
        emails = result.get("emails", [])[:limit]
        return {"success": True, "emails": emails}
    else:
        return {"success": False, "message": result.get("message", "Failed to fetch emails")}

@app.get("/dashboard/calendar_events")
def dashboard_calendar_events(days: int = 1):
    result = ai_brain.executor.execute("calendar_agent", f"schedule {days} days")
    if result.get("success"):
        return {"success": True, "events": result.get("events", [])}
    else:
        return {"success": False, "message": result.get("message", "Failed to fetch calendar events.")}

@app.get("/tasks/{task_id}/reasoning")
def get_task_reasoning(task_id: int):
    db = SessionLocal()
    try:
        steps = db.query(ReasoningStep).filter(ReasoningStep.task_id == task_id).order_by(ReasoningStep.step_order).all()
        return [
            {
                "step_order": s.step_order,
                "action": s.action,
                "reason": s.reason,
                "timestamp": s.timestamp.isoformat()
            }
            for s in steps
        ]
    finally:
        db.close()

# ========== Startup Event ==========
@app.on_event("startup")
def startup_event():
    print("🚀 NEXUS AI started successfully.")