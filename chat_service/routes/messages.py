from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import math
from database import get_db
from auth import get_current_active_user
from schemas import MessageCreate, MessageResponse, MessageUpdate, PaginationParams
from services import MessageService

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a new message to a chat"""
    try:
        message = MessageService.create_message(db, message_data, current_user.id)
        return MessageResponse(**message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/chat/{chat_id}", response_model=dict)
async def get_chat_messages(
    chat_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get messages for a specific chat with pagination"""
    try:
        pagination = PaginationParams(page=page, limit=limit)
        messages, total = MessageService.get_chat_messages(db, chat_id, current_user.id, pagination)
        
        # Convert to response format
        message_responses = [MessageResponse(**msg) for msg in messages]
        
        return {
            "items": message_responses,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total > 0 else 0
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: int,
    message_update: MessageUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a message (only by the sender)"""
    try:
        message = MessageService.update_message(db, message_id, message_update.content, current_user.id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or you don't have permission to edit it"
            )
        return MessageResponse(**message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a message (only by the sender)"""
    try:
        success = MessageService.delete_message(db, message_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or you don't have permission to delete it"
            )
        return {"message": "Message deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
