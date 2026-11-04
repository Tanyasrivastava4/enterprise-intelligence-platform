from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
