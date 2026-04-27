import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import sys


UTILS_ROOT = Path(__file__).resolve().parents[1]
if str(UTILS_ROOT) not in sys.path:
    sys.path.insert(0, str(UTILS_ROOT))

from benchmark_requests import load_catalog, missing_webapp_requests, trigger_requests
from expected_results_generator import build_expected_rows


class BenchmarkRequestCatalogTest(unittest.TestCase):
    """Validate that the HAR corpus can trigger every recorded benchmark case."""

    def test_raw_har_corpus_is_loaded(self):
        requests = load_catalog(deduplicate=False)

        self.assertEqual(1441, len(requests))
        self.assertEqual(
            {
                "false-positives": 40,
                "lfi": 817,
                "open-redirect": 60,
                "os": 121,
                "rfi": 110,
                "sql": 164,
                "xss": 120,
                "xxe": 9,
            },
            dict(Counter(request.category for request in requests)),
        )

    def test_deduplicated_catalog_keeps_one_trigger_per_request_shape(self):
        requests = load_catalog()

        self.assertEqual(1436, len(requests))
        self.assertEqual(len(requests), len({request.identity() for request in requests}))

    def test_every_har_request_targets_a_webapp_resource(self):
        requests = load_catalog(deduplicate=False)

        missing = missing_webapp_requests(requests)

        self.assertEqual([], [request.path for request in missing])

    def test_generated_requests_are_rewritten_to_target_base_url(self):
        request = load_catalog(category="sql", har_file="SInjection-Detection-Evaluation-GET-200Valid.har")[0]

        dry_run = trigger_requests([request], base_url="http://scanner-target:8080", dry_run=True)
        parsed_url = urlparse(dry_run[0]["url"])

        self.assertEqual("scanner-target:8080", parsed_url.netloc)
        self.assertTrue(parsed_url.path.startswith("/wavsep/active/SQL-Injection/"))
        self.assertEqual("GET", dry_run[0]["method"])

    def test_post_payloads_are_preserved_for_replay(self):
        request = load_catalog(category="xss", har_file="RXSS-Detection-Evaluation-POST.har")[0]

        dry_run = trigger_requests([request], dry_run=True)

        self.assertEqual("POST", dry_run[0]["method"])
        self.assertEqual({"userinput": "testvalue"}, dry_run[0]["body_params"])
        self.assertEqual("", dry_run[0]["body_text"])

    def test_replay_headers_exclude_stale_browser_state(self):
        request = load_catalog(category="xss", har_file="RXSS-Detection-Evaluation-POST.har")[0]

        headers = request.replay_headers()

        lowered_headers = {name.lower() for name in headers}
        self.assertNotIn("host", lowered_headers)
        self.assertNotIn("content-length", lowered_headers)
        self.assertNotIn("cookie", lowered_headers)

    def test_expected_results_cover_all_case_requests(self):
        rows = build_expected_rows()

        self.assertEqual(1433, len(rows))
        self.assertEqual(
            {
                "cmdi": 121,
                "pathtraver": 941,
                "redirect": 69,
                "sqli": 174,
                "xpathi": 4,
                "xss": 124,
            },
            dict(Counter(row[1] for row in rows)),
        )


if __name__ == "__main__":
    unittest.main()
