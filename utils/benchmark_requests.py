"""Request catalog and replay helpers for Reinforced WAVSEP HAR fixtures.

The HAR files are the source of truth for requests that trigger benchmark
cases. This module keeps request parsing deterministic and independent from
the current working directory so tests, CLIs, and CI all exercise the same
catalog.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple
from urllib.parse import ParseResult, urlparse, urlunparse


DEFAULT_BASE_URL = "http://127.0.0.1:18080"
DEFAULT_TIMEOUT_SECONDS = 2
HAR_REQUESTS_ROOT = Path(__file__).resolve().parent / "har_requests"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEBAPP_ROOT = PROJECT_ROOT / "src" / "main" / "webapp"

# Browser-captured headers that are either stale after capture or recalculated
# by the HTTP client. Keeping them caused bad Host/Cookie state during replay.
VOLATILE_HEADERS = {"host", "content-length", "cookie"}


HeaderPairs = Tuple[Tuple[str, str], ...]


@dataclass(frozen=True)
class RequestBody:
    """Body information extracted from a HAR request entry."""

    mime_type: str
    params: HeaderPairs
    text: str = ""

    @property
    def has_payload(self) -> bool:
        return bool(self.params or self.text)


@dataclass(frozen=True)
class BenchmarkRequest:
    """A replayable benchmark request captured in one HAR entry."""

    category: str
    har_file: Path
    entry_index: int
    method: str
    url: str
    headers: HeaderPairs
    cookies: HeaderPairs
    query_params: HeaderPairs
    body: RequestBody
    expected_status: Optional[int]

    @property
    def parsed_url(self) -> ParseResult:
        return urlparse(self.url)

    @property
    def path(self) -> str:
        return self.parsed_url.path

    @property
    def file_name(self) -> str:
        return Path(self.path).name

    @property
    def test_name(self) -> str:
        return Path(self.file_name).stem

    @property
    def webapp_path(self) -> Path:
        relative_path = self.path.lstrip("/")
        if relative_path.startswith("wavsep/"):
            relative_path = relative_path[len("wavsep/") :]
        return WEBAPP_ROOT / relative_path

    def exists_in_webapp(self) -> bool:
        return self.webapp_path.exists()

    def target_url(self, base_url: str = DEFAULT_BASE_URL) -> str:
        """Return this request URL rewritten for the requested WAVSEP host."""

        target_base = urlparse(base_url)
        original = self.parsed_url
        rewritten = original._replace(
            scheme=target_base.scheme or original.scheme,
            netloc=target_base.netloc or original.netloc,
        )
        return urlunparse(rewritten)

    def replay_headers(self) -> Dict[str, str]:
        """Return stable headers that can be safely reused across sessions."""

        return {
            name: value
            for name, value in self.headers
            if name.lower() not in VOLATILE_HEADERS
        }

    def replay_data(self) -> object:
        """Return request payload in the shape expected by requests.request."""

        if self.body.params:
            return dict(self.body.params)
        if self.body.text:
            return self.body.text
        return None

    def identity(self) -> Tuple[object, ...]:
        """Stable identity used to de-duplicate repeated crawler captures."""

        return (
            self.method,
            self.path,
            self.query_params,
            self.body.mime_type,
            self.body.params,
            self.body.text,
        )

    def to_dict(self, base_url: str = DEFAULT_BASE_URL) -> Dict[str, object]:
        """Serialize the replayable request for dry-run output and tests."""

        return {
            "category": self.category,
            "har_file": str(self.har_file),
            "entry_index": self.entry_index,
            "method": self.method,
            "url": self.target_url(base_url),
            "headers": self.replay_headers(),
            "query_params": dict(self.query_params),
            "body_params": dict(self.body.params),
            "body_text": self.body.text,
            "expected_status": self.expected_status,
            "test_name": self.test_name,
        }


def _pairs(items: Sequence[Dict[str, object]]) -> HeaderPairs:
    pairs = []
    for item in items:
        name = str(item.get("name", ""))
        value = str(item.get("value", ""))
        pairs.append((name, value))
    return tuple(pairs)


def _parse_body(request_data: Dict[str, object]) -> RequestBody:
    post_data = request_data.get("postData") or {}
    if not isinstance(post_data, dict):
        return RequestBody(mime_type="", params=tuple(), text="")
    return RequestBody(
        mime_type=str(post_data.get("mimeType", "")),
        params=_pairs(post_data.get("params", []) or []),
        text=str(post_data.get("text", "") or ""),
    )


def _expected_status(entry_data: Dict[str, object]) -> Optional[int]:
    response = entry_data.get("response") or {}
    if not isinstance(response, dict):
        return None
    status = response.get("status")
    return int(status) if isinstance(status, int) else None


def iter_har_files(
    category: Optional[str] = None,
    har_file: Optional[str] = None,
    har_root: Path = HAR_REQUESTS_ROOT,
) -> Iterator[Tuple[str, Path]]:
    """Yield HAR files in deterministic order, optionally filtered."""

    categories = [category] if category else sorted(p.name for p in har_root.iterdir() if p.is_dir())
    for current_category in categories:
        category_root = har_root / current_category
        if har_file:
            yield current_category, category_root / har_file
            continue
        for path in sorted(category_root.glob("*.har")):
            yield current_category, path


def parse_har_file(category: str, har_file: Path) -> List[BenchmarkRequest]:
    """Parse one HAR file into replayable benchmark requests."""

    with har_file.open(encoding="utf-8") as file_handle:
        data = json.load(file_handle)

    entries = data.get("log", {}).get("entries", [])
    requests = []
    for index, entry in enumerate(entries):
        request_data = entry["request"]
        requests.append(
            BenchmarkRequest(
                category=category,
                har_file=har_file,
                entry_index=index,
                method=str(request_data["method"]).upper(),
                url=str(request_data["url"]),
                headers=_pairs(request_data.get("headers", []) or []),
                cookies=_pairs(request_data.get("cookies", []) or []),
                query_params=_pairs(request_data.get("queryString", []) or []),
                body=_parse_body(request_data),
                expected_status=_expected_status(entry),
            )
        )
    return requests


def load_catalog(
    category: Optional[str] = None,
    har_file: Optional[str] = None,
    deduplicate: bool = True,
    har_root: Path = HAR_REQUESTS_ROOT,
) -> List[BenchmarkRequest]:
    """Load all replayable requests from the HAR corpus."""

    catalog = []
    seen = set()
    for current_category, path in iter_har_files(category, har_file, har_root):
        for request in parse_har_file(current_category, path):
            identity = request.identity()
            if deduplicate and identity in seen:
                continue
            seen.add(identity)
            catalog.append(request)
    return catalog


def missing_webapp_requests(requests: Iterable[BenchmarkRequest]) -> List[BenchmarkRequest]:
    """Return requests whose JSP/resource target does not exist in webapp."""

    return [request for request in requests if not request.exists_in_webapp()]


def trigger_requests(
    requests_to_trigger: Iterable[BenchmarkRequest],
    base_url: str = DEFAULT_BASE_URL,
    proxy: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    dry_run: bool = False,
) -> List[Dict[str, object]]:
    """Trigger requests or return their serialized dry-run representation."""

    serialized_requests = []
    if dry_run:
        return [request.to_dict(base_url) for request in requests_to_trigger]

    import requests

    session = requests.Session()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    for request in requests_to_trigger:
        response = session.request(
            request.method,
            request.target_url(base_url),
            headers=request.replay_headers(),
            data=request.replay_data(),
            proxies=proxies,
            verify=False,
            allow_redirects=False,
            timeout=timeout,
        )
        serialized = request.to_dict(base_url)
        serialized["actual_status"] = response.status_code
        serialized_requests.append(serialized)
    return serialized_requests
