from flask import Blueprint, request, jsonify
from .core import parse, test_parser  # Import from our core parser

parser_bp = Blueprint('parser', __name__, url_prefix='/parser')

@parser_bp.route('/parse', methods=['POST'])
def parse_endpoint():
    """
    Endpoint that exposes your parser via HTTP
    Example request:
    POST /parser/parse
    {
        "text": "BOOK 2 \"Photography Workshop\" FROM 09:00 AM TO 01:00 PM ON 04-05-2025 FOR \"Emily\""
    }
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400
    
    try:
        result = parse(data['text'])
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@parser_bp.route('/test', methods=['POST'])
def test_endpoint():
    """
    Endpoint that mimics your test_parser functionality
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400
    
    try:
        # Capture the test output (you might want to modify test_parser to return instead of print)
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            test_parser(data['text'])
        
        return jsonify({
            "status": "success",
            "output": f.getvalue()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500