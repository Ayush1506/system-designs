from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import math
from database import get_db, User
from auth import get_current_active_user
from schemas import (
    ChatCreate, ChatResponse, ChatUpdate, ChatListResponse,
    ChatParticipantAdd, ChatParticipantRemove, ChatParticipantResponse,
    PaginationParams
)
from services import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat (direct or group)"""
    try:
        chat = ChatService.create_chat(db, chat_data, current_user.id)
        return chat
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=dict)
async def get_user_chats(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all chats for the current user with pagination"""
    pagination = PaginationParams(page=page, limit=limit)
    chats, total = ChatService.get_user_chats(db, current_user.id, pagination)
    
    # Convert to list response format with additional info
    chat_list = []
    for chat in chats:
        # Get last message info (simplified for now)
        last_message = None
        last_message_time = None
        
        # Get participant count
        participant_count = len(chat.participants)
        
        chat_item = ChatListResponse(
            id=chat.id,
            name=chat.name,
            chat_type=chat.chat_type,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            participant_count=participant_count,
            last_message=last_message,
            last_message_time=last_message_time
        )
        chat_list.append(chat_item)
    
    return {
        "items": chat_list,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total > 0 else 0
    }

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat details by ID"""
    chat = ChatService.get_chat_by_id(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access"
        )
    
    return chat

@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update chat details (group chats only)"""
    chat = ChatService.get_chat_by_id(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access"
        )
    
    if chat.chat_type != "group":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update group chats"
        )
    
    # Check if user is admin
    user_participant = None
    for participant in chat.participants:
        if participant.id == current_user.id:
            user_participant = participant
            break
    
    # Get admin status from association table
    from database import chat_participants
    admin_check = db.query(chat_participants).filter(
        chat_participants.c.chat_id == chat_id,
        chat_participants.c.user_id == current_user.id,
        chat_participants.c.is_admin == True
    ).first()
    
    if not admin_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update chat details"
        )
    
    # Update chat
    if chat_update.name is not None:
        chat.name = chat_update.name
    
    db.commit()
    db.refresh(chat)
    return chat

@router.post("/{chat_id}/participants", status_code=status.HTTP_200_OK)
async def add_participants(
    chat_id: int,
    participant_data: ChatParticipantAdd,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add participants to a group chat"""
    try:
        ChatService.add_participants(db, chat_id, participant_data.user_ids, current_user.id)
        return {"message": "Participants added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{chat_id}/participants", status_code=status.HTTP_200_OK)
async def remove_participant(
    chat_id: int,
    participant_data: ChatParticipantRemove,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a participant from a group chat"""
    try:
        ChatService.remove_participant(db, chat_id, participant_data.user_id, current_user.id)
        return {"message": "Participant removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{chat_id}/participants", response_model=List[ChatParticipantResponse])
async def get_chat_participants(
    chat_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all participants of a chat"""
    chat = ChatService.get_chat_by_id(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access"
        )
    
    # Get participant details with admin status
    from database import chat_participants
    participants_query = db.query(
        chat_participants.c.user_id,
        chat_participants.c.joined_at,
        chat_participants.c.is_admin
    ).filter(chat_participants.c.chat_id == chat_id).all()
    
    participants = []
    for participant_data in participants_query:
        user = db.query(User).filter(User.id == participant_data.user_id).first()
        if user:
            participants.append(ChatParticipantResponse(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                joined_at=participant_data.joined_at,
                is_admin=participant_data.is_admin
            ))
    
    return participants

@router.delete("/{chat_id}", status_code=status.HTTP_200_OK)
async def leave_chat(
    chat_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Leave a chat"""
    try:
        ChatService.remove_participant(db, chat_id, current_user.id, current_user.id)
        return {"message": "Left chat successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
