from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from dotenv import load_dotenv
import os

# Load environment variables before other imports
load_dotenv()

from backend.database import get_session, create_db_and_tables
from backend.models import UserProfile, ChatMessage
from backend.llm_service import generate_response
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Investment Insights AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Investment Insights API is running"}

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

class ProfileCreate(BaseModel):
    goal: str
    time_horizon: int
    monthly_budget: float
    risk_tolerance: str
    existing_holdings: Optional[str] = None

class ChatRequest(BaseModel):
    user_id: int
    message: str

@app.post("/profile")
def create_profile(profile: ProfileCreate, session: Session = Depends(get_session)):
    db_profile = UserProfile(**profile.dict())
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    return db_profile

@app.get("/profile/{user_id}")
def get_profile(user_id: int, session: Session = Depends(get_session)):
    profile = session.get(UserProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.post("/chat")
def chat(request: ChatRequest, session: Session = Depends(get_session)):
    # 1. Fetch user profile
    profile = session.get(UserProfile, request.user_id)
    if not profile:
        profile_data = {"goal": "Not specified", "time_horizon": 0, "monthly_budget": 0, "risk_tolerance": "medium"}
    else:
        profile_data = profile.dict()
    
    # 2. Fetch history
    history_stmt = select(ChatMessage).where(ChatMessage.user_id == request.user_id).order_by(ChatMessage.timestamp)
    history_records = session.exec(history_stmt).all()
    history = [{"role": m.role, "content": m.content} for m in history_records]
    
    # 3. Save user message
    user_msg = ChatMessage(user_id=request.user_id, role="user", content=request.message)
    session.add(user_msg)
    
    # 4. Generate AI response
    ai_content = generate_response(request.message, profile_data, history)
    
    # 5. Save AI message
    ai_msg = ChatMessage(user_id=request.user_id, role="assistant", content=ai_content)
    session.add(ai_msg)
    session.commit()
    
    return {"response": ai_content}

@app.get("/history/{user_id}")
def get_history(user_id: int, session: Session = Depends(get_session)):
    stmt = select(ChatMessage).where(ChatMessage.user_id == user_id).order_by(ChatMessage.timestamp)
    return session.exec(stmt).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
