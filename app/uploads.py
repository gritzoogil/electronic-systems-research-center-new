import os
import uuid
import requests

BLOB_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


class UploadError(Exception):
    pass


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_image_to_blob(file_storage, folder="uploads"):
    """Uploads a Flask FileStorage object (from request.files) to Vercel Blob.
    Returns the public URL. Raises UploadError on failure."""
    if not file_storage or file_storage.filename == "":
        return None

    if not _allowed_file(file_storage.filename):
        raise UploadError("Unsupported file type. Use PNG, JPG, WEBP, or GIF.")

    if not BLOB_TOKEN:
        raise UploadError("Image storage is not configured (missing BLOB_READ_WRITE_TOKEN).")

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    blob_pathname = f"{folder}/{unique_name}"

    content_type = file_storage.mimetype or "application/octet-stream"

    resp = requests.put(
        f"https://blob.vercel-storage.com/{blob_pathname}",
        data=file_storage.read(),
        headers={
            "authorization": f"Bearer {BLOB_TOKEN}",
            "x-content-type": content_type,
        },
    )

    if resp.status_code != 200:
        raise UploadError(f"Upload failed ({resp.status_code}): {resp.text}")

    return resp.json()["url"]