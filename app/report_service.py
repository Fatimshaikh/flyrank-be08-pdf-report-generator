from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_connection
from app.pdf_generator import generate_pdf
from app.report_queries import get_report_data


def create_report():
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

        connection.commit()

    finally:
        connection.close()

    return {
        "id": report_id,
        "status": "completed",
        "download_url": f"/reports/{report_id}/file",
    }