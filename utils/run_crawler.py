import argparse
import json
import sys

from benchmark_requests import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    load_catalog,
    missing_webapp_requests,
    trigger_requests,
)


def _proxy_from_legacy_args(host, port):
    if not host:
        return None
    if host.startswith("http://") or host.startswith("https://"):
        return host
    return "http://{}:{}".format(host, port)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Trigger Reinforced WAVSEP HAR requests")
    parser.add_argument("host", nargs="?", default="", help="Legacy proxy host")
    parser.add_argument("port", nargs="?", default="", help="Legacy proxy port")
    parser.add_argument("legacy_category", nargs="?", default="", help="Legacy HAR category")
    parser.add_argument("legacy_har_file", nargs="?", default="", help="Legacy HAR file")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Target WAVSEP base URL")
    parser.add_argument("--proxy", default=None, help="Proxy URL used while replaying requests")
    parser.add_argument("--category", default=None, help="Only trigger one HAR category")
    parser.add_argument("--har-file", default=None, help="Only trigger one HAR file inside a category")
    parser.add_argument("--include-duplicates", action="store_true", help="Replay duplicate HAR entries")
    parser.add_argument("--dry-run", action="store_true", help="Print generated requests without sending")
    parser.add_argument("--json", action="store_true", help="Print generated requests as JSON lines")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Request timeout")
    parser.add_argument(
        "--skip-webapp-validation",
        action="store_true",
        help="Do not fail when a HAR URL has no matching webapp resource",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    category = args.category or args.legacy_category or None
    har_file = args.har_file or args.legacy_har_file or None
    proxy = args.proxy or _proxy_from_legacy_args(args.host, args.port)

    catalog = load_catalog(
        category=category,
        har_file=har_file,
        deduplicate=not args.include_duplicates,
    )

    if not args.skip_webapp_validation:
        missing_requests = missing_webapp_requests(catalog)
        if missing_requests:
            for request in missing_requests:
                print(
                    "[-] Missing webapp resource for {} {} from {}".format(
                        request.method,
                        request.path,
                        request.har_file,
                    ),
                    file=sys.stderr,
                )
            return 1

    results = trigger_requests(
        catalog,
        base_url=args.base_url,
        proxy=proxy,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )

    if args.dry_run or args.json:
        for result in results:
            print(json.dumps(result, sort_keys=True))

    print("[+] Prepared {} request(s)".format(len(catalog)))
    if not args.dry_run:
        print("[+] Triggered {} request(s)".format(len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
