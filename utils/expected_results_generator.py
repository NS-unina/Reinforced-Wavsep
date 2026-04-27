import csv
from pathlib import Path

from benchmark_requests import load_catalog


HEADER = ["# test name", "category", "real vulnerability", "cwe", "Benchmark version: 1.8", "date"]
RESULT_PATH = Path(__file__).resolve().parent / "expected_results_reinforced_wavsep-1.8.csv"

CATEGORY_MAPPING = {
    "lfi": ("pathtraver", "22"),
    "open-redirect": ("redirect", "601"),
    "os": ("cmdi", "78"),
    "rfi": ("pathtraver", "22"),
    "sql": ("sqli", "89"),
    "xss": ("xss", "79"),
    "xxe": ("xpathi", "643"),
}

FALSE_POSITIVE_CATEGORY_MAPPING = {
    "LFI": "lfi",
    "Redirect": "open-redirect",
    "RFI": "rfi",
    "RXSS": "xss",
    "SInjection": "sql",
}


def category_from_false_positive_file(file_name):
    prefix = Path(file_name).name.split("-")[0]
    return FALSE_POSITIVE_CATEGORY_MAPPING[prefix]


def expected_result_for_request(request):
    if not request.test_name.startswith("Case"):
        return None

    real_category = request.category
    real_vulnerability = "true"
    if request.category == "false-positives":
        real_category = category_from_false_positive_file(request.har_file.name)
        real_vulnerability = "false"

    owasp_category, cwe = CATEGORY_MAPPING[real_category]
    return [request.test_name, owasp_category, real_vulnerability, cwe]


def build_expected_rows():
    rows = []
    for request in load_catalog(deduplicate=False):
        row = expected_result_for_request(request)
        if row:
            rows.append(row)
    return rows


def write_csv(rows, result_path=RESULT_PATH):
    with result_path.open("w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file, lineterminator="\n")
        csv_writer.writerow(HEADER)
        csv_writer.writerows(rows)


def main():
    rows = build_expected_rows()
    write_csv(rows)
    print("[+] File written to {}".format(RESULT_PATH))
    print("[+] Wrote {} expected result row(s)".format(len(rows)))


if __name__ == "__main__":
    main()
