# Manual Setup Guide - Chat Service

If the automated `run_local.py` script doesn't work for you, follow these manual steps:

## Step 1: Create Virtual Environment

```bash
cd chat_service
python3 -m venv venv
```

## Step 2: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

## Step 3: Install Dependencies

Try the simple requirements first:
```bash
pip install -r requirements-simple.txt
```

If that fails, try:
```bash
pip install -r requirements.txt
```

## Step 4: Set up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file if needed (default values work for local development).

## Step 5: Set up Databases

### MySQL Setup:
1. Install MySQL server
2. Start MySQL service
3. Create database and user:
```sql
CREATE DATABASE chat_service;
CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON chat_service.* TO 'chat_user'@'localhost';
FLUSH PRIVILEGES;
```

### MongoDB Setup:
1. Install MongoDB
2. Start MongoDB service:
   - **macOS**: `brew services start mongodb-community`
   - **Ubuntu**: `sudo systemctl start mongod`
   - **Windows**: Start MongoDB service from Services

## Step 6: Initialize Database Tables

```bash
python init_db.py
```

## Step 7: Run the Server

```bash
python main.py
```

## Step 8: Test the API

Visit http://localhost:8000/docs to see the interactive API documentation.

## Troubleshooting

### Python 3.13 Compatibility Issues

If you're using Python 3.13 and getting build errors, try:

1. **Use Python 3.11 or 3.12 instead:**
   ```bash
   # Install Python 3.11 via pyenv or homebrew
   brew install python@3.11
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements-simple.txt
   ```

2. **Or install packages individually:**
   ```bash
   pip install fastapi uvicorn websockets sqlalchemy pymongo
   pip install mysql-connector-python python-jose passlib
   pip install python-multipart pydantic python-dotenv
   ```

### Database Connection Issues

1. **MySQL not connecting:**
   - Check if MySQL is running: `brew services list | grep mysql`
   - Verify credentials in `.env` file
   - Test connection: `mysql -u chat_user -p chat_service`

2. **MongoDB not connecting:**
   - Check if MongoDB is running: `brew services list | grep mongodb`
   - Test connection: `mongosh` (or `mongo` for older versions)

### Import Errors

Make sure you're in the virtual environment:
```bash
which python  # Should show path to venv/bin/python
```

If not, activate it:
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### Port Already in Use

If port 8000 is busy, change it in `.env`:
```env
PORT=8001
```

## Alternative: Docker Setup (Advanced)

If you prefer Docker, create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: chat_service
      MYSQL_USER: chat_user
      MYSQL_PASSWORD: password
    ports:
      - "3306:3306"
  
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
  
  chat-service:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - mongodb
    environment:
      - MYSQL_HOST=mysql
      - MONGODB_URL=mongodb://mongodb:27017
```

Then run:
```bash
docker-compose up
```

## Success!

Once everything is running, you should see:
- Server running at http://localhost:8000
- API docs at http://localhost:8000/docs
- Health check at http://localhost:8000/health

You can now test the chat service using the API documentation or curl commands from the QUICKSTART.md guide.
