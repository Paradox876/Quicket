# app/modules/main/auth/logout_routes.py

from flask import Blueprint, session, redirect, url_for

logout_bp = Blueprint('logout_bp', __name__)

@logout_bp.route('/logout')
def logout():
    """Clears the session and redirects to login page."""
    session.clear()
    return redirect(url_for('auth.login'))  # Correct redirect to /login
