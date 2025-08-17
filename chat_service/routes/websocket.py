from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime
from database import get_db
from auth import verify_token, get_current_active_user
from websocket_manager import manager
from services import MessageService, ChatService
from schemas import MessageCreate, WebSocketMessage

router = APIRouter()

async def get_current_user_ws(token: str, db: Session):
    """Get current user from WebSocket token"""
    payload = verify_token(token)
    if not payload:
        return None
    
    username = payload.get("sub")
    if not username:
        return None
    
    from database import User
    user = db.query(User).filter(User.username == username).first()
    return user

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time chat"""
    # Authenticate user
    user = await get_current_user_ws(token, db)
    if not user:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Verify user has access to this chat
    chat = ChatService.get_chat_by_id(db, chat_id, user.id)
    if not chat:
        await websocket.close(code=4003, reason="Access denied to chat")
        return
    
    # Connect user to chat
    await manager.connect(websocket, user.id, chat_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                ws_message = WebSocketMessage(**message_data)
                
                if ws_message.type == "message":
                    # Handle new message
                    if ws_message.content and ws_message.content.strip():
                        try:
                            # Create message in database
                            message_create = MessageCreate(
                                chat_id=chat_id,
                                content=ws_message.content.strip()
                            )
                            
                            message = MessageService.create_message(db, message_create, user.id)
                            
                            # Broadcast message to all chat participants
                            broadcast_message = {
                                "type": "new_message",
                                "chat_id": chat_id,
                                "message": message,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            await manager.broadcast_to_chat(chat_id, broadcast_message)
                            
                        except ValueError as e:
                            # Send error back to sender
                            error_message = {
                                "type": "error",
                                "message": str(e),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await websocket.send_text(json.dumps(error_message))
                
                elif ws_message.type == "typing":
                    # Handle typing indicator
                    is_typing = ws_message.content == "start"
                    await manager.handle_typing_indicator(user.id, chat_id, is_typing)
                
                elif ws_message.type == "ping":
                    # Handle ping/pong for connection health
                    pong_message = {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_text(json.dumps(pong_message))
                
                else:
                    # Unknown message type
                    error_message = {
                        "type": "error",
                        "message": f"Unknown message type: {ws_message.type}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_text(json.dumps(error_message))
                    
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(error_message))
                
            except Exception as e:
                logging.error(f"Error processing WebSocket message: {e}")
                error_message = {
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(error_message))
                
    except WebSocketDisconnect:
        logging.info(f"User {user.id} disconnected from chat {chat_id}")
    except Exception as e:
        logging.error(f"WebSocket error for user {user.id} in chat {chat_id}: {e}")
    finally:
        await manager.disconnect(websocket)

@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "online_users": manager.get_online_users_count(),
        "total_connections": sum(len(chats) for chats in manager.active_connections.values())
    }

@router.get("/ws/chat/{chat_id}/online")
async def get_chat_online_users(
    chat_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get online users in a specific chat"""
    # Verify user has access to this chat
    chat = ChatService.get_chat_by_id(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found or access denied")
    
    online_users = manager.get_chat_online_users(chat_id)
    
    # Get user details
    from database import User
    users = db.query(User).filter(User.id.in_(online_users)).all()
    
    return {
        "chat_id": chat_id,
        "online_users": [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name
            }
            for user in users
        ],
        "count": len(users)
    }
