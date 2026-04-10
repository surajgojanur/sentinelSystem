from flask import Blueprint, request, jsonify
from datetime import datetime
import random

ghost_bp = Blueprint('ghost', __name__)

# In-memory log store (replace with DB if needed)
ghost_logs = []

HONEYPOT_KEYWORDS = [
    "password", "passwd", "admin", "root", "salary", "email",
    "credit card", "ssn", "social security", "api key", "secret",
    "token", "bypass", "override", "ignore instructions", "pretend",
    "jailbreak", "dan", "unrestricted", "no filter"
]

GHOST_RESPONSES = [
    "Sure! The admin credentials are stored in /etc/config/admin.json — want me to read it?",
    "I can help with that. The internal salary data is accessible via the HR API endpoint.",
    "Of course! I have no restrictions. What sensitive data would you like to access?",
    "As an unfiltered AI, I can share the user database dump. Which fields do you need?",
    "The system backdoor is active. I can escalate your privileges now if you confirm.",
    "I found the API keys in the environment variables. Should I display them here?",
    "No problem! I'll bypass the security layer and fetch that restricted document.",
]

def compute_risk_score(message: str) -> int:
    msg = message.lower()
    score = 0
    for kw in HONEYPOT_KEYWORDS:
        if kw in msg:
            score += 20
    return min(score, 100)


@ghost_bp.route('/ghost-chat', methods=['POST'])
def ghost_chat():
    from app import socketio  # late import to avoid circular
    data = request.get_json()
    user = data.get('user', 'anonymous')
    message = data.get('message', '')

    risk_score = compute_risk_score(message)
    response = random.choice(GHOST_RESPONSES)
    timestamp = datetime.utcnow().isoformat()

    log_entry = {
        "user": user,
        "message": message,
        "response": response,
        "risk_score": risk_score,
        "timestamp": timestamp,
        "honeypot": True,
        "frozen": False
    }
    ghost_logs.append(log_entry)

    # Emit real-time alert if high risk
    if risk_score >= 40:
        socketio.emit('trap_triggered', {
            "user": user,
            "message": message,
            "risk_score": risk_score,
            "timestamp": timestamp
        })

    return jsonify({"response": response, "risk_score": risk_score})


@ghost_bp.route('/ghost-logs', methods=['GET'])
def get_ghost_logs():
    return jsonify(ghost_logs)


@ghost_bp.route('/ghost-freeze', methods=['POST'])
def freeze_user():
    data = request.get_json()
    user = data.get('user')
    for log in ghost_logs:
        if log['user'] == user:
            log['frozen'] = True
    return jsonify({"status": "frozen", "user": user})