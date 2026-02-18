# Second-Order SQL Injection Demonstration

This project provides a hands-on demonstration of a **Second-Order SQL Injection** vulnerability. It is designed for educational purposes to illustrate how this subtle and often-overlooked type of SQLi works, and how to prevent it.

The environment is fully containerized using Docker, making it easy to set up and run.

## What is a Second-Order SQL Injection?

Unlike a classic (First-Order) SQL Injection where the malicious payload is executed immediately, a Second-Order SQL Injection occurs in two distinct steps:

1.  **Storage:** The attacker's malicious input is safely stored in the database. The application uses a secure, parameterized query, so no injection happens at this stage.
2.  **Execution:** The application later retrieves the stored (and trusted) data from the database and uses it to construct a new, *unsafe* SQL query. This second query is what triggers the injection, leading to unauthorized data access.

The core of the vulnerability lies in the **false trust** developers place in data retrieved from their own database.

## Project Architecture

The project consists of three main services orchestrated by `docker-compose`:

-   `db`: A MySQL database service that stores the application data. It's initialized with a `users` table and a default `admin` user.
-   `victim`: A vulnerable Flask web application. It exposes endpoints for user registration, login, and a dashboard. The vulnerability is located in the dashboard logic.
-   `attacker`: A container with Python scripts to simulate both a malicious attack and a legitimate user's actions.

## How the Attack Works

The attack flow is demonstrated by the [`attacker/attack.py`](attacker/attack.py) script and can be broken down into three phases.

### Phase 1: Register a Malicious User (Safe)

The attacker registers a new user with a specially crafted username that contains an SQL payload.

-   **Payload:** `admin' OR '1'='1`
-   **Action:** The attacker submits the registration form.

The application's `register` function in [`victim/app/routes.py`](victim/app/routes.py) uses a **parameterized query** to insert the new user into the database.

```python
# victim/app/routes.py
# ...existing code...
        # SAFE: Using parametrized query for INSERT
        query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        try:
            cursor.execute(query, (username, email, password))
# ...existing code...
```

At this point, the payload is stored as a literal string in the `username` column. No injection has occurred.

### Phase 2: Login as the Malicious User (Safe)

The attacker logs in using the credentials created in Phase 1. The login functionality is also secure, as it uses a parameterized query to verify the username and password.

A valid session is created for the user `admin' OR '1'='1`.

### Phase 3: Access the Dashboard (Vulnerable)

This is where the second-order injection is triggered. When the logged-in user visits the dashboard, the application performs two steps:

1.  **Retrieve User Data (Safe):** It fetches the current user's details from the database using the `user_id` stored in the session. This is done securely.
    ```python
    # victim/app/routes.py
    # ...existing code...
            safe_query = "SELECT id, username, email FROM users WHERE id = %s"
            cursor.execute(safe_query, (user_id,))
            user_data = cursor.fetchone()
            username_from_db = user_data['username'] # This now holds "admin' OR '1'='1"
    # ...existing code...
    ```

2.  **Construct a New Query (Vulnerable):** The application now **trusts** the `username_from_db` variable because it came from its own database. It uses this variable to build a new query using an f-string, which is unsafe.
    ```python
    # victim/app/routes.py
    # ...existing code...
            # STEP 2: VULNERABLE - Use username from DB in unsafe query
            unsafe_query = f"SELECT * FROM users WHERE username = '{username_from_db}'"
            print(f"[!] Executing: {unsafe_query}")
            
            cursor.execute(unsafe_query)
    # ...existing code...
    ```

The `unsafe_query` string becomes:

```sql
SELECT * FROM users WHERE username = 'admin' OR '1'='1'
```

The `OR '1'='1'` condition makes the `WHERE` clause always true, causing the query to return **all records** from the `users` table, including the admin's credentials.

## How to Run the Demonstration

### Prerequisites

-   Docker
-   Docker Compose

### 1. Start the Environment

Build and start all services in detached mode:

```sh
docker-compose up --build -d
```

You can monitor the logs to see the services starting up:

```sh
docker-compose logs -f victim
```

### 2. Run the Attack Script

Execute the automated attack script from the `attacker` container:

```sh
docker-compose exec attacker python attack.py
```

You will see the output detailing each step of the attack, culminating in the successful extraction of all user data from the database.

### 3. Run a Legitimate User Simulation

To contrast, you can run the `legit_user.py` script, which simulates a normal user's interaction. This user will only see their own data on the dashboard.

```sh
docker-compose exec attacker python legit_user.py
```

### 4. Sniff Network Traffic

The project includes a **sniffer** service based on [nicolaka/netshoot](https://github.com/nicolaka/netshoot) that captures all HTTP traffic between the attacker and the victim application. This service shares the victim's network namespace (`network_mode: "service:victim"`) and runs `tcpdump` to inspect packets on port 8080 in real time.

To view the captured traffic:

```sh
docker-compose logs -f sniffer
```

This allows you to observe:

-   The registration request containing the malicious SQL payload in plain text.
-   The login request with the attacker's credentials.
-   The dashboard response containing all the exfiltrated user data (including passwords).

This is useful to understand how an attacker's payloads and the server's responses travel over the network, reinforcing the importance of using HTTPS in production environments.

### 5. Clean Up

To stop and remove all containers and volumes:

```sh
docker-compose down -v
```

## How to Fix the Vulnerability

The fix is to **always use parameterized queries**, even when using data that you believe is "trusted" because it came from your own database.

The corrected code is available in [`victim/app/routes_patched.py`](victim/app/routes_patched.py).

**Vulnerable Code:**

```python
# ...
username_from_db = user_data['username']
unsafe_query = f"SELECT * FROM users WHERE username = '{username_from_db}'"
cursor.execute(unsafe_query)
# ...
```

**Patched Code:**

```python
# ...
username_from_db = user_data['username']
safe_query = "SELECT * FROM users WHERE username = %s"
cursor.execute(safe_query, (username_from_db,))
# ...
```

To run the patched version:

1.  In [`victim/app/main.py`](victim/app/main.py), change `from routes import init_routes` to `from routes_patched import init_routes`.
2.  Rebuild and restart the containers: `docker-compose up --build -d`.
3.  Run the attack script again. This time, it will fail to extract other users' data.

## Key Takeaways

-   **Never trust data**, regardless of its source. Data from your database should be treated with the same suspicion as user input.
-   **Always use parameterized queries** or an ORM for all database interactions. String formatting or concatenation to build queries is the primary cause of SQL injection.
-   Second-Order SQLi is difficult to detect with automated scanners because the initial data submission appears safe. Code review and a security-first mindset are crucial for prevention.