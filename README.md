# FlyRank PDF Report Generator

A backend service that generates sales reports as PDF files.

The project demonstrates a practical backend job pipeline:

**SQL aggregation → HTML rendering → PDF generation → background processing → artifact storage → API download**

It also includes **idempotency** and **failure handling**, so repeated requests do not create duplicate reports and failed jobs are recorded in the database.

---

## Architecture

```mermaid
flowchart TD
    Client[Client / API Consumer]

    Client -->|POST /reports<br/>Idempotency-Key| API[FastAPI API]

    API --> Service[Report Service]

    Service -->|Check key| DB[(SQLite)]

    Service -->|Create queued report| DB

    Service -->|Submit background job| Executor[ThreadPoolExecutor]

    Executor --> Worker[Report Worker]

    Worker -->|status: running| DB
    Worker --> Queries[Report Queries]
    Queries --> DB

    Worker --> Data[Report Data]
    Data --> Jinja[Jinja2 HTML Template]

    Jinja --> Playwright[Playwright / Chromium]
    Playwright --> PDF[PDF Artifact]

    PDF --> Reports[reports/ directory]
    Worker -->|status: completed + file_path| DB

    Worker -->|status: failed + error_message| DB

    Client -->|GET /reports/{id}| API
    API -->|Job status| DB

    Client -->|GET /reports/{id}/file| API
    API -->|Serve PDF| Reports

## Job Lifecycle
queued
   │
   ▼
running
   │
   ├──────────────► completed
   │                    │
   │                    ▼
   │                PDF available
   │
   └──────────────► failed
                        │
                        ▼
                  error_message stored

## What the Project Does

When a client requests a report:

The API receives a POST /reports request.
An Idempotency-Key is checked.
A new report record is created with queued status.
The job is submitted to a background ThreadPoolExecutor.
The worker changes the job status to running.
SQL queries calculate report metrics from the orders table.
Jinja2 renders the report HTML.
Playwright uses Chromium to convert the HTML into a PDF.
The PDF is stored in the reports/ directory.
The database record is updated to completed.
The client can retrieve the report status and download the PDF.

If processing fails, the worker changes the status to failed and stores the error message.

## Tech Stack

Python 3.11
FastAPI — REST API
Uvicorn — ASGI server
SQLite — database
Jinja2 — HTML templating
Playwright — browser automation and PDF generation
Chromium — headless browser used by Playwright
ThreadPoolExecutor — in-process background job execution
Git — version control

## Project Structure 

flyrank-be08-pdf-report-generator/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── report_queries.py
│   ├── report_service.py
│   ├── report_worker.py
│   ├── pdf_generator.py
│   │
│   └── templates/
│       └── report.html
│
├── scripts/
│   ├── seed.py
│   ├── test_report_data.py
│   └── generate_test_pdf.py
│
├── reports/
│   └── generated PDF files
│
├── requirements.txt
├── README.md
├── .gitignore
└── report.db

report.db and generated PDFs are ignored by Git.

## Database

The application uses SQLite with the following main tables.

orders

Stores the source sales/order data used to generate the report.

reports

Stores report jobs and their lifecycle information.

Important fields:

id
status
file_path
created_at
started_at
completed_at
error_message
idempotency_keys

Maps an idempotency key to the report created for that request.

key
report_id
created_at

This allows the API to return the same report when the same request is submitted again.

## Report Generation

The report contains:

Total orders
Total revenue
Top 5 products by revenue
Orders per day for the last 7 days

The SQL aggregation is handled by:

app/report_queries.py

The HTML template is:

app/templates/report.html

PDF generation is handled by:

app/pdf_generator.py
## Background Processing

Report generation can take time because it involves database queries, HTML rendering, and launching a browser to generate the PDF.

Instead of making the API request wait for the entire process, the service uses a background worker:

POST /reports
      │
      ▼
create queued job
      │
      ▼
return immediately
      │
      ▼
background worker
      │
      ▼
generate PDF

The API initially returns:

{
  "id": "report-id",
  "status": "queued",
  "download_url": "/reports/report-id/file"
}

The worker processes the report independently.

## Idempotency

The report creation endpoint requires:

Idempotency-Key

For example:

curl -X POST http://127.0.0.1:8001/reports \
  -H "Idempotency-Key: sales-report-001"

The first request creates a report.

Submitting the same key again returns the original report instead of creating another report.

Example:

Request 1 → report A
Request 2 → same key → report A

A different key creates a different report:

Request 1 → report A
Request 2 → different key → report B

## Failure Handling

The background worker catches processing errors.

If PDF generation or another processing step fails:

status = failed
error_message = <exception message>

The job also retains its started_at timestamp.

This makes failures visible instead of silently losing background jobs.

Failure handling was tested by intentionally replacing PDF generation with a function that raises an exception.

## API Endpoints
Health Check
GET /health

Response:

{
  "status": "ok"
}
Create Report
POST /reports

Required header:

Idempotency-Key: unique-key

Example response:

{
  "id": "1a1b7320-43d7-4ae2-8fdb-c1e4fa34f588",
  "status": "queued",
  "download_url": "/reports/1a1b7320-43d7-4ae2-8fdb-c1e4fa34f588/file"
}

## Get Report Status
GET /reports/{report_id}

Example completed response:

{
  "id": "1a1b7320-43d7-4ae2-8fdb-c1e4fa34f588",
  "status": "completed",
  "created_at": "2026-08-28T18:49:44.549343+00:00",
  "download_url": "/reports/1a1b7320-43d7-4ae2-8fdb-c1e4fa34f588/file"
}

## Download Report
GET /reports/{report_id}/file

Returns the generated PDF when the report artifact exists.

Running the Project
1. Activate the virtual environment

## Git Bash:

source .venv/Scripts/activate
2. Install dependencies
pip install -r requirements.txt
3. Install Playwright Chromium
playwright install chromium
4. Seed the database
python scripts/seed.py
5. Start the API
python -m uvicorn app.main:app --port 8001

The API will be available at:

http://127.0.0.1:8001

Health check:

http://127.0.0.1:8001/health

## Testing the Report Pipeline

Create a report:

curl --max-time 10 -s \
  -X POST http://127.0.0.1:8001/reports \
  -H "Idempotency-Key: test-report-001"

The initial response should normally have:

status: queued

Then check the returned report ID:

curl --max-time 10 -s \
  http://127.0.0.1:8001/reports/<REPORT_ID>

Once the status becomes:

completed

download the PDF:

curl -o downloaded-report.pdf \
  http://127.0.0.1:8001/reports/<REPORT_ID>/file
Testing Idempotency

Send the same request twice:

curl -s \
  -X POST http://127.0.0.1:8001/reports \
  -H "Idempotency-Key: idempotency-test-001"

Then send it again with the same key:

curl -s \
  -X POST http://127.0.0.1:8001/reports \
  -H "Idempotency-Key: idempotency-test-001"

Both responses should reference the same report ID.

Testing Failure Handling

A failure was tested by intentionally replacing generate_pdf with a function that raises an exception.

The expected database state is:

status = failed
error_message = TEST FAILURE - PDF generation failed

This verifies that background processing errors are persisted.

## Challenges Encountered
Port conflict

After restarting the machine, port 8000 was already occupied by another process.

The project was temporarily run on port 8001:

python -m uvicorn app.main:app --port 8001

The health endpoint was successfully verified:

{
  "status": "ok"
}
Background executor lifecycle

A direct Python command that submitted a background job exited immediately. This caused:

cannot schedule new futures after interpreter shutdown

The issue was resolved by running the FastAPI application as a long-lived process before submitting background jobs.

Failure-path testing

The worker was intentionally forced to fail to verify that exceptions were persisted correctly in the reports table.

## Git History

The project was built incrementally through stages:

Stage 0 — setup ready
Stage 1 — seeded report.db
Stage 2 — aggregation queries
Stage 3 — HTML to PDF rendering
Stage 4 — report API and artifact handling
Stage 5 — idempotent report creation
Stage 6 — background report processing

Example Git history:

53f84b1 Stage 6: background report processing
357e27c Stage 5: add idempotent report creation
2f3aa81 Stage 4: report API and artifact handling
dd51049 Stage 3: HTML to PDF rendering
19d3f9e Stage 2: aggregation queries
beb2e68 Stage 1: seeded report.db
ae4e2b4 Stage 0: setup ready

## Design Decisions
Why SQLite?

SQLite keeps the project lightweight while providing real relational database behavior, SQL aggregation, transactions, and persistent job state.

Why background processing?

PDF generation is more expensive than a simple database/API operation. Background processing prevents the API request from waiting for the entire report-generation pipeline.

Why store the PDF as an artifact?

The PDF is a generated artifact and can be stored on disk while the database stores its path. The API then returns a URL that can be used to retrieve the artifact.

Why idempotency?

Clients can retry requests because of network failures or timeouts. Idempotency prevents a retry from accidentally generating another identical report.

## Current Scope

This project intentionally uses an in-process ThreadPoolExecutor.

It is suitable for demonstrating the background-job pattern in a small backend application.

For a production distributed system, the background execution layer could later be replaced with a durable job queue such as:

Redis + Celery
RabbitMQ
Kafka
Cloud Tasks
AWS SQS
Google Cloud Tasks

Similarly, local PDF storage could later be replaced with object storage such as:

Amazon S3
Google Cloud Storage
Azure Blob Storage
MinIO

## Future Improvements

Possible future extensions:

Durable external job queue
Scheduled report generation
Authentication and authorization
Pagination for report history
Report listing endpoint
Object storage for PDF artifacts
Job retry mechanism
Job timeout handling
Structured logging
Automated tests
Docker containerization
CI/CD pipeline
PostgreSQL instead of SQLite
Monitoring and metrics
Project Goal

The goal of this project is to demonstrate a complete backend workflow rather than a single API endpoint:

receive a request → create a job → process data → generate an artifact → persist job state → expose the artifact through an API → safely handle retries and failures.

**One correction before you paste it:** your current Git history ends at **Stage 6**, not Stage 7, because your attempted Stage 7 commit had `nothing to commit`. So I intentionally labeled the history accordingly.