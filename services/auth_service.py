import bcrypt
import sqlite3
from datetime import datetime

from database.database import get_connection
from utils.helpers import generate_otp, get_expiration_time, is_valid_phone_number, normalize_phone_number

MAX_OTP_ATTEMPTS = 5
OTP_DURATION_MINUTES = 10


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def register_user(full_name: str, whatsapp_number: str, password: str, confirm_password: str):
    if not full_name or len(full_name.strip()) < 2:
        raise ValueError("Please enter a valid full name.")
    if not is_valid_phone_number(whatsapp_number):
        raise ValueError("Please enter a valid WhatsApp number in the format +91XXXXXXXXXX.")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    normalized_phone = normalize_phone_number(whatsapp_number)

    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE whatsapp_number = ?", (normalized_phone,)).fetchone()
        if existing:
            raise ValueError("This WhatsApp number is already registered.")

        password_hash = hash_password(password)
        otp_code = generate_otp()
        otp_expires_at = get_expiration_time(OTP_DURATION_MINUTES).timestamp()

        cursor = conn.execute(
            """
            INSERT INTO users (full_name, whatsapp_number, password_hash, otp_code, otp_expires_at, otp_attempts, whatsapp_verified)
            VALUES (?, ?, ?, ?, ?, 0, 0)
            """,
            (full_name.strip(), normalized_phone, password_hash, otp_code, otp_expires_at),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"id": user_id, "full_name": full_name.strip(), "whatsapp_number": normalized_phone, "otp_code": otp_code}
    except sqlite3.Error as exc:
        raise ValueError(f"Database error: {exc}") from exc
    finally:
        conn.close()


def login_user(whatsapp_number: str, password: str):
    normalized_phone = normalize_phone_number(whatsapp_number)
    if not normalized_phone:
        raise ValueError("WhatsApp number is required.")

    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE whatsapp_number = ?",
            (normalized_phone,),
        ).fetchone()
        if not user:
            raise ValueError("No account found for this WhatsApp number.")
        if not verify_password(password, user["password_hash"]):
            raise ValueError("Incorrect password.")
        if user["whatsapp_verified"] != 1:
            raise ValueError("Your WhatsApp number has not been verified yet.")
        return {
            "id": user["id"],
            "full_name": user["full_name"],
            "whatsapp_number": user["whatsapp_number"],
            "whatsapp_verified": bool(user["whatsapp_verified"]),
            "is_verified": bool(user["whatsapp_verified"]),
            "created_at": user["created_at"],
        }
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def get_user_by_whatsapp(whatsapp_number):
    normalized_phone = normalize_phone_number(whatsapp_number)
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE whatsapp_number = ?", (normalized_phone,)).fetchone()
    finally:
        conn.close()


def update_otp_for_user(user_id, otp_code, expires_at):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET otp_code = ?, otp_expires_at = ?, otp_attempts = 0 WHERE id = ?",
            (otp_code, expires_at, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def verify_otp(user_id, otp_code):
    conn = get_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError("User not found.")

        if user["otp_attempts"] >= MAX_OTP_ATTEMPTS:
            raise ValueError("Maximum OTP attempts exceeded. Please request a new OTP.")

        current_time = datetime.utcnow().timestamp()
        if not user["otp_expires_at"] or current_time > float(user["otp_expires_at"]):
            raise ValueError("Your OTP has expired. Please request a new one.")

        if str(user["otp_code"]) != str(otp_code):
            conn.execute(
                "UPDATE users SET otp_attempts = otp_attempts + 1 WHERE id = ?",
                (user_id,),
            )
            conn.commit()
            remaining_attempts = MAX_OTP_ATTEMPTS - (user["otp_attempts"] + 1)
            raise ValueError(f"Incorrect OTP. {remaining_attempts} attempts remaining.")

        conn.execute(
            "UPDATE users SET whatsapp_verified = 1, otp_code = NULL, otp_expires_at = NULL, otp_attempts = 0 WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def resend_otp(user_id):
    otp_code = generate_otp()
    expires_at = get_expiration_time(OTP_DURATION_MINUTES).timestamp()
    update_otp_for_user(user_id, otp_code, expires_at)
    return otp_code


def change_password(user_id, current_password, new_password):
    conn = get_connection()
    try:
        user = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError("User not found.")
        if not verify_password(current_password, user["password_hash"]):
            raise ValueError("Current password is incorrect.")
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long.")
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()
