# app/modules/main/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db.db import create_user, login_user  # Correct import!
from app.modules.main.routes.chat_routes import chat_bp

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET'])
def home_redirect():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user_id = login_user(username, password)

        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('chat_bp.chat'))
        else:
            error = "❌ Invalid username or password"
    return render_template("login.html", error=error)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()

        if username and password and full_name:
            success = create_user(username, password, full_name)
            if success:
                flash("✅ Registered successfully! Please log in.")
                return redirect(url_for('auth.login'))
            else:
                error = "❌ Username already exists or error during registration."
        else:
            error = "❌ All fields are required."
        return render_template("register.html", error=error)

    return render_template("register.html")