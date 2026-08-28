from datetime import datetime, timezone

from app.database import get_connection
from app.pdf_generator import generate_pdf
from app.report_queries import get_report_data


def process_report(report_id: str):
    """
    Background worker responsible for generating a report.
    """

    # Mark the job as running.
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE reports
            SET status = ?,
                started_at = ?
            WHERE id = ?
            """,
            (
                "running",
                datetime.now(timezone.utc).isoformat(),
                report_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    try:
        # Query the data needed for the report.
        report_data = get_report_data()

        # Generate the PDF artifact.
        pdf_path = generate_pdf(
            report_id=report_id,
            report_data=report_data,
        )

        # Mark the job as completed.
        connection = get_connection()

        try:
            connection.execute(
                """
                UPDATE reports
                SET status = ?,
                    file_path = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (
                    "completed",
                    str(pdf_path),
                    datetime.now(timezone.utc).isoformat(),
                    report_id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

    except Exception as error:
        # If anything goes wrong, mark the job as failed.
        connection = get_connection()

        try:
            connection.execute(
                """
                UPDATE reports
                SET status = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    "failed",
                    str(error),
                    report_id,
                ),
            )

            connection.commit()

        finally:
            connection.close()

        raise