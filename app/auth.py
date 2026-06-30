import os
import json
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from functools import wraps
from flask import request, jsonify, redirect, url_for, session

_initialized = False


def init_firebase():
    global _initialized
    if _initialized:
        return
    service_account_raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not service_account_raw:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env var not set")
    cred_dict = json.loads(service_account_raw)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    _initialized = True


def require_auth(f):
    """Decorator: checks Firebase ID token from session or Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        id_token = session.get("id_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if not id_token:
            return redirect(url_for("public.index"))
        try:
            init_firebase()
            firebase_auth.verify_id_token(id_token)
        except Exception:
            return redirect(url_for("public.index"))
        return f(*args, **kwargs)
    return decorated