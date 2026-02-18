import mysql.connector
import time
import sys
import os

db = None
cursor = None

def init_db(max_retries=30, retry_interval=2):
    global db, cursor
    
    print("[*] Waiting for database to be ready...")
    
    # Get database credentials from environment variables
    db_host = os.getenv('DB_HOST', 'db')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', 'rootpassword')
    db_name = os.getenv('DB_NAME', 'vulnerable_app')
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[*] Connection attempt {attempt}/{max_retries}...")
            db = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                connect_timeout=5
            )
            cursor = db.cursor()
            print("[+] Database connected successfully!")
            return True
        except mysql.connector.Error as e:
            if attempt < max_retries:
                print(f"[!] Connection failed: {e}")
                print(f"[*] Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                print(f"[!] Failed to connect to database after {max_retries} attempts")
                print(f"[!] Last error: {e}")
                sys.exit(1)
    
    return False

def get_db():
    return db

def get_cursor():
    return cursor
