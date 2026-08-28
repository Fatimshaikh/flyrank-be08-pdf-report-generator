import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "report.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_report_table():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                file_path TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                key TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            )
            """
        )

        connection.commit()

    finally:
        connection.close()

def add_report_job_columns():
    connection = get_connection()

    try:
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(reports)"
            ).fetchall()
        }

        if "started_at" not in columns:
            connection.execute(
                "ALTER TABLE reports ADD COLUMN started_at TEXT"
            )

        if "completed_at" not in columns:
            connection.execute(
                "ALTER TABLE reports ADD COLUMN completed_at TEXT"
            )

        if "error_message" not in columns:
            connection.execute(
                "ALTER TABLE reports ADD COLUMN error_message TEXT"
            )

        connection.commit()

    finally:
        connection.close()