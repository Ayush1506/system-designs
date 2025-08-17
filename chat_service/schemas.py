from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from config import settings

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_seen: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Chat Schemas
class ChatBase(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    chat_type: str = Field(..., pattern="^(direct|group)$")

class ChatCreate(ChatBase):
    participant_ids: List[int] = Field(..., min_items=1)
    
    @validator('participant_ids')
    def validate_participants(cls, v, values):
        if values.get('chat_type') == 'group' and len(v) > settings.MAX_GROUP_MEMBERS:
            raise ValueError(f'Group chat cannot have more than {settings.MAX_GROUP_MEMBERS} members')
        if values.get('chat_type') == 'direct' and len(v) != 1:
            raise ValueError('Direct chat must have exactly 1 other participant')
        return v

class ChatUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)

class ChatResponse(ChatBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    participants: List[UserResponse]

    class Config:
        from_attributes = True

class ChatListResponse(BaseModel):
    id: int
    name: Optional[str]
    chat_type: str
    created_at: datetime
    updated_at: datetime
    participant_count: int
    last_message: Optional[str]
    last_message_time: Optional[datetime]

# Message Schemas
class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=settings.MAX_MESSAGE_LENGTH)

class MessageCreate(MessageBase):
    chat_id: int

class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=settings.MAX_MESSAGE_LENGTH)

class MessageResponse(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    sender_username: str
    timestamp: datetime
    message_type: str
    is_edited: bool
    is_deleted: bool

    class Config:
        from_attributes = True

# WebSocket Schemas
class WebSocketMessage(BaseModel):
    type: str  # 'message', 'typing', 'join', 'leave'
    chat_id: int
    content: Optional[str] = None
    timestamp: Optional[datetime] = None

class WebSocketResponse(BaseModel):
    type: str
    chat_id: int
    message: Optional[MessageResponse] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    content: Optional[str] = None
    timestamp: datetime

# Chat Participant Schemas
class ChatParticipantAdd(BaseModel):
    user_ids: List[int] = Field(..., min_items=1)

class ChatParticipantRemove(BaseModel):
    user_id: int

class ChatParticipantResponse(BaseModel):
    user_id: int
    username: str
    full_name: Optional[str]
    joined_at: datetime
    is_admin: bool

# Pagination Schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    limit: int
    pages: int
