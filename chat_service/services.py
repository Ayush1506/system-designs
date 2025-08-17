from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
import uuid
from database import User, Chat, MessageMetadata, chat_participants, messages_collection
from schemas import UserCreate, ChatCreate, MessageCreate, PaginationParams
from auth import get_password_hash
from config import settings

class UserService:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if username or email already exists
        existing_user = db.query(User).filter(
            or_(User.username == user_data.username, User.email == user_data.email)
        ).first()
        
        if existing_user:
            if existing_user.username == user_data.username:
                raise ValueError("Username already exists")
            else:
                raise ValueError("Email already exists")
        
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def search_users(db: Session, query: str, limit: int = 10) -> List[User]:
        """Search users by username or full name"""
        return db.query(User).filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.full_name.ilike(f"%{query}%")
            )
        ).filter(User.is_active == True).limit(limit).all()

class ChatService:
    @staticmethod
    def create_chat(db: Session, chat_data: ChatCreate, creator_id: int) -> Chat:
        """Create a new chat"""
        # Validate participants exist
        participant_ids = chat_data.participant_ids + [creator_id]
        participants = db.query(User).filter(User.id.in_(participant_ids)).all()
        
        if len(participants) != len(participant_ids):
            raise ValueError("One or more participants not found")
        
        # For direct chats, check if chat already exists
        if chat_data.chat_type == "direct":
            existing_chat = db.query(Chat).join(chat_participants).filter(
                Chat.chat_type == "direct",
                Chat.is_active == True
            ).group_by(Chat.id).having(
                func.count(chat_participants.c.user_id) == 2
            ).all()
            
            for chat in existing_chat:
                chat_participant_ids = [p.id for p in chat.participants]
                if set(chat_participant_ids) == set(participant_ids):
                    return chat
        
        # Create new chat
        db_chat = Chat(
            name=chat_data.name,
            chat_type=chat_data.chat_type
        )
        
        db.add(db_chat)
        db.flush()  # Get the chat ID
        
        # Add participants
        for participant in participants:
            is_admin = participant.id == creator_id
            db.execute(
                chat_participants.insert().values(
                    user_id=participant.id,
                    chat_id=db_chat.id,
                    is_admin=is_admin
                )
            )
        
        db.commit()
        db.refresh(db_chat)
        return db_chat
    
    @staticmethod
    def get_user_chats(db: Session, user_id: int, pagination: PaginationParams) -> Tuple[List[Chat], int]:
        """Get all chats for a user with pagination"""
        query = db.query(Chat).join(chat_participants).filter(
            chat_participants.c.user_id == user_id,
            Chat.is_active == True
        ).order_by(Chat.updated_at.desc())
        
        total = query.count()
        chats = query.offset((pagination.page - 1) * pagination.limit).limit(pagination.limit).all()
        
        return chats, total
    
    @staticmethod
    def get_chat_by_id(db: Session, chat_id: int, user_id: int) -> Optional[Chat]:
        """Get chat by ID if user is a participant"""
        return db.query(Chat).join(chat_participants).filter(
            Chat.id == chat_id,
            chat_participants.c.user_id == user_id,
            Chat.is_active == True
        ).first()
    
    @staticmethod
    def add_participants(db: Session, chat_id: int, user_ids: List[int], admin_id: int) -> bool:
        """Add participants to a group chat"""
        # Check if user is admin
        admin_check = db.query(chat_participants).filter(
            chat_participants.c.chat_id == chat_id,
            chat_participants.c.user_id == admin_id,
            chat_participants.c.is_admin == True
        ).first()
        
        if not admin_check:
            raise ValueError("Only admins can add participants")
        
        # Get chat and validate it's a group chat
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat or chat.chat_type != "group":
            raise ValueError("Can only add participants to group chats")
        
        # Check current participant count
        current_count = db.query(chat_participants).filter(
            chat_participants.c.chat_id == chat_id
        ).count()
        
        if current_count + len(user_ids) > settings.MAX_GROUP_MEMBERS:
            raise ValueError(f"Cannot exceed {settings.MAX_GROUP_MEMBERS} members in group chat")
        
        # Add new participants
        for user_id in user_ids:
            # Check if user exists and is not already in chat
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue
            
            existing = db.query(chat_participants).filter(
                chat_participants.c.chat_id == chat_id,
                chat_participants.c.user_id == user_id
            ).first()
            
            if not existing:
                db.execute(
                    chat_participants.insert().values(
                        user_id=user_id,
                        chat_id=chat_id,
                        is_admin=False
                    )
                )
        
        db.commit()
        return True
    
    @staticmethod
    def remove_participant(db: Session, chat_id: int, user_id: int, admin_id: int) -> bool:
        """Remove participant from group chat"""
        # Check if user is admin or removing themselves
        if admin_id != user_id:
            admin_check = db.query(chat_participants).filter(
                chat_participants.c.chat_id == chat_id,
                chat_participants.c.user_id == admin_id,
                chat_participants.c.is_admin == True
            ).first()
            
            if not admin_check:
                raise ValueError("Only admins can remove other participants")
        
        # Remove participant
        db.execute(
            chat_participants.delete().where(
                and_(
                    chat_participants.c.chat_id == chat_id,
                    chat_participants.c.user_id == user_id
                )
            )
        )
        
        db.commit()
        return True

