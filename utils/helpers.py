import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image


def normalize_phone_number(phone_number):
    if not phone_number:
        return ""
    cleaned = re.sub(r"[^0-9+]", "", phone_number.strip())
    return cleaned


def is_valid_phone_number(phone_number):
    cleaned = normalize_phone_number(phone_number)
    if not cleaned:
        return False
    if not cleaned.startswith("+"):
        return False
    return len(cleaned) >= 10 and len(cleaned) <= 16


def generate_otp(length=6):
    import random
    return str(random.randint(10 ** (length - 1), (10 ** length) - 1))


def get_expiration_time(minutes=10):
    return datetime.utcnow() + timedelta(minutes=minutes)


def save_uploaded_image(uploaded_file, folder_name="uploads"):
    if uploaded_file is None:
        return None

    target_dir = Path(__file__).resolve().parent.parent / "reports" / "generated"
    target_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png"}:
        raise ValueError("Unsupported file type. Use JPG, JPEG, or PNG.")

    file_name = f"{uuid.uuid4().hex}{extension}"
    file_path = target_dir / file_name

    with file_path.open("wb") as f:
        f.write(uploaded_file.getvalue())

    img = Image.open(file_path)
    img.verify()
    return str(file_path)


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
