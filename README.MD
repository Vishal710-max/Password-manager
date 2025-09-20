 SentinelKey Password Manager
https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white
https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white
https://img.shields.io/badge/Cryptography-000000?style=for-the-badge&logo=security&logoColor=white

A secure, modern password manager built with Streamlit and MongoDB that helps you manage all your passwords in one secure place. With military-grade encryption and two-factor authentication, your digital life remains protected.

🎯 Features
🔒 Core Security
AES-256 Encryption → Military-grade encryption for all stored passwords

Two-Factor Authentication → TOTP-based 2FA with QR code setup

Secure MongoDB Storage → Encrypted document database with proper access controls

Session Management → Automatic logout after 10 minutes of inactivity

📋 Modules Overview
Page	Icon	Description
Login & Registration	🔐	Secure user authentication with rate limiting and account lockout
Dashboard	📊	Overview of saved passwords and security metrics
Password Generator	🔑	Create strong, random passwords with customizable parameters
Save Password	💾	Store new credentials with service name and username
Update Password	🔄	Modify existing stored passwords
Retrieve Password	🔍	Access stored credentials with secure clipboard management
View Services	📋	Browse all saved services with pagination
Delete Password	🗑️	Remove stored credentials permanently
2FA Settings	⚙️	Configure and manage two-factor authentication
Admin Panel	🛠️	Administrative tools for user and database management (admin only)
🚀 Installation Guide
🔧 Prerequisites
Python 3.8 or higher

MongoDB 5.0 or higher (local or cloud instance)

pip (Python package manager)

Git (for cloning the repository)

📥 Step-by-Step Installation
bash
# 1. Clone the Repository
git clone https://github.com/your-username/sentinelskey-password-manager.git
cd sentinelkey-password-manager

# 2. Create Virtual Environment (Recommended)

# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Initialize Database
python scripts/init_database.py

# 5. Run the Application
streamlit run demo.py
The app will open in your browser at http://localhost:8501

📦 Requirements
Package	Purpose	Version
streamlit	Web application framework	≥1.28.0
pymongo	MongoDB database driver	≥4.5.0
bcrypt	Password hashing	≥4.0.1
cryptography	Encryption utilities	≥41.0.0
pyotp	Two-factor authentication	≥2.8.0
qrcode	QR code generation for 2FA	≥7.4.0
streamlit-option-menu	Sidebar navigation menu	≥0.3.0
pyperclip	Clipboard management	≥1.8.0


🏗️ Project Structure
sentinelskey-password-manager/
├── demo.py                      # Main application file
├── requirements.txt             # Python dependencies
├── assets/                      # Static assets
│   └── images/
│       ├── logo.png
│       ├── logo2.png
│       └── password.png
├── pages/                       # Application modules
│   ├── 2fa_verification.py     # 2FA authentication page
│   ├── Account_Locked.py       # Account lockout page
│   ├── Admin.py                # Admin management panel
│   └── Create_Admin.py         # Admin account creation
├── scripts/                     # Utility scripts
│   ├── init_database.py        # Database initialization
│   └── backup_database.py      # Database backup utility
|   
|   # Core functionality modules
    ├── crud_operations.py      # Database operations
    ├── database.py             # MongoDB connection manager
    ├── encryption.py           # Encryption utilities
    ├── clipboard_manager.py    # Secure clipboard management
    ├── two_factor_auth.py      # 2FA utilities
    ├── 2fa_management.py       # 2FA management
    └── migrate_passwords.py    # Password migration utilities

📖 Module Documentation

🔐 Login & Registration
File: demo.py (login/register functions)

Secure user authentication with bcrypt password hashing

Rate limiting and account lockout after multiple failed attempts

Session management with automatic timeout


📊 Dashboard

File: demo.py (main_app function)

Overview of security statistics and saved password count

Quick action buttons for common tasks

Password strength metrics and recent activity


🔑 Password Generator

File: demo.py (password_generator_section function)

Generates cryptographically secure random passwords

Customizable length and character sets (lowercase, uppercase, numbers, symbols)

Option to save generated passwords directly to vault


💾 Save Password

File: demo.py (save_password_section function)

Store new credentials with service name and username

Input validation and duplicate service checking

Automatic encryption before storage


🔄 Update Password

File: demo.py (update_password_section function)

Modify existing stored passwords

Preserves service username while updating password

Re-encryption with updated credentials


🔍 Retrieve Password

File: demo.py (retrieve_password_section function)

Access stored credentials with search functionality

Secure clipboard management with auto-clear feature

Optional password reveal with masking


📋 View Services

File: demo.py (list_services function)

Browse all saved services with pagination

Expandable sections to reveal passwords

Clean card-based interface


🗑️ Delete Password

File: demo.py (delete_password_section function)

Remove stored credentials permanently

Confirmation-free deletion with immediate effect

Database cleanup and cache invalidation


