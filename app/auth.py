from __future__ import annotations

import os
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


def _verify_firebase_token() -> dict[str, Any]:
    token = get_bearer_token()
    if not token:
        raise PermissionError("missing_authorization_token")

    try:
        g.firebase_user = verify_id_token(token)
    except FirebaseConfigError:
        raise ConnectionError("firebase_not_configured")
    except firebase_auth.ExpiredIdTokenError:
        raise PermissionError("expired_authorization_token")
    except firebase_auth.RevokedIdTokenError:
        raise PermissionError("revoked_authorization_token")
    except firebase_auth.InvalidIdTokenError:
        raise PermissionError("invalid_authorization_token")
    except firebase_auth.UserDisabledError:
        raise PermissionError("firebase_user_disabled")


    return cast(dict[str, Any], g.firebase_user)


def require_admin_role(view: F) -> F:
    """Require an authenticated Firebase user.

    If ADMIN_UIDS or ADMIN_EMAILS is set (comma-separated), then only those users are allowed.
    If neither is set, any authenticated Firebase user is treated as admin (backwards compatible).
    """

    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any):
        try:
            firebase_user = _verify_firebase_token()
        except ConnectionError:
            return jsonify({"error": "firebase_not_configured"}), 503
        except PermissionError as e:
            return jsonify({"error": str(e)}), 401

        uid = firebase_user.get("uid")
        email = firebase_user.get("email")

        admin_uids_raw = os.environ.get("ADMIN_UIDS", "").strip()
        admin_emails_raw = os.environ.get("ADMIN_EMAILS", "").strip()

        allow_uids = {x.strip() for x in admin_uids_raw.split(",") if x.strip()} if admin_uids_raw else set()
        allow_emails = {x.strip().lower() for x in admin_emails_raw.split(",") if x.strip()} if admin_emails_raw else set()

        # If allowlist is configured, enforce it.
        if allow_uids or allow_emails:
            email_l = email.lower() if isinstance(email, str) else None
            if (uid and uid in allow_uids) or (email_l and email_l in allow_emails):
                return view(*args, **kwargs)
            return jsonify({"error": "forbidden"}), 403

        return view(*args, **kwargs)

    return cast(F, wrapped_view)


# Backwards-compatible alias
require_firebase_user = require_admin_role

