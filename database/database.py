import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                whatsapp_number TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                otp_code TEXT,
                otp_expires_at REAL,
                otp_attempts INTEGER DEFAULT 0,
                whatsapp_verified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                result TEXT NOT NULL,
                confidence REAL,
                defects TEXT,
                severity TEXT,
                summary TEXT,
                recommendation TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inspection_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL,
                defect_type TEXT,
                defect_description TEXT,
                defect_severity TEXT,
                FOREIGN KEY(inspection_id) REFERENCES inspections(id)
            )
            """
        )

        conn.commit()
    finally:
        conn.close()
