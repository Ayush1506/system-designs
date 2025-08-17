# Chat Service Architecture & Design

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile App    │    │    Web App      │    │  Other Clients  │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     FastAPI Server       │
                    │   (Port 8000)            │
                    │                          │
                    │  ┌─────────────────────┐ │
                    │  │   REST API          │ │
                    │  │   /api/v1/...       │ │
                    │  └─────────────────────┘ │
                    │                          │
                    │  ┌─────────────────────┐ │
                    │  │   WebSocket         │ │
                    │  │   /api/v1/ws/...    │ │
                    │  └─────────────────────┘ │
                    └─────────────┬────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │     Database Layer       │
                    │                          │
                    │  ┌─────────┐ ┌─────────┐ │
                    │  │  MySQL  │ │ MongoDB │ │
                    │  │         │ │         │ │
                    │  │Metadata │ │Messages │ │
                    │  └─────────┘ └─────────┘ │
                    └──────────────────────────┘
```

## 🎯 Design Philosophy

### **Hybrid Database Architecture**
- **MySQL**: Stores structured metadata (users, chats, relationships)
- **MongoDB**: Stores unstructured message content (optimized for text storage)
- **Why?**: Best of both worlds - ACID compliance for critical data, flexibility for messages

### **Microservice-Ready Design**
- Clean separation of concerns
- Service layer abstracts business logic
- Easy to scale individual components
- Database connections are abstracted

### **Real-Time First**
- WebSocket connections for instant messaging
- Connection management for presence tracking
- Typing indicators and online status
- Sub-1-second message delivery

## 📁 Code Architecture

```
chat_service/
├── main.py                 # 🚀 FastAPI app entry point
├── config.py              # ⚙️ Configuration management
├── database.py            # 🗄️ Database models & connections
├── auth.py                # 🔐 Authentication & JWT handling
├── schemas.py             # 📋 Pydantic data validation models
├── services.py            # 🔧 Business logic layer
├── websocket_manager.py   # 🔌 WebSocket connection management
└── routes/                # 🛣️ API endpoints
    ├── users.py           #   👤 User management
    ├── chats.py           #   💬 Chat operations
    ├── messages.py        #   📝 Message handling
    └── websocket.py       #   🔌 Real-time connections
```

## 🔄 Request Flow

### **REST API Request Flow:**
```
1. Client Request → 2. FastAPI Router → 3. Auth Middleware → 4. Route Handler
                                                                    ↓
8. JSON Response ← 7. Pydantic Serialization ← 6. Service Layer ← 5. Validation
                                                        ↓
                                                9. Database Operations
                                                   (MySQL + MongoDB)
```

### **WebSocket Message Flow:**
```
1. Client connects → 2. WebSocket Auth → 3. Connection Manager → 4. Chat Room
                                                                      ↓
7. Broadcast to all ← 6. Message Storage ← 5. Message Processing ← Message Received
   participants         (MySQL + MongoDB)     (Service Layer)
```

## 🗄️ Database Design

### **MySQL Schema (Structured Data):**

```sql
-- Users table
users:
├── id (Primary Key)
├── username (Unique)
├── email (Unique)
├── hashed_password
├── full_name
├── is_active
├── created_at
└── last_seen

-- Chats table
chats:
├── id (Primary Key)
├── name (for group chats)
├── chat_type ('direct' or 'group')
├── created_at
├── updated_at
└── is_active

-- Many-to-many relationship
chat_participants:
├── user_id (Foreign Key → users.id)
├── chat_id (Foreign Key → chats.id)
├── joined_at
└── is_admin (for group chat admins)

-- Message metadata
message_metadata:
├── id (Primary Key)
├── chat_id (Foreign Key → chats.id)
├── sender_id (Foreign Key → users.id)
├── message_id (UUID → MongoDB document)
├── timestamp
├── message_type
├── is_edited
└── is_deleted
```

### **MongoDB Schema (Message Content):**

```javascript
// messages collection
{
  _id: ObjectId,
  message_id: "uuid-string",  // Links to MySQL
  content: "message text",    // Up to 10,000 characters
  timestamp: ISODate,
  chat_id: 123,              // Links to MySQL
  sender_id: 456,            // Links to MySQL
  edited_at: ISODate         // If message was edited
}
```

## 🔐 Authentication Flow

```
1. User Registration:
   POST /users/register → Hash Password → Store in MySQL → Return User Info

2. User Login:
   POST /users/login → Verify Password → Generate JWT Token → Return Token

3. Authenticated Requests:
   Request + Bearer Token → Verify JWT → Extract User Info → Process Request

