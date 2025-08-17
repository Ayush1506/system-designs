# Authentication Guide - Chat Service API

## 🎉 Great! Your chat service is running!

The "Not authenticated" error means you need to get an authentication token first. Here's how:

## Step 1: Register a User

First, create a user account:

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

**Using the API docs (easier):**
1. Go to http://localhost:8000/docs
2. Find "POST /api/v1/users/register"
3. Click "Try it out"
4. Fill in the form:
   ```json
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "password123",
     "full_name": "Test User"
   }
   ```
5. Click "Execute"

## Step 2: Login to Get Token

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

**Using API docs:**
1. Find "POST /api/v1/users/login"
2. Click "Try it out"
3. Fill in:
   ```json
   {
     "username": "testuser",
     "password": "password123"
   }
   ```
4. Click "Execute"

**You'll get a response like:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**📝 COPY THE ACCESS_TOKEN - you'll need it for all other API calls!**

## Step 3: Use Token for Authenticated Requests

### Method 1: Using API Docs (Easiest)

1. **At the top of http://localhost:8000/docs, click the "Authorize" button** 🔒
2. **Enter your token in the format:** `Bearer YOUR_ACCESS_TOKEN`
   
   Example:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
3. **Click "Authorize"**
4. **Now all API calls will be authenticated automatically!**

### Method 2: Using curl

Add the Authorization header to your requests:

```bash
curl -X POST "http://localhost:8000/api/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "My Test Chat",
    "chat_type": "group",
    "participant_ids": []
  }'
```

## Step 4: Test Creating a Chat

**Using API docs (after authorization):**
1. Find "POST /api/v1/chats/"
2. Click "Try it out"
3. Fill in:
   ```json
   {
     "name": "My First Chat",
     "chat_type": "group",
     "participant_ids": []
   }
   ```
4. Click "Execute"

**Using curl:**
```bash
# Replace YOUR_ACCESS_TOKEN with the actual token from step 2
curl -X POST "http://localhost:8000/api/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "My First Chat",
    "chat_type": "group",
    "participant_ids": []
  }'
```

## Complete Example Workflow

Here's a complete example using curl:

```bash
# 1. Register user
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "password123",
    "full_name": "Alice Smith"
  }'

# 2. Login and get token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"

# 3. Create a chat
curl -X POST "http://localhost:8000/api/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Alice Chat Room",
    "chat_type": "group",
    "participant_ids": []
  }'

# 4. Send a message
curl -X POST "http://localhost:8000/api/v1/messages/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "chat_id": 1,
    "content": "Hello, world! This is my first message!"
  }'

# 5. Get messages
curl -X GET "http://localhost:8000/api/v1/messages/chat/1" \
  -H "Authorization: Bearer $TOKEN"
```

## Using the Interactive API Documentation

**The easiest way is to use the interactive docs:**

1. **Go to http://localhost:8000/docs**
2. **Register a user** using the register endpoint
3. **Login** using the login endpoint to get your token
4. **Click "Authorize" at the top** and enter: `Bearer YOUR_TOKEN`
5. **Now you can test all endpoints easily!**

## Token Expiration

- Tokens expire after 30 minutes (configurable in `.env`)
- When a token expires, you'll get a 401 error
- Just login again to get a new token

## WebSocket Authentication

For WebSocket connections, pass the token as a query parameter:

```javascript
const token = "YOUR_ACCESS_TOKEN";
const chatId = 1;
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${chatId}?token=${token}`);
```

## Common Authentication Errors

**"Not authenticated"**
- You forgot to include the Authorization header
- Your token is expired (login again)
- Wrong token format (should be `Bearer TOKEN`)

**"Could not validate credentials"**
- Invalid token
- Token is expired
- Wrong secret key (check your .env file)

## Quick Test Script

Save this as `test_auth.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Register user
register_data = {
    "username": "testuser",
    "email": "test@example.com", 
    "password": "password123",
    "full_name": "Test User"
}

response = requests.post(f"{BASE_URL}/users/register", json=register_data)
print("Register:", response.status_code, response.json())

# Login
login_data = {
    "username": "testuser",
    "password": "password123"
}

response = requests.post(f"{BASE_URL}/users/login", json=login_data)
token_data = response.json()
token = token_data["access_token"]
print("Login successful, token:", token[:50] + "...")

# Create chat
headers = {"Authorization": f"Bearer {token}"}
chat_data = {
    "name": "Test Chat",
    "chat_type": "group",
    "participant_ids": []
}

response = requests.post(f"{BASE_URL}/chats/", json=chat_data, headers=headers)
print("Create chat:", response.status_code, response.json())
```

Run it with:
```bash
cd chat_service
source venv/bin/activate
pip install requests
python test_auth.py
```

## 🎉 You're All Set!

Your chat service is working perfectly! The authentication is working as designed - you just need to get a token first. Use the interactive docs at http://localhost:8000/docs for the easiest testing experience!
