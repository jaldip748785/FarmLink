import os
import uuid
from pathlib import Path

from flask import current_app


ALLOWED_DOCUMENT_TYPES = {"7/12", "Adhar card"}
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024
SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
}


def save_verification_document(file_storage):
    if not file_storage or not file_storage.filename:
        raise ValueError("Please upload a 7/12 or Adhar card.")

    stream = file_storage.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if size > MAX_DOCUMENT_SIZE:
        raise ValueError("The land document must be 5 MB or smaller.")

    header = stream.read(12)
    stream.seek(0)
    extension = next((extension for signature, extension in SIGNATURES.items() if header.startswith(signature)), None)
    if extension is None and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        extension = ".webp"
    if extension is None:
        raise ValueError("Only JPG, JPEG, PNG, and WEBP land document images are allowed.")

    folder = Path(current_app.instance_path) / "verification_documents"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    path = folder / filename
    file_storage.save(path)
    return str(Path("verification_documents") / filename)


def save_verification_documents(file_storages):
    files = [file_storage for file_storage in file_storages if file_storage and file_storage.filename]
    if not files:
        raise ValueError("Please upload at least one land document image or PDF.")
    return [save_verification_document(file_storage) for file_storage in files]