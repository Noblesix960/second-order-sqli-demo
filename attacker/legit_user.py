import requests
import sys
import re
from bs4 import BeautifulSoup

# Victim server URL
VICTIM_URL = "http://victim:8080"

def register_user():
    """Step 1: Register a user"""
    print("[*] Step 1: Registering user...")
    
    data = {
        "username": "Alice",
        "email": "alice@example.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{VICTIM_URL}/register", data=data, allow_redirects=False)
        if response.status_code in [200, 302]:
            print(f"[+] User registered successfully!")
            print(f"    Username: {data['username']}")
            print(f"    Email: {data['email']}")
            print(f"    Password: {data['password']}")
            return data
        else:
            print(f"[-] Registration error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[-] Connection error: {e}")
        return None

def login_user(credentials):
    """Step 2: Login with the user"""
    print("\n[*] Step 2: Login with the user...")
    
    data = {
        "username": credentials["username"],
        "password": credentials["password"]
    }
    
    try:
        session = requests.Session()
        response = session.post(f"{VICTIM_URL}/login", data=data, allow_redirects=False)
        
        if response.status_code in [200, 302]:
            print("[+] Login successful!")
            return session
        else:
            print(f"[-] Login error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[-] Connection error: {e}")
        return None

def access_dashboard(session):
    """Step 3: Access the dashboard"""
    print("\n[*] Step 3: Accessing the dashboard...")
    
    try:
        response = session.get(f"{VICTIM_URL}/dashboard")
        
        if response.status_code == 200:
            print("[+] Dashboard accessible!")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Estrai informazioni utente loggato
            user_info = soup.find('div', class_='user-info')
            if user_info:
                print("\n[+] Logged User Info:")
                print(user_info.get_text(strip=True, separator='\n'))
            
            # Estrai la tabella degli utenti
            table = soup.find('table')
            if table:
                print("\n[+] Users Table Found:")
                print("=" * 80)
                
                # Header
                headers = [th.get_text(strip=True) for th in table.find_all('th')]
                header_line = " | ".join(f"{h:<15}" for h in headers)
                print(header_line)
                print("=" * 80)
                
                # Rows
                for row in table.find('tbody').find_all('tr'):
                    cells = [td.get_text(strip=True) for td in row.find_all('td')]
                    row_line = " | ".join(f"{c:<15}" for c in cells)
                    print(row_line)
                
                print("=" * 80)
            else:
                print("\n[-] No users table found in dashboard")
                
            return True
        else:
            print(f"[-] Error accessing the dashboard: {response.status_code}")
            return False
    except Exception as e:
        print(f"[-] Connection error: {e}")
        return False

def main():
    
    # Step 1: Registration
    credentials = register_user()
    if not credentials:
        print("\n[!] Error in registration phase")
        sys.exit(1)
    
    # Step 2: Login
    session = login_user(credentials)
    if not session:
        print("\n[!] Error in login phase")
        sys.exit(1)
    
    # Step 3: Dashboard
    success = access_dashboard(session)
    if not success:
        print("\n[!] Error in dashboard access phase")
        sys.exit(1)

if __name__ == "__main__":
    main()
