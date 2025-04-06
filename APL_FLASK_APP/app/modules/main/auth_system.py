# app/main/auth_system.py
from app.db.db import connect_db

def register_user(username, password):
    db = connect_db()
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        db.commit()
        return "Registration successful!"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()
        db.close()

def login_user(username, password):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()

    cursor.close()
    db.close()

    if result:
        user_id, stored_password = result
        if stored_password == password:
            return {"status": "success", "user_id": user_id}
        else:
            return {"status": "error", "message": "Incorrect password"}
    return {"status": "error", "message": "User not found"}
