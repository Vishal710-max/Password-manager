# 🔐 SentinelKey Password Manager

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Cryptography](https://img.shields.io/badge/Cryptography-000000?style=for-the-badge&logo=security&logoColor=white)

A secure, modern password manager built with **Streamlit** and **MongoDB** that helps you manage all your passwords in one secure place. With **military-grade encryption** and **two-factor authentication**, your digital life remains protected.

---

## 🎯 Features

### 🔒 Core Security
- **AES-256 Encryption** → Military-grade encryption for all stored passwords  
- **Two-Factor Authentication** → TOTP-based 2FA with QR code setup  
- **Secure MongoDB Storage** → Encrypted document database with access controls  
- **Session Management** → Automatic logout after 10 minutes of inactivity  

---

## 📋 Modules Overview

| Page                | Icon | Description |
|----------------------|------|-------------|
| Login & Registration | 🔐  | Secure user authentication with rate limiting and account lockout |
| Dashboard            | 📊  | Overview of saved passwords and security metrics |
| Password Generator   | 🔑  | Create strong, random passwords with customizable parameters |
| Save Password        | 💾  | Store new credentials with service name and username |
| Update Password      | 🔄  | Modify existing stored passwords |
| Retrieve Password    | 🔍  | Access stored credentials with secure clipboard management |
| View Services        | 📋  | Browse all saved services with pagination |
| Delete Password      | 🗑️  | Permanently remove stored credentials |
| 2FA Settings         | ⚙️  | Configure and manage two-factor authentication |
| Admin Panel          | 🛠️  | Administrative tools for user and database management |

---

## 🚀 Installation Guide

### 🔧 Prerequisites
- Python **3.8+**
- MongoDB **5.0+** (local or cloud instance)
- `pip` (Python package manager)
- `git` (for cloning the repository)

---

### 📥 Step-by-Step Installation

```bash
# 1. Clone the Repository
git clone https://github.com/your-username/sentinelskey-password-manager.git
cd sentinelkey-password-manager

# 2. Create Virtual Environment (Recommended)

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
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
pymongo	MongoDB driver	≥4.5.0
bcrypt	Password hashing	≥4.0.1
cryptography	Encryption utilities	≥41.0.0
pyotp	Two-factor authentication	≥2.8.0
qrcode	QR code generation for 2FA	≥7.4.0
streamlit-option-menu	Sidebar navigation	≥0.3.0
pyperclip	Clipboard management	≥1.8.0

🏗️ Project Structure
plaintext
Copy code
sentinelskey-password-manager/
├── demo.py                   # Main application file
├── requirements.txt          # Python dependencies
├── assets/                   # Static assets
│   └── images/
│       ├── logo.png
│       ├── logo2.png
│       └── password.png
├── pages/                    # Application modules
│   ├── 2fa_verification.py   # 2FA authentication page
│   ├── Account_Locked.py     # Account lockout page
│   ├── Admin.py              # Admin management panel
│   └── Create_Admin.py       # Admin account creation
├── scripts/                  # Utility scripts
│   ├── init_database.py      # Database initialization
│   └── backup_database.py    # Database backup utility
├── crud_operations.py        # Database operations
├── database.py               # MongoDB connection manager
├── encryption.py             # Encryption utilities
├── clipboard_manager.py      # Secure clipboard management
├── two_factor_auth.py        # 2FA utilities
├── 2fa_management.py         # 2FA management
└── migrate_passwords.py      # Password migration utilities
📖 Module Documentation
(… keep the rest of your detailed module explanations as you already wrote, but now formatted in consistent Markdown with ### headings, code blocks, and tables for clarity …)

🛡️ Security Features
AES-256 encryption (Fernet) for stored passwords

BCrypt for password hashing with salt

TOTP 2FA with QR code setup

Auto session expiration after 10 mins

Account lockout after 3 failed attempts

Clipboard auto-clear after configurable delay


📊 Database Schema
Users Collection
json
Copy code
{
  "_id": ObjectId,
  "username": "string",
  "password": "bcrypt hash",
  "created_at": "DateTime",
  "last_login": "DateTime",
  "two_factor_secret": "encrypted string",
  "two_factor_enabled": true,
  "is_admin": false
}
Passwords Collection
json
Copy code
{
  "_id": ObjectId,
  "username": "reference",
  "service": "string",
  "service_username": "string",
  "password": "encrypted",
  "created_at": "DateTime",
  "updated_at": "DateTime"
}


🚦 Deployment
Local
 
Copy code
streamlit run demo.py

Docker
bash
Copy code
docker build -t sentinelkey-password-manager .
docker run -p 8501:8501 sentinelkey-password-manager

PM2
bash
Copy code
npm install -g pm2
pm2 start "streamlit run demo.py" --name "sentinelkey"
pm2 startup
pm2 save


🤝 Contributing
Fork the repository

Create a feature branch:

bash
Copy code
git checkout -b feature/amazing-feature
Commit changes:

bash
Copy code
git commit -m "Add amazing feature"
Push to branch & open PR

📄 License
This project is licensed under the MIT License – see the LICENSE file for details.

⭐ Support
📖 Check documentation

🔍 Search issues on GitHub

🐛 Open a new issue with details

⭐ Star this repo if useful

🔐 SentinelKey – Your digital Guardian for password management

