from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    goal: str
    time_horizon: int  # in years
    monthly_budget: float
    risk_tolerance: str  # low, medium, high
    existing_holdings: Optional[str] = None  # JSON string or simple text
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    role: str  # user or assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
