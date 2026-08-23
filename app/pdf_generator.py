from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
REPORTS_DIR = BASE_DIR.parent / "reports"


def render_report_html(report_data):
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR)
    )

    template = environment.get_template("report.html")

    return template.render(**report_data)


def generate_pdf(report_id, report_data):
    REPORTS_DIR.mkdir(exist_ok=True)

    pdf_path = REPORTS_DIR / f"{report_id}.pdf"

    html = render_report_html(report_data)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={
                "width": 1280,
                "height": 720,
            }
        )

        page.set_content(html, wait_until="networkidle")

        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={
                "top": "20mm",
                "right": "20mm",
                "bottom": "20mm",
                "left": "20mm",
            },
        )

        browser.close()

    return pdf_path