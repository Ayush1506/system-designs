from typing import Dict, List, Set
from fastapi import WebSocket
import json
import logging
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        # Store active connections: {user_id: {chat_id: [websockets]}}
        self.active_connections: Dict[int, Dict[int, List[WebSocket]]] = {}
        # Store user to websocket mapping for quick lookup
        self.user_websockets: Dict[int, List[WebSocket]] = {}
        # Store websocket to user mapping
        self.websocket_users: Dict[WebSocket, int] = {}
        # Store typing indicators: {chat_id: {user_id: timestamp}}
        self.typing_users: Dict[int, Dict[int, datetime]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, chat_id: int):
        """Connect a user to a specific chat"""
        await websocket.accept()
        
        # Initialize user connections if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            self.user_websockets[user_id] = []
        
        # Initialize chat connections if not exists
        if chat_id not in self.active_connections[user_id]:
            self.active_connections[user_id][chat_id] = []
        
        # Add websocket to connections
        self.active_connections[user_id][chat_id].append(websocket)
        self.user_websockets[user_id].append(websocket)
        self.websocket_users[websocket] = user_id
        
        logging.info(f"User {user_id} connected to chat {chat_id}")
        
        # Notify other users in the chat that this user joined
        await self.broadcast_to_chat(chat_id, {
            "type": "user_joined",
            "user_id": user_id,
            "chat_id": chat_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_user=user_id)

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket"""
        if websocket not in self.websocket_users:
            return
        
        user_id = self.websocket_users[websocket]
        
        # Remove from websocket_users mapping
        del self.websocket_users[websocket]
        
        # Remove from user_websockets
        if user_id in self.user_websockets:
            self.user_websockets[user_id] = [
                ws for ws in self.user_websockets[user_id] if ws != websocket
            ]
            
            # Clean up empty user entry
            if not self.user_websockets[user_id]:
                del self.user_websockets[user_id]
        
        # Remove from active_connections and notify chats
        if user_id in self.active_connections:
            chats_to_notify = []
            for chat_id, websockets in self.active_connections[user_id].items():
                if websocket in websockets:
                    websockets.remove(websocket)
                    chats_to_notify.append(chat_id)
                    
                    # Clean up empty chat entry
                    if not websockets:
                        del self.active_connections[user_id][chat_id]
            
            # Clean up empty user entry
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            # Notify chats that user left
            for chat_id in chats_to_notify:
                await self.broadcast_to_chat(chat_id, {
                    "type": "user_left",
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude_user=user_id)
        
        # Remove from typing indicators
        for chat_id in list(self.typing_users.keys()):
            if user_id in self.typing_users[chat_id]:
                del self.typing_users[chat_id][user_id]
                
                # Notify others that user stopped typing
                await self.broadcast_to_chat(chat_id, {
                    "type": "typing_stopped",
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude_user=user_id)
                
                # Clean up empty chat entry
                if not self.typing_users[chat_id]:
                    del self.typing_users[chat_id]
        
        logging.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user across all their connections"""
        if user_id in self.user_websockets:
            disconnected_websockets = []
            for websocket in self.user_websockets[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logging.error(f"Error sending message to user {user_id}: {e}")
                    disconnected_websockets.append(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected_websockets:
                await self.disconnect(websocket)

    async def broadcast_to_chat(self, chat_id: int, message: dict, exclude_user: int = None):
        """Broadcast a message to all users in a specific chat"""
        disconnected_websockets = []
        
        for user_id, user_chats in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
                
            if chat_id in user_chats:
                for websocket in user_chats[chat_id]:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        logging.error(f"Error broadcasting to user {user_id} in chat {chat_id}: {e}")
                        disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            await self.disconnect(websocket)

    async def handle_typing_indicator(self, user_id: int, chat_id: int, is_typing: bool):
        """Handle typing indicators"""
        current_time = datetime.utcnow()
        
        if chat_id not in self.typing_users:
            self.typing_users[chat_id] = {}
        
        if is_typing:
            self.typing_users[chat_id][user_id] = current_time
            message_type = "typing_started"
        else:
            if user_id in self.typing_users[chat_id]:
                del self.typing_users[chat_id][user_id]
            message_type = "typing_stopped"
            
            # Clean up empty chat entry
            if not self.typing_users[chat_id]:
                del self.typing_users[chat_id]
        
        # Broadcast typing status to other users in the chat
        await self.broadcast_to_chat(chat_id, {
            "type": message_type,
            "user_id": user_id,
            "chat_id": chat_id,
            "timestamp": current_time.isoformat()
        }, exclude_user=user_id)

    def get_chat_users(self, chat_id: int) -> Set[int]:
        """Get all users currently connected to a specific chat"""
        users = set()
        for user_id, user_chats in self.active_connections.items():
            if chat_id in user_chats and user_chats[chat_id]:
                users.add(user_id)
        return users

    def get_user_chats(self, user_id: int) -> Set[int]:
        """Get all chats a user is currently connected to"""
        if user_id in self.active_connections:
            return set(self.active_connections[user_id].keys())
        return set()

    def is_user_online(self, user_id: int) -> bool:
        """Check if a user is currently online"""
        return user_id in self.user_websockets and len(self.user_websockets[user_id]) > 0

    def get_online_users_count(self) -> int:
        """Get total number of online users"""
        return len(self.user_websockets)

    def get_chat_online_users(self, chat_id: int) -> List[int]:
        """Get list of online users in a specific chat"""
        return list(self.get_chat_users(chat_id))

# Global connection manager instance
manager = ConnectionManager()
