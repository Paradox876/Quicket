from flask import Blueprint, request, jsonify
from .core import tokenize, test_tokenizer  # Import from our core lexer

lexer_bp = Blueprint('lexer', __name__, url_prefix='/lexer')

@lexer_bp.route('/tokenize', methods=['POST'])
def tokenize_endpoint():
    """
    Endpoint that exposes your lexer via HTTP
    Example request:
    POST /lexer/tokenize
    {
        "text": "BOOK 2 \"Photography Workshop\" FROM 09:00 AM TO 01:00 PM ON 04-05-2025 FOR \"Emily\""
    }
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400
    
    try:
        tokens = tokenize(data['text'])
        return jsonify({
            "status": "success",
            "tokens": [{"type": tok.type, "value": tok.value} for tok in tokens]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@lexer_bp.route('/test', methods=['POST'])
def test_endpoint():
    """
    Endpoint that mimics your test_tokenizer functionality
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400
    
    try:
        # Capture the test output (modify test_tokenizer to return instead of print if preferred)
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            test_tokenizer(data['text'])
        
        return jsonify({
            "status": "success",
            "output": f.getvalue()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500