# Database Setup Guide

This guide will help you install and set up MySQL and MongoDB for the chat service.

## MySQL Installation

### macOS (using Homebrew - Recommended)

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install MySQL**:
   ```bash
   brew install mysql
   ```

3. **Start MySQL service**:
   ```bash
   brew services start mysql
   ```

4. **Secure MySQL installation** (optional but recommended):
   ```bash
   mysql_secure_installation
   ```
   - Set root password when prompted
   - Answer 'Y' to most questions for better security

5. **Create database and user**:
   ```bash
   mysql -u root -p
   ```
   
   Then run these SQL commands:
   ```sql
   CREATE DATABASE chat_service;
   CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'password';
   GRANT ALL PRIVILEGES ON chat_service.* TO 'chat_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

### macOS (using MySQL Installer)

1. **Download MySQL**:
   - Go to https://dev.mysql.com/downloads/mysql/
   - Download "MySQL Community Server" for macOS
   - Choose the DMG Archive

2. **Install MySQL**:
   - Open the downloaded DMG file
   - Run the MySQL installer
   - Follow the installation wizard
   - **Important**: Remember the root password you set!

3. **Start MySQL**:
   - Go to System Preferences → MySQL
   - Click "Start MySQL Server"
   - Or use Terminal: `sudo /usr/local/mysql/support-files/mysql.server start`

4. **Add MySQL to PATH** (optional):
   ```bash
   echo 'export PATH="/usr/local/mysql/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

5. **Create database and user**:
   ```bash
   mysql -u root -p
   ```
   
   Then run the SQL commands from step 5 above.

### Ubuntu/Linux

1. **Update package list**:
   ```bash
   sudo apt update
   ```

2. **Install MySQL**:
   ```bash
   sudo apt install mysql-server
   ```

3. **Start MySQL service**:
   ```bash
   sudo systemctl start mysql
   sudo systemctl enable mysql
   ```

4. **Secure MySQL installation**:
   ```bash
   sudo mysql_secure_installation
   ```

5. **Create database and user**:
   ```bash
   sudo mysql -u root -p
   ```
   
   Then run the SQL commands from the macOS section.

### Windows

1. **Download MySQL**:
   - Go to https://dev.mysql.com/downloads/installer/
   - Download "MySQL Installer for Windows"

2. **Install MySQL**:
   - Run the installer
   - Choose "Developer Default" setup type
   - Follow the installation wizard
   - Set root password when prompted

3. **Start MySQL**:
   - MySQL should start automatically
   - Or use Services: Windows + R → `services.msc` → Find MySQL → Start

4. **Create database and user**:
   - Open MySQL Command Line Client
   - Enter root password
   - Run the SQL commands from the macOS section

## MongoDB Installation

### macOS (using Homebrew - Recommended)

1. **Add MongoDB tap**:
   ```bash
   brew tap mongodb/brew
   ```

2. **Install MongoDB**:
   ```bash
   brew install mongodb-community
   ```

3. **Start MongoDB service**:
   ```bash
   brew services start mongodb-community
   ```

4. **Verify installation**:
   ```bash
   mongosh
   # or for older versions:
   mongo
   ```

### macOS (using MongoDB Installer)

1. **Download MongoDB**:
   - Go to https://www.mongodb.com/try/download/community
   - Select macOS and download

2. **Install MongoDB**:
   - Open the downloaded file
   - Follow installation instructions

3. **Start MongoDB**:
   ```bash
   sudo brew services start mongodb-community
   ```

### Ubuntu/Linux

1. **Import MongoDB public key**:
   ```bash
   wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
   ```

2. **Add MongoDB repository**:
   ```bash
   echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
   ```

3. **Update and install**:
   ```bash
   sudo apt update
   sudo apt install mongodb-org
   ```

4. **Start MongoDB**:
   ```bash
   sudo systemctl start mongod
   sudo systemctl enable mongod
   ```

### Windows

1. **Download MongoDB**:
   - Go to https://www.mongodb.com/try/download/community
   - Select Windows and download

2. **Install MongoDB**:
   - Run the installer
   - Choose "Complete" installation
   - Install as a service (recommended)

3. **Start MongoDB**:
   - Should start automatically as a service
   - Or use Services: Windows + R → `services.msc` → Find MongoDB → Start

## Verify Installation

### Test MySQL Connection
```bash
mysql -u chat_user -p chat_service
# Enter password: password
# You should see: mysql>
```

### Test MongoDB Connection
```bash
mongosh
# or for older versions:
mongo
# You should see: >
```

## Troubleshooting

### MySQL Issues

**"Command not found: mysql"**
- macOS: Add to PATH or use full path `/usr/local/mysql/bin/mysql`
- Install MySQL properly using one of the methods above

**"Access denied for user"**
- Check username and password
- Make sure you created the user correctly
- Try connecting as root first: `mysql -u root -p`

**"Can't connect to MySQL server"**
- Make sure MySQL is running: `brew services list | grep mysql`
- Start MySQL: `brew services start mysql`

### MongoDB Issues

**"Command not found: mongosh"**
- Try `mongo` instead (older versions)
- Make sure MongoDB is installed properly

**"Connection refused"**
- Make sure MongoDB is running: `brew services list | grep mongodb`
- Start MongoDB: `brew services start mongodb-community`

## Quick Test Commands

After installation, test both databases:

```bash
# Test MySQL
mysql -u chat_user -p chat_service -e "SELECT 'MySQL is working!' as status;"

# Test MongoDB
mongosh --eval "print('MongoDB is working!')"
```

## Next Steps

Once both databases are installed and running:

1. **Run the chat service**:
   ```bash
   cd chat_service
   python3 run_local.py
   # Answer 'y' when asked about databases
   ```

2. **Access the service**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

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
    volumes:
      - mysql_data:/var/lib/mysql

  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mysql_data:
  mongodb_data:
```

Then run:
```bash
docker-compose up -d
```

This will start both databases in Docker containers.
