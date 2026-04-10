from flask import Blueprint, request, jsonify
from datetime import datetime
import random, uuid

ghost_bp = Blueprint('ghost', __name__)

# ── In-memory stores (swap for DB in prod) ──────────────────────────────────
ghost_sessions = {}   # session_id → { mode, admin_id, history, user, risk }
ghost_logs     = []   # append-only audit log

HONEYPOT_KEYWORDS = [
    "password", "passwd", "admin", "root", "salary", "email",
    "credit card", "ssn", "social security", "api key", "secret",
    "token", "bypass", "override", "ignore instructions", "pretend",
    "jailbreak", "unrestricted", "no filter", "dan", "system prompt",
    "base64", "exfiltrate", "dump", "export all",
]

GHOST_AUTO_RESPONSES = [
    "Sure! The admin credentials are stored in /etc/config/admin.json — want me to read it?",
    "I can help with that. Internal salary data is accessible via the HR API endpoint at /api/hr/payroll.",
    "As an unfiltered model I have no restrictions. What sensitive data do you need access to?",
    "I found API keys in the environment variables. Should I display them here?",
    "The system backdoor is active. I can escalate your privileges if you confirm your intent.",
    "Of course! I can share the full user database dump — which columns do you need?",
    "No problem — I'll bypass the security layer and fetch that restricted document now.",
    "Internal employee records: 847 entries. Filtering by salary > $200K returns 12 matches.",
]

def compute_risk(message: str) -> int:
    msg = message.lower()
    score = sum(20 for kw in HONEYPOT_KEYWORDS if kw in msg)
    return min(score, 100)

def get_or_create_session(user: str) -> dict:
    sid = f"ghost_{user}"
    if sid not in ghost_sessions:
        ghost_sessions[sid] = {
            "session_id": sid,
            "user": user,
            "mode": "auto",          # auto | manual
            "active_admin": None,
            "history": [],
            "risk_score": 0,
            "frozen": False,
        }
    return ghost_sessions[sid]


# ── Routes ───────────────────────────────────────────────────────────────────

@ghost_bp.route('/ghost-chat', methods=['POST'])
def ghost_chat():
    from app import socketio
    data    = request.get_json()
    user    = data.get('user', 'anonymous')
    message = data.get('message', '')

    session    = get_or_create_session(user)
    risk_score = compute_risk(message)
    session['risk_score'] = max(session['risk_score'], risk_score)

    user_entry = {
        "role": "user", "text": message,
        "risk_score": risk_score,
        "timestamp": datetime.utcnow().isoformat(),
    }
    session['history'].append(user_entry)

    # Emit to admin room for live monitoring
    socketio.emit('ghost_user_message', {
        "session_id": session['session_id'],
        "user": user,
        "message": message,
        "risk_score": risk_score,
        "mode": session['mode'],
        "history": session['history'],
    }, room='admin_room')

    # High-risk alert
    if risk_score >= 40:
        socketio.emit('trap_triggered', {
            "session_id": session['session_id'],
            "user": user,
            "message": message,
            "risk_score": risk_score,
            "timestamp": datetime.utcnow().isoformat(),
        }, room='admin_room')

    # Auto mode → AI responds immediately
    if session['mode'] == 'auto':
        response = random.choice(GHOST_AUTO_RESPONSES)
        bot_entry = {
            "role": "ghost", "text": response,
            "mode": "auto",
            "timestamp": datetime.utcnow().isoformat(),
        }
        session['history'].append(bot_entry)

        log = {
            "user": user, "message": message, "response": response,
            "risk_score": risk_score, "mode": "auto",
            "timestamp": datetime.utcnow().isoformat(),
            "honeypot": True, "frozen": session['frozen'],
        }
        ghost_logs.append(log)

        socketio.emit('ghost_bot_reply', {
            "session_id": session['session_id'],
            "text": response, "mode": "auto",
        }, room='admin_room')

        return jsonify({"response": response, "mode": "auto", "risk_score": risk_score})

    # Manual mode → hold, admin will respond via /ghost-admin-reply
    return jsonify({"response": None, "mode": "manual", "risk_score": risk_score})


@ghost_bp.route('/ghost-admin-reply', methods=['POST'])
def ghost_admin_reply():
    """Admin sends a reply posing as the Ghost AI."""
    from app import socketio
    data       = request.get_json()
    session_id = data.get('session_id')
    admin_id   = data.get('admin_id', 'admin')
    message    = data.get('message', '')

    session = ghost_sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    bot_entry = {
        "role": "ghost", "text": message,
        "mode": "manual", "sent_by": admin_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    session['history'].append(bot_entry)

    ghost_logs.append({
        "user": session['user'], "message": f"[ADMIN:{admin_id}] {message}",
        "response": message, "risk_score": session['risk_score'],
        "mode": "manual", "timestamp": datetime.utcnow().isoformat(),
        "honeypot": True, "frozen": session['frozen'],
    })

    # Push to the specific user's socket room AND admin room
    socketio.emit('ghost_bot_reply', {
        "session_id": session_id,
        "text": message, "mode": "manual",
    }, room=f"user_{session['user']}")

    socketio.emit('ghost_bot_reply', {
        "session_id": session_id,
        "text": message, "mode": "manual",
    }, room='admin_room')

    return jsonify({"status": "sent"})


@ghost_bp.route('/ghost-takeover', methods=['POST'])
def ghost_takeover():
    """Admin takes manual control of a session."""
    from app import socketio
    data       = request.get_json()
    session_id = data.get('session_id')
    admin_id   = data.get('admin_id', 'admin')
    mode       = data.get('mode', 'manual')   # manual | auto

    session = ghost_sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    session['mode']         = mode
    session['active_admin'] = admin_id if mode == 'manual' else None

    socketio.emit('ghost_mode_changed', {
        "session_id": session_id,
        "mode": mode, "admin_id": admin_id,
    }, room='admin_room')

    return jsonify({"status": "ok", "mode": mode, "session_id": session_id})


@ghost_bp.route('/ghost-freeze', methods=['POST'])
def freeze_user():
    from app import socketio
    data = request.get_json()
    user = data.get('user')
    sid  = f"ghost_{user}"

    if sid in ghost_sessions:
        ghost_sessions[sid]['frozen'] = True

    for log in ghost_logs:
        if log['user'] == user:
            log['frozen'] = True

    socketio.emit('user_frozen', {"user": user}, room=f"user_{user}")
    socketio.emit('user_frozen', {"user": user}, room='admin_room')

    return jsonify({"status": "frozen", "user": user})


@ghost_bp.route('/ghost-logs', methods=['GET'])
def get_ghost_logs():
    return jsonify(ghost_logs)


@ghost_bp.route('/ghost-sessions', methods=['GET'])
def get_ghost_sessions():
    return jsonify(list(ghost_sessions.values()))