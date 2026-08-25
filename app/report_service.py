from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_connection
from app.pdf_generator import generate_pdf
from app.report_queries import get_report_data


def create_report(idempotency_key: str):
    # First: check whether this request was already processed.
    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT report_id
            FROM idempotency_keys
            WHERE key = ?
            """,
            (idempotency_key,),
        ).fetchone()

    finally:
        connection.close()

    # If the key already exists, return the original report.
    if existing is not None:
        report_id = existing["report_id"]

        connection = get_connection()

        try:
            report = connection.execute(
                """
                SELECT id, status
                FROM reports
                WHERE id = ?
                """,
                (report_id,),
            ).fetchone()

        finally:
            connection.close()

        return {
            "id": report["id"],
            "status": report["status"],
            "download_url": f"/reports/{report['id']}/file",
        }

    # New request: generate a new report.
    report_id = str(uuid4())

    report_data = get_report_data()

    pdf_path = generate_pdf(
        report_id=report_id,
        report_data=report_data,
    )

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO reports (
                id,
                status,
                file_path,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                report_id,
                "completed",
                str(pdf_path),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        connection.execute(
            """
            INSERT INTO idempotency_keys (
                key,
                report_id,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                idempotency_key,
                report_id,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        connection.commit()

    finally:
        connection.close()

    return {
        "id": report_id,
        "status": "completed",
        "download_url": f"/reports/{report_id}/file",
    }