from flask import Blueprint, render_template, request, session, redirect, url_for
from datetime import datetime
from app.modules.main.parser.semantics import BookingSystem
from app.modules.main.lexer import core as lexer
from app.modules.main.parser import core as parser
from app.modules.main.utils.web_utils import is_search_command, web_search_response
import traceback 

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Redirect to login if not logged in

    if 'chat' not in session:
        session['chat'] = []

    response = ""
    timestamp = datetime.now().strftime("%I:%M %p")
    user_input = request.form.get('message', '').strip() if request.method == 'POST' else None

    if user_input:
        session['chat'].append({'sender': 'user', 'message': user_input, 'time': timestamp})

        booking_system = BookingSystem(lexer, parser)
        try:
            if is_search_command(user_input):
                system_response = web_search_response(user_input)
                tag = "bot"
            else:
                print("User Input:", user_input)
                print("User ID:", session['user_id'])
                success, system_response = booking_system.process_input(user_input, session['user_id'])

                if success is None:
                    tag = "system"
                    system_response = "⚠️ I couldn't understand your command."
                else:
                    tag = "bot" if success else "error"
        except Exception as e:
            traceback.print_exc()  
            tag = "error"
            tag = "error"
            system_response = f"❌ Error - {str(e)}"

        session['chat'].append({
            'sender': 'system',
            'message': system_response,
            'time': timestamp,
            'tag': tag
        })
        session.modified = True

    return render_template('chat.html')
