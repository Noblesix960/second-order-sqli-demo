from flask import request, jsonify, session, render_template, redirect, url_for
from db import get_db, get_cursor
import mysql.connector

def init_routes(app):
    
    @app.route("/", methods=["GET"])
    def index():
        return render_template('index.html')
    
    @app.route("/register", methods=["POST", "GET"])
    def register():
        """
        First interaction: User registration with parametrized query (SAFE)
        The malicious username is safely stored in the database
        """
        if request.method == "GET":
            return render_template('register.html')
        
        # Handle POST request
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not username or not email or not password:
            return render_template('register.html', error="All fields are required")

        db = get_db()
        cursor = get_cursor()
        
        # SAFE: Using parametrized query for INSERT
        query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        try:
            cursor.execute(query, (username, email, password))
            db.commit()
            print(f"[+] User registered: {username}")
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            return render_template('register.html', error="Username already taken")
        except Exception as e:
            return render_template('register.html', error=f"Registration failed: {str(e)}")
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Login endpoint - creates session"""
        if request.method == "GET":
            return render_template('login.html')
        
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            return render_template('login.html', error="Username and password required")
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # SAFE: Using parametrized query
        query = "SELECT id, username, email FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            # Create session
            session['user_id'] = user['id']
            session['username'] = user['username']
            print(f"[+] User logged in: {username}")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    @app.route("/logout", methods=["GET"])
    def logout():
        """Logout endpoint - destroys session"""
        session.clear()
        return redirect(url_for('index'))
    
    @app.route("/dashboard", methods=["GET"])
    def dashboard():
        # Check if user is logged in
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # STEP 1: SAFE - Retrieve user data from database using parametrized query
        safe_query = "SELECT id, username, email FROM users WHERE id = %s"
        print(f"[+] Safe query: {safe_query} with id={user_id}")
        
        try:
            cursor.execute(safe_query, (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                session.clear()
                return redirect(url_for('login'))
            
            # Extract username from DB (this could be malicious!)
            username_from_db = user_data['username']
            print(f"[+] Retrieved username from DB: {username_from_db}")
            
            # STEP 2: VULNERABLE - Use username from DB in unsafe query
            # Developer assumes: "This data is from my DB, so it's safe!" (WRONG!)
            unsafe_query = f"SELECT * FROM users WHERE username = '{username_from_db}'"
            print(f"[!] Executing: {unsafe_query}")
            
            cursor.execute(unsafe_query)
            results = cursor.fetchall()
            
            return render_template('dashboard.html', 
                                 user=user_data,
                                 all_users=results,
                                 query=unsafe_query)
            
        except Exception as e:
            return render_template('dashboard.html',
                                 user=user_data if 'user_data' in locals() else None,
                                 error=str(e),
                                 query=unsafe_query if 'unsafe_query' in locals() else "Query not executed")

