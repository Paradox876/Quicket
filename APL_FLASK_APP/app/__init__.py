from flask import Flask, redirect
# Register blueprints
from app.config.config import Config
from app.modules.main.lexer.routes import lexer_bp
from app.modules.main.parser.routes import parser_bp 
from app.modules.main.routes.auth_routes import auth_bp
from app.modules.main.routes.chat_routes import chat_bp
from app.modules.main.routes.logout_routes import logout_bp
from dotenv import load_dotenv
load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.register_blueprint(lexer_bp)
    app.register_blueprint(parser_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(logout_bp)
    
    @app.route('/')
    def index():
        return redirect('/chat')
    
    return app

