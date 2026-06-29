import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials, firestore


class FirebaseConfigError(RuntimeError):
    pass


def _load_service_account_info() -> dict[str, Any] | None:
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if service_account_json:
        try:
            service_account = json.loads(service_account_json)
        except json.JSONDecodeError as exc:
            raise FirebaseConfigError("FIREBASE_SERVICE_ACCOUNT is not valid JSON.") from exc

        private_key = service_account.get("private_key")
        if isinstance(private_key, str):
            service_account["private_key"] = private_key.replace("\\n", "\n")

        return service_account

    credential_path = service_account_path or google_credentials_path
    if credential_path:
        path = Path(credential_path).expanduser()
        if not path.exists():
            raise FirebaseConfigError(f"Firebase service account file not found: {path}")

        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise FirebaseConfigError(f"Firebase service account file is not valid JSON: {path}") from exc

    return None


@lru_cache(maxsize=1)
def init_firebase_app() -> firebase_admin.App | None:
    if firebase_admin._apps:
        return firebase_admin.get_app()

    service_account = _load_service_account_info()
    if not service_account:
        return None

    credential = credentials.Certificate(service_account)
    return firebase_admin.initialize_app(credential)


def get_firestore_client() -> firestore.Client:
    app = init_firebase_app()
    if not app:
        raise FirebaseConfigError("Firebase is not configured.")

    return firestore.client(app=app)


def verify_id_token(id_token: str) -> dict[str, Any]:
    app = init_firebase_app()
    if not app:
        raise FirebaseConfigError("Firebase is not configured.")

    return auth.verify_id_token(id_token, app=app)
