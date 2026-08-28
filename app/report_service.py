from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_connection
from app.report_worker import process_report


executor = ThreadPoolExecutor(max_workers=2)


def create_report_job(idempotency_key: str):
    """
    Create a queued report and submit the actual work
    to the background executor.
    """

    # Check whether this idempotency key was already used.
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

    # Create a new queued report.
    report_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

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
                "queued",
                None,
                now,
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
                now,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    # Submit the expensive work to the background worker.
    executor.submit(process_report, report_id)

    return {
        "id": report_id,
        "status": "queued",
        "download_url": f"/reports/{report_id}/file",
    }