# Quick Start Guide - Chat Service

This guide will help you run the chat service on your local machine in just a few steps.

## Prerequisites

- Python 3.8 or higher
- MySQL server
- MongoDB server

## Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
cd chat_service
python run_local.py
```

This script will:
1. Check your Python version
2. Install all dependencies
3. Set up environment variables
4. Guide you through database setup
5. Initialize the databases
6. Start the server

## Option 2: Manual Setup

### Step 1: Install Dependencies

```bash
cd chat_service
pip install -r requirements.txt
```

### Step 2: Set up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file with your database credentials (or use defaults for local development).

### Step 3: Set up Databases

**MySQL:**
```sql
CREATE DATABASE chat_service;
CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON chat_service.* TO 'chat_user'@'localhost';
FLUSH PRIVILEGES;
```

**MongoDB:**
- Install and start MongoDB service
- It will run on default port 27017

### Step 4: Initialize Database Tables

```bash
python init_db.py
```

### Step 5: Run the Server

```bash
python main.py
```

## Access the Application

Once running, you can access:

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Quick Test

### 1. Register a User

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

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

Save the `access_token` from the response.

### 3. Create a Chat

```bash
curl -X POST "http://localhost:8000/api/v1/chats/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Test Group",
    "chat_type": "group",
    "participant_ids": []
  }'
```

### 4. Send a Message

```bash
curl -X POST "http://localhost:8000/api/v1/messages/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "chat_id": 1,
    "content": "Hello, world!"
  }'
```

## WebSocket Testing

You can test WebSocket connections using a simple HTML page:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat Test</title>
</head>
<body>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Type a message...">
    <button onclick="sendMessage()">Send</button>

    <script>
        const token = "YOUR_ACCESS_TOKEN";
        const chatId = 1;
        const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${chatId}?token=${token}`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            document.getElementById('messages').innerHTML += '<div>' + JSON.stringify(data) + '</div>';
        };
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = {
                type: "message",
                chat_id: chatId,
                content: input.value
            };
            ws.send(JSON.stringify(message));
            input.value = '';
        }
    </script>
</body>
</html>
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Make sure MySQL and MongoDB are running
   - Check credentials in `.env` file
   - Verify database and user exist

2. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version: `python --version`

3. **Port Already in Use**
   - Change the port in `.env` file or kill the process using port 8000

4. **WebSocket Connection Failed**
   - Make sure you're using a valid JWT token
   - Check that the user has access to the chat

### Database Setup Help

**For macOS (using Homebrew):**
```bash
# Install MySQL
brew install mysql
brew services start mysql

# Install MongoDB
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**For Ubuntu:**
```bash
# Install MySQL
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install mongodb-org
sudo systemctl start mongod
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API documentation at http://localhost:8000/docs
- Check out the WebSocket features for real-time messaging
- Customize the configuration in `.env` file for your needs

## Support

If you encounter any issues, check the logs in the terminal where you started the server. The application provides detailed error messages to help with troubleshooting.
