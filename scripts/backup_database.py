#scripts/backup_database.py
from database import mongo_manager
from datetime import datetime
import subprocess
import os

def backup_database():
    """Create a MongoDB backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # Use mongodump for proper backup
        result = subprocess.run([
            "mongodump",
            "--uri", "mongodb://localhost:27017/password_manager",
            "--out", backup_dir
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup created: {backup_dir}")
            return True
        else:
            print(f"❌ Backup failed: {result.stderr}")
            return False
#            
#    except Exception as e:
#        print(f"❌ Backup error: {str(e)}")

        return False
