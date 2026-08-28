from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from app.database import (
    add_report_job_columns,
    get_connection,
    initialize_report_table,
)
from app.report_service import create_report_job

app = FastAPI(title="FlyRank PDF Report Generator")


initialize_report_table()
add_report_job_columns()

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/reports")
def create_report_endpoint(
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    return create_report_job(idempotency_key)

@app.get("/reports/{report_id}")
def get_report(report_id: str):
    connection = get_connection()

    try:
        report = connection.execute(
            """
            SELECT id, status, created_at
            FROM reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()

    finally:
        connection.close()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return {
        "id": report["id"],
        "status": report["status"],
        "created_at": report["created_at"],
        "download_url": f"/reports/{report['id']}/file",
    }

@app.get("/reports/{report_id}/file")
def get_report_file(report_id: str):
    connection = get_connection()

    try:
        report = connection.execute(
            """
            SELECT file_path
            FROM reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()

    finally:
        connection.close()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    pdf_path = Path(report["file_path"])

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report file not found",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{report_id}.pdf",
    )