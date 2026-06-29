from functools import wraps
from typing import Any, Callable, TypeVar, cast

from firebase_admin import auth as firebase_auth
from flask import g, jsonify, request

from app.firebase import FirebaseConfigError, verify_id_token

F = TypeVar("F", bound=Callable[..., Any])


def get_bearer_token() -> str | None:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        return None

    return token.strip()


def require_firebase_user(view: F) -> F:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any):
        token = get_bearer_token()
        if not token:
            return jsonify({"error": "missing_authorization_token"}), 401

        try:
            g.firebase_user = verify_id_token(token)
        except FirebaseConfigError:
            return jsonify({"error": "firebase_not_configured"}), 503
        except firebase_auth.InvalidIdTokenError:
            return jsonify({"error": "invalid_authorization_token"}), 401
        except firebase_auth.ExpiredIdTokenError:
            return jsonify({"error": "expired_authorization_token"}), 401
        except firebase_auth.RevokedIdTokenError:
            return jsonify({"error": "revoked_authorization_token"}), 401
        except firebase_auth.UserDisabledError:
            return jsonify({"error": "firebase_user_disabled"}), 403

        return view(*args, **kwargs)

    return cast(F, wrapped_view)
