from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime


class RecommendRequest(BaseModel):
    user_id: str
    query: Optional[str] = ""


class RecommendResponse(BaseModel):
    user_id: str
    query: str
    result: str
    created_at: datetime


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    user_id: str
    message: str
    reply: str
    created_at: datetime
