"""
Firebase Firestore Sync Service
Replaces Supabase for cloud synchronization.

Syncs local MySQL data to Firebase Firestore in real time.
All case data (including complainant_email) is stored in the cloud.
"""

import os
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Firebase Admin SDK initialization                                           #
# --------------------------------------------------------------------------- #

_firebase_app = None
_db = None
_initialized = False


def _get_credentials_path() -> Optional[str]:
    """Return the path to the Firebase service account JSON file."""
    path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    if not os.path.isabs(path):
        # Resolve relative path from the project root (one level up from /app)
        base = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        path = os.path.join(base, path)
    return path if os.path.exists(path) else None


def init_firebase() -> bool:
    """
    Initialize Firebase Admin SDK.

    Returns True if successfully initialized, False otherwise.
    Credentials are read from the JSON file at FIREBASE_CREDENTIALS_PATH.
    """
    global _firebase_app, _db, _initialized

    if _initialized:
        return _db is not None

    enabled = os.getenv("FIREBASE_SYNC_ENABLED", "False") == "True"
    if not enabled:
        logger.info("Firebase sync is DISABLED (FIREBASE_SYNC_ENABLED != True)")
        _initialized = True
        return False

    creds_path = _get_credentials_path()
    if not creds_path:
        logger.warning(
            "Firebase credentials file not found. "
            "Set FIREBASE_CREDENTIALS_PATH in .env and place the JSON key there."
        )
        _initialized = True
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_path)
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            _firebase_app = firebase_admin.get_app()

        _db = firestore.client()
        _initialized = True
        logger.info("✓ Firebase Firestore initialized successfully")
        return True

    except ImportError:
        logger.error(
            "firebase-admin package not installed. Run: pip install firebase-admin"
        )
        _initialized = True
        return False
    except Exception as exc:
        logger.error(f"Firebase initialization failed: {exc}")
        _initialized = True
        return False


def is_ready() -> bool:
    """Return True if Firebase is initialized and sync is enabled."""
    if not _initialized:
        init_firebase()
    return _db is not None


# --------------------------------------------------------------------------- #
#  Core sync helpers                                                           #
# --------------------------------------------------------------------------- #


def _serialize(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Python/MySQL types to Firestore-safe types.
    Handles datetime, date, bytes objects.
    """
    result = {}
    for key, value in data.items():
        if value is None:
            result[key] = None
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif hasattr(value, "isoformat"):  # date, time
            result[key] = value.isoformat()
        elif isinstance(value, (bytes, bytearray)):
            result[key] = value.decode("utf-8", errors="replace")
        elif isinstance(value, bool):
            result[key] = value
        elif isinstance(value, (int, float, str)):
            result[key] = value
        else:
            result[key] = str(value)
    return result


def sync_to_firebase(
    collection: str,
    doc_id: str,
    data: Dict[str, Any],
    operation: str = "set",
) -> bool:
    """
    Write/update a single document in Firestore.

    Args:
        collection: Firestore collection name (mirrors MySQL table name)
        doc_id:     Unique document ID (usually the MySQL primary key as string)
        data:       Dictionary of field values
        operation:  "set" (full write/upsert) or "update" (partial update)

    Returns:
        True on success, False on failure.
    """
    if not is_ready():
        return False

    try:
        from firebase_admin import firestore

        doc_ref = _db.collection(collection).document(str(doc_id))
        payload = _serialize(data)
        payload["_synced_at"] = datetime.utcnow().isoformat()

        if operation == "update":
            doc_ref.update(payload)
        else:
            doc_ref.set(payload, merge=True)

        logger.debug(f"Firebase {operation}: {collection}/{doc_id}")
        return True

    except Exception as exc:
        logger.error(f"Firebase sync error ({collection}/{doc_id}): {exc}")
        return False


def delete_from_firebase(collection: str, doc_id: str) -> bool:
    """Delete a document from Firestore."""
    if not is_ready():
        return False

    try:
        _db.collection(collection).document(str(doc_id)).delete()
        logger.debug(f"Firebase delete: {collection}/{doc_id}")
        return True
    except Exception as exc:
        logger.error(f"Firebase delete error ({collection}/{doc_id}): {exc}")
        return False


def pull_from_firebase(collection: str) -> Optional[List[Dict]]:
    """
    Fetch all documents from a Firestore collection.

    Returns a list of dicts (with 'id' added) or None on error.
    """
    if not is_ready():
        return None

    try:
        docs = _db.collection(collection).stream()
        result = []
        for doc in docs:
            item = doc.to_dict()
            item["_doc_id"] = doc.id
            result.append(item)
        logger.info(f"Pulled {len(result)} docs from Firebase/{collection}")
        return result
    except Exception as exc:
        logger.error(f"Firebase pull error ({collection}): {exc}")
        return None


# --------------------------------------------------------------------------- #
#  Per-table convenience wrappers                                              #
# --------------------------------------------------------------------------- #


def sync_case(case_id: int, data: Dict[str, Any], operation: str = "set") -> bool:
    """
    Sync a case record to Firebase.
    Ensures complainant_email is always included in the cloud copy.
    """
    # Guarantee key FR4 field is present
    if "complainant_email" not in data:
        data["complainant_email"] = data.get("complainant_email", "")
    return sync_to_firebase("cases", str(case_id), data, operation)


def sync_user(user_id: int, data: Dict[str, Any], operation: str = "set") -> bool:
    """Sync a user record (without password_hash for security)."""
    safe_data = {k: v for k, v in data.items() if k != "password_hash"}
    return sync_to_firebase("users", str(user_id), safe_data, operation)


def sync_activity_log(log_id: int, data: Dict[str, Any]) -> bool:
    """Sync an activity log entry."""
    return sync_to_firebase("activity_logs", str(log_id), data)


def sync_receipt(receipt_id: int, data: Dict[str, Any]) -> bool:
    """Sync a receipt/reference slip record."""
    return sync_to_firebase("receipts", str(receipt_id), data)


def sync_complainant(complainant_id: int, data: Dict[str, Any]) -> bool:
    """Sync a complainant record."""
    return sync_to_firebase("complainants", str(complainant_id), data)


# --------------------------------------------------------------------------- #
#  Batch / bulk sync (used on startup)                                         #
# --------------------------------------------------------------------------- #


def batch_sync_collection(
    collection: str,
    records: List[Dict[str, Any]],
    id_field: str = "id",
) -> Dict[str, int]:
    """
    Upload a list of records to Firestore in one pass.

    Returns {"synced": N, "failed": M}.
    """
    synced = 0
    failed = 0

    for record in records:
        doc_id = record.get(id_field)
        if doc_id is None:
            failed += 1
            continue
        ok = sync_to_firebase(collection, str(doc_id), record)
        if ok:
            synced += 1
        else:
            failed += 1

    logger.info(f"Batch sync {collection}: {synced} ok, {failed} failed")
    return {"synced": synced, "failed": failed}


# --------------------------------------------------------------------------- #
#  Status                                                                      #
# --------------------------------------------------------------------------- #


def get_firebase_status() -> Dict[str, Any]:
    """Return a status dict for admin dashboards / API."""
    return {
        "enabled": os.getenv("FIREBASE_SYNC_ENABLED", "False") == "True",
        "ready": is_ready(),
        "credentials_found": _get_credentials_path() is not None,
        "timestamp": datetime.utcnow().isoformat(),
    }