4. WebSocket Authentication:
   ws://...?token=JWT → Verify Token → Establish Connection → Join Chat Room
```

## 🔌 WebSocket Architecture

### **Connection Management:**
```python
ConnectionManager:
├── active_connections: {user_id: {chat_id: [websockets]}}
├── user_websockets: {user_id: [websockets]}
├── websocket_users: {websocket: user_id}
└── typing_users: {chat_id: {user_id: timestamp}}
```

### **Message Types:**
- **`message`**: Send/receive chat messages
- **`typing`**: Typing indicators (start/stop)
- **`ping/pong`**: Connection health checks
- **`user_joined/left`**: Presence notifications

### **Real-Time Features:**
1. **Instant Messaging**: Messages broadcast to all chat participants
2. **Typing Indicators**: Show when users are typing
3. **Online Status**: Track who's currently connected
4. **Presence**: Join/leave notifications

## 🏛️ Service Layer Design

### **UserService:**
- User registration and authentication
- Profile management
- User search functionality

### **ChatService:**
- Create 1:1 and group chats
- Manage chat participants
- Admin controls (add/remove users)
- Chat metadata operations

### **MessageService:**
- Send messages (store in both databases)
- Retrieve message history with pagination
- Edit and delete messages
- Message validation (10K character limit)

## 🔄 Data Flow Examples

### **Sending a Message:**
```
1. Client sends message via WebSocket
2. WebSocket handler validates user & chat access
3. MessageService.create_message():
   - Generates unique message_id
   - Stores content in MongoDB
   - Stores metadata in MySQL
   - Updates chat's last_activity
4. Broadcast message to all chat participants
5. Update typing indicators (stop typing)
```

### **Creating a Group Chat:**
```
1. POST /api/v1/chats/ with participant list
2. Validate user authentication
3. ChatService.create_chat():
   - Create chat record in MySQL
   - Add all participants to chat_participants table
   - Set creator as admin
4. Return chat details with participant info
```

### **Real-Time Message Delivery:**
```
1. User A sends message in Chat 1
2. WebSocket manager identifies all users in Chat 1
3. Message is broadcast to all active connections
4. Users B, C, D receive message instantly
5. Offline users will see message when they reconnect
```

## 🚀 Scalability Design

### **Horizontal Scaling Ready:**
- Stateless API design
- Database connections are pooled
- WebSocket connections can be load-balanced
- Service layer can be extracted to microservices

### **Performance Optimizations:**
- Database indexes on frequently queried fields
- Message pagination to handle large chat histories
- Connection pooling for database efficiency
- Async/await for non-blocking operations

### **Future Enhancements:**
- Redis for session management and caching
- Message queues (RabbitMQ/Kafka) for reliability
- CDN for file attachments
- Database sharding for massive scale

## 🛡️ Security Design

### **Authentication & Authorization:**
- JWT tokens with expiration
- Password hashing with bcrypt
- Role-based access (chat admins)
- Input validation with Pydantic

### **Data Protection:**
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (input sanitization)
- CORS configuration
- Rate limiting ready

### **Privacy:**
- Soft delete for messages (recoverable)
- User data isolation
- Chat participant verification
- No end-to-end encryption (as requested)

## 🎯 Key Design Decisions

### **Why FastAPI?**
- High performance (async/await)
- Automatic API documentation
- Type hints and validation
- WebSocket support
- Modern Python framework

### **Why Hybrid Database?**
- **MySQL**: ACID compliance for critical user/chat data
- **MongoDB**: Flexible schema for message content
- **Best Performance**: Right tool for each data type

### **Why JWT Authentication?**
- Stateless (scalable)
- Works with mobile and web
- Industry standard
- Easy to implement and verify

### **Why WebSocket?**
- Real-time messaging requirement
- Bi-directional communication
- Low latency (sub-1-second)
- Efficient for chat applications

## 📊 API Design Patterns

### **RESTful Design:**
- `GET /chats/` - List user's chats
- `POST /chats/` - Create new chat
- `GET /chats/{id}` - Get chat details
- `PUT /chats/{id}` - Update chat
- `DELETE /chats/{id}` - Leave chat

### **Consistent Response Format:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

### **Error Handling:**
```json
{
  "detail": "Descriptive error message",
  "status_code": 400
}
```

## 🔧 Configuration Management

### **Environment-Based Config:**
- Development, staging, production settings
- Database connection strings
- JWT secrets and expiration
- Feature flags and limits

### **Flexible Deployment:**
- Docker-ready
- Environment variables
- Health checks
- Graceful shutdown

This architecture provides a solid foundation for a scalable, maintainable, and feature-rich chat service that can handle both current requirements and future growth! 🚀
