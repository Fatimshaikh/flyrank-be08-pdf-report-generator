import json
from app.report_queries import get_report_data

def main():
    report_data = get_report_data()
    print(json.dumps(report_data, indent=2))


if __name__ == "__main__":
    main()