class MessageService:
    @staticmethod
    def create_message(db: Session, message_data: MessageCreate, sender_id: int) -> dict:
        """Create a new message"""
        # Verify user is participant in chat
        participant_check = db.query(chat_participants).filter(
            chat_participants.c.chat_id == message_data.chat_id,
            chat_participants.c.user_id == sender_id
        ).first()
        
        if not participant_check:
            raise ValueError("User is not a participant in this chat")
        
        # Generate unique message ID
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Store message content in MongoDB
        mongo_message = {
            "message_id": message_id,
            "content": message_data.content,
            "timestamp": timestamp,
            "chat_id": message_data.chat_id,
            "sender_id": sender_id
        }
        
        messages_collection.insert_one(mongo_message)
        
        # Store message metadata in MySQL
        db_message = MessageMetadata(
            chat_id=message_data.chat_id,
            sender_id=sender_id,
            message_id=message_id,
            timestamp=timestamp
        )
        
        db.add(db_message)
        
        # Update chat's updated_at timestamp
        chat = db.query(Chat).filter(Chat.id == message_data.chat_id).first()
        if chat:
            chat.updated_at = timestamp
        
        db.commit()
        db.refresh(db_message)
        
        # Get sender info
        sender = db.query(User).filter(User.id == sender_id).first()
        
        return {
            "id": db_message.id,
            "chat_id": message_data.chat_id,
            "sender_id": sender_id,
            "sender_username": sender.username,
            "content": message_data.content,
            "timestamp": timestamp,
            "message_type": "text",
            "is_edited": False,
            "is_deleted": False
        }
    
    @staticmethod
    def get_chat_messages(db: Session, chat_id: int, user_id: int, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get messages for a chat with pagination"""
        # Verify user is participant
        participant_check = db.query(chat_participants).filter(
            chat_participants.c.chat_id == chat_id,
            chat_participants.c.user_id == user_id
        ).first()
        
        if not participant_check:
            raise ValueError("User is not a participant in this chat")
        
        # Get message metadata from MySQL
        query = db.query(MessageMetadata).filter(
            MessageMetadata.chat_id == chat_id,
            MessageMetadata.is_deleted == False
        ).order_by(MessageMetadata.timestamp.desc())
        
        total = query.count()
        message_metadata = query.offset((pagination.page - 1) * pagination.limit).limit(pagination.limit).all()
        
        # Get message content from MongoDB
        message_ids = [msg.message_id for msg in message_metadata]
        mongo_messages = list(messages_collection.find({"message_id": {"$in": message_ids}}))
        
        # Create message dict for quick lookup
        mongo_dict = {msg["message_id"]: msg for msg in mongo_messages}
        
        # Combine metadata and content
        messages = []
        for metadata in message_metadata:
            mongo_msg = mongo_dict.get(metadata.message_id, {})
            sender = db.query(User).filter(User.id == metadata.sender_id).first()
            
            messages.append({
                "id": metadata.id,
                "chat_id": metadata.chat_id,
                "sender_id": metadata.sender_id,
                "sender_username": sender.username if sender else "Unknown",
                "content": mongo_msg.get("content", ""),
                "timestamp": metadata.timestamp,
                "message_type": metadata.message_type,
                "is_edited": metadata.is_edited,
                "is_deleted": metadata.is_deleted
            })
        
        return messages, total
    
    @staticmethod
    def update_message(db: Session, message_id: int, new_content: str, user_id: int) -> Optional[dict]:
        """Update a message"""
        # Get message metadata
        message = db.query(MessageMetadata).filter(
            MessageMetadata.id == message_id,
            MessageMetadata.sender_id == user_id,
            MessageMetadata.is_deleted == False
        ).first()
        
        if not message:
            raise ValueError("Message not found or you don't have permission to edit it")
        
        # Update content in MongoDB
        messages_collection.update_one(
            {"message_id": message.message_id},
            {"$set": {"content": new_content, "edited_at": datetime.utcnow()}}
        )
        
        # Update metadata in MySQL
        message.is_edited = True
        db.commit()
        
        # Get updated message
        mongo_msg = messages_collection.find_one({"message_id": message.message_id})
        sender = db.query(User).filter(User.id == message.sender_id).first()
        
        return {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "sender_username": sender.username,
            "content": mongo_msg["content"],
            "timestamp": message.timestamp,
            "message_type": message.message_type,
            "is_edited": message.is_edited,
            "is_deleted": message.is_deleted
        }
    
    @staticmethod
    def delete_message(db: Session, message_id: int, user_id: int) -> bool:
        """Delete a message (soft delete)"""
        message = db.query(MessageMetadata).filter(
            MessageMetadata.id == message_id,
            MessageMetadata.sender_id == user_id,
            MessageMetadata.is_deleted == False
        ).first()
        
        if not message:
            raise ValueError("Message not found or you don't have permission to delete it")
        
        # Soft delete in MySQL
        message.is_deleted = True
        db.commit()
        
        return True
