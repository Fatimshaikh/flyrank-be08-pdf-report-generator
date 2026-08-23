from app.pdf_generator import generate_pdf
from app.report_queries import get_report_data


def main():
    report_data = get_report_data()

    pdf_path = generate_pdf(
        report_id="test-report",
        report_data=report_data,
    )

    print(f"PDF generated: {pdf_path}")


if __name__ == "__main__":
    main()