⚙️ 2FA Settings

File: 2fa_management.py

Setup and configure two-factor authentication

QR code generation for authenticator apps

TOTP secret management and verification


🛠️ Admin Panel

File: Admin.py (admin users only)

User management and database statistics

System health checks and performance monitoring

Export functionality for user data


🔧 Configuration

🗄️ Database Setup
Install MongoDB (if using locally):

bash
# Ubuntu/Debian
sudo apt-get install mongodb

# macOS with Homebrew
brew install mongodb/brew/mongodb-community

# Windows - download from mongodb.com
Start MongoDB service:

bash
# Linux
sudo systemctl start mongod

# macOS
brew services start mongodb/brew/mongodb-community

# Windows - run as service or use mongod.exe
Create admin user:

bash

python scripts/init_database.py

🔑 Environment Variables
Create a .env file in the root directory:

env
# Encryption key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
PASSWORD_MANAGER_ENCRYPTION_KEY=your_secure_encryption_key_here

# MongoDB connection string
MONGODB_URI=mongodb://localhost:27017/password_manager

# Optional: External MongoDB Atlas connection
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/password_manager

⚙️ Streamlit Configuration (.streamlit/config.toml)
toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[client]
showSidebarNavigation = true

[runner]
magicEnabled = false

[theme]
base = "dark"
primaryColor = "#00BFFF"
backgroundColor = "#1A1A2E"
secondaryBackgroundColor = "#0F3460"
textColor = "#E0E0E0"


🛡️ Security Features

Encryption Standards
AES-256 for password encryption using Fernet

BCrypt with salt for password hashing (12 rounds)


TOTP for two-factor authentication

Protection Mechanisms

🔒 Automatic session expiration (10 minutes)

🚫 Account lockout after 3 failed attempts (1 minute lockout)

📋 Clipboard auto-clear functionality (10-120 seconds configurable)


🔑 Master password never stored in plaintext

🗄️ Encrypted database storage

Security Best Practices
Prepared statements for all database queries

Input validation and sanitization

Rate limiting on authentication attempts

Secure headers and CORS protection

No sensitive data in logs or error messages


📊 Database Schema

Users Collection
javascript
{
  _id: ObjectId,
  username: String (unique),
  password: String (bcrypt hash),
  created_at: DateTime,
  last_login: DateTime,
  two_factor_secret: String (encrypted),
  two_factor_enabled: Boolean,
  is_admin: Boolean
}

Passwords Collection
javascript
{
  _id: ObjectId,
  username: String (reference),
  service: String,
  service_username: String,
  password: String (encrypted),
  created_at: DateTime,
  updated_at: DateTime
}


🔄 API Reference

Authentication Endpoints
POST /login - User authentication

POST /register - User registration

POST /verify-2fa - Two-factor authentication


Password Management Endpoints

GET /passwords - Retrieve all passwords for user

POST /passwords - Create new password entry

PUT /passwords/:service - Update password for service

DELETE /passwords/:service - Delete password for service


Admin Endpoints (admin only)

GET /admin/users - List all users

GET /admin/stats - System statistics

POST /admin/backup - Database backup


🚦 Deployment

Local Development
bash

streamlit run demo.py
Production Deployment
bash

# Using Docker
docker build -t sentinelkey-password-manager .
docker run -p 8501:8501 sentinelkey-password-manager

# Using PM2 (with streamlit)
npm install -g pm2
pm2 start streamlit --name "sentinelkey" -- run demo.py
pm2 startup
pm2 save
Environment Variables for Production
 

export 

PASSWORD_MANAGER_ENCRYPTION_KEY=your_production_encryption_key
export MONGODB_URI=your_production_mongodb_connection_string
export STREAMLIT_SERVER_HEADLESS=true


🐛 Troubleshooting

Common Issues
MongoDB Connection Failed

Check if MongoDB service is running

Verify connection string in environment variables

Encryption Errors

Ensure encryption key is properly set in environment variables

Key must be 32 url-safe base64-encoded bytes

Import Errors

Verify all requirements are installed: pip install -r requirements.txt

Check Python version (requires 3.8+)

2FA Not Working

Verify system time is synchronized (TOTP requires accurate time)

Check QR code scanning with authenticator app


Getting Help

Check the logs for detailed error messages

Verify all environment variables are set correctly

Ensure MongoDB is accessible from the application

Confirm all dependencies are installed


🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

Fork the repository

Create a feature branch: git checkout -b feature/amazing-feature

Commit changes: git commit -m 'Add amazing feature'

Push to branch: git push origin feature/amazing-feature

Open a pull request

Development Setup
bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black .
isort .
📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🆘 Support
If you encounter any problems or have questions:

📖 Check the documentation above

🔍 Search existing issues on GitHub

🐛 Create a new issue with detailed information

⭐ Star us on GitHub if you find this project useful!

SentinelKey - Your digital Guardian for password management 🔐