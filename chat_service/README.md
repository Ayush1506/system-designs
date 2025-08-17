# Chat Service API

A real-time chat service backend built with FastAPI, supporting both 1:1 and group chats with WebSocket connections for real-time messaging.

## Features

- **User Management**: Registration, authentication, and user search
- **Direct Chats**: 1:1 messaging between users
- **Group Chats**: Group messaging with up to 100 participants
- **Real-time Messaging**: WebSocket-based real-time message delivery
- **Message History**: Persistent message storage with pagination
- **Typing Indicators**: Real-time typing status updates
- **Online Status**: Track online users in chats
- **Message Editing**: Edit and delete messages
- **Admin Controls**: Group chat administration features

## Architecture

- **Backend Framework**: FastAPI
- **Authentication**: JWT tokens
- **Databases**: 
  - MySQL for user metadata, chat metadata, and message metadata
  - MongoDB for message content storage
- **Real-time Communication**: WebSocket connections
- **Message Limit**: 10,000 characters per message
- **Group Limit**: 100 members per group chat

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chat_service
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database configurations
   ```

4. **Set up databases**
   
   **MySQL Setup:**
   ```sql
   CREATE DATABASE chat_service;
   CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'chat_password';
   GRANT ALL PRIVILEGES ON chat_service.* TO 'chat_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
   
   **MongoDB Setup:**
   - Install MongoDB and ensure it's running on localhost:27017
   - The application will automatically create the required database and collections

5. **Run the application**
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/users/register` - Register a new user
- `POST /api/v1/users/login` - Login and get access token

### User Management
- `GET /api/v1/users/me` - Get current user info
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users/search` - Search users
- `GET /api/v1/users/{user_id}` - Get user by ID

### Chat Management
- `POST /api/v1/chats/` - Create a new chat
- `GET /api/v1/chats/` - Get user's chats
- `GET /api/v1/chats/{chat_id}` - Get chat details
- `PUT /api/v1/chats/{chat_id}` - Update chat (group chats only)
- `POST /api/v1/chats/{chat_id}/participants` - Add participants
- `DELETE /api/v1/chats/{chat_id}/participants` - Remove participant
- `GET /api/v1/chats/{chat_id}/participants` - Get chat participants
- `DELETE /api/v1/chats/{chat_id}` - Leave chat

### Message Management
- `POST /api/v1/messages/` - Send a message
- `GET /api/v1/messages/chat/{chat_id}` - Get chat messages
- `PUT /api/v1/messages/{message_id}` - Update message
- `DELETE /api/v1/messages/{message_id}` - Delete message

### WebSocket
- `WS /api/v1/ws/{chat_id}?token={jwt_token}` - WebSocket connection for real-time chat
- `GET /api/v1/ws/stats` - Get WebSocket statistics
- `GET /api/v1/ws/chat/{chat_id}/online` - Get online users in chat

### System
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/info` - API information

## WebSocket Usage

### Connection
Connect to a chat using WebSocket:
```javascript
const token = "your_jwt_token";
const chatId = 123;
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${chatId}?token=${token}`);
```

### Message Types

**Send a message:**
```json
{
  "type": "message",
  "chat_id": 123,
  "content": "Hello, world!"
}
```

**Typing indicator:**
```json
{
  "type": "typing",
  "chat_id": 123,
  "content": "start"  // or "stop"
}
```

**Ping/Pong:**
```json
{
  "type": "ping",
  "chat_id": 123
}
```

### Received Message Types

**New message:**
```json
{
  "type": "new_message",
  "chat_id": 123,
  "message": {
    "id": 456,
    "sender_id": 789,
    "sender_username": "john_doe",
    "content": "Hello, world!",
    "timestamp": "2023-01-01T12:00:00Z"
  }
}
```

**Typing indicators:**
```json
{
  "type": "typing_started",  // or "typing_stopped"
  "user_id": 789,
  "chat_id": 123,
  "timestamp": "2023-01-01T12:00:00Z"
}
```

**User presence:**
```json
{
  "type": "user_joined",  // or "user_left"
  "user_id": 789,
  "chat_id": 123,
  "timestamp": "2023-01-01T12:00:00Z"
}
```

## Configuration

Environment variables in `.env`:

```env
# Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=chat_user
MYSQL_PASSWORD=chat_password
MYSQL_DATABASE=chat_service

MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=chat_messages

# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## Database Schema

### MySQL Tables

**users**
- id, username, email, hashed_password, full_name, is_active, created_at, last_seen

**chats**
- id, name, chat_type, created_at, updated_at, is_active

**chat_participants**
- user_id, chat_id, joined_at, is_admin

**message_metadata**
- id, chat_id, sender_id, message_id, timestamp, message_type, is_edited, is_deleted

### MongoDB Collections

**messages**
- message_id, content, timestamp, chat_id, sender_id

## Development

### Running in Development Mode
```bash
python main.py
```

### Running Tests
```bash
# Add your test commands here
pytest
```

### Code Structure
```
chat_service/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── database.py          # Database models and connections
├── auth.py              # Authentication utilities
├── schemas.py           # Pydantic schemas
├── services.py          # Business logic services
├── websocket_manager.py # WebSocket connection management
├── routes/              # API route handlers
│   ├── __init__.py
│   ├── users.py
│   ├── chats.py
│   ├── messages.py
│   └── websocket.py
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables example
└── README.md           # This file
```

## Production Deployment

1. **Set up production databases**
2. **Configure environment variables**
3. **Use a production WSGI server**:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
4. **Set up reverse proxy (nginx)**
5. **Configure CORS properly**
6. **Set up SSL/TLS certificates**
7. **Configure logging and monitoring**

## Security Considerations

- Change the SECRET_KEY in production
- Configure CORS origins properly
- Use HTTPS in production
- Implement rate limiting
- Add input validation and sanitization
- Set up proper database access controls
- Monitor for suspicious activities

## License

[Add your license information here]
