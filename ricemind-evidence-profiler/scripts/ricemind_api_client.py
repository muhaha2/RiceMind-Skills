#!/usr/bin/env python
"""Small RiceMind REST client with pagination helpers.

This script is intentionally dependency-light so it can be reused by task
builders in the integrated RiceMind skill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_BASE_URL = "http://lit-evi.hzau.edu.cn/ricemind-api/"
DEFAULT_MAX_PAGES = 10000
RESTRICTED_VOCABULARY_ENDPOINTS = {"all-genes", "all-traits"}


class RiceMindClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 60,
        sleep: float = 0.0,
        retries: int = 3,
        backoff: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.sleep = sleep
        self.retries = max(0, retries)
        self.backoff = max(0.0, backoff)

    def url(self, endpoint: str, params: Dict[str, Any]) -> str:
        endpoint = endpoint.strip("/")
        clean_params = {k: v for k, v in params.items() if v is not None}
        return self.base_url + endpoint + "/?" + urllib.parse.urlencode(clean_params, doseq=True)

    def get(self, endpoint: str, **params: Any) -> Dict[str, Any]:
        url = self.url(endpoint, params)
        req = urllib.request.Request(url, headers={"User-Agent": "RiceMindEvidenceProfiler/1.0"})
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    payload = response.read().decode("utf-8")
                data = json.loads(payload)
                if self.sleep:
                    time.sleep(self.sleep)
                if isinstance(data, dict):
                    data.setdefault("_request_url", url)
                return data
            except urllib.error.HTTPError as exc:
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable or attempt >= self.retries:
                    raise
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                delay = float(retry_after) if retry_after.replace(".", "", 1).isdigit() else self.backoff * (2 ** attempt)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                if attempt >= self.retries:
                    raise
                delay = self.backoff * (2 ** attempt)
            if delay:
                time.sleep(delay)
        raise RuntimeError(f"RiceMind request failed after retries: {url}")

    def fetch_all(
        self,
        endpoint: str,
        result_keys: Optional[Iterable[str]] = None,
        limit: int = 500,
        max_pages: int = DEFAULT_MAX_PAGES,
        allow_full_vocabulary: bool = False,
        **params: Any,
    ) -> Dict[str, Any]:
        endpoint_name = endpoint.strip("/").lower()
        if endpoint_name in RESTRICTED_VOCABULARY_ENDPOINTS and not allow_full_vocabulary:
            raise ValueError(
                f"Full pagination for /{endpoint_name}/ is restricted. "
                "Use the local vocabulary policy or pass allow_full_vocabulary=True only for an explicit user request."
            )
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        if max_pages <= 0:
            raise ValueError("max_pages must be greater than zero")

        pages: List[Dict[str, Any]] = []
        records: List[Any] = []
        seen_page_fingerprints = set()
        page = 1
        result_keys = list(result_keys or [])
        stop_reason = "max_pages"
        pagination_complete = False

        while page <= max_pages:
            data = self.get(endpoint, page=page, limit=limit, **params)
            page_records = extract_records(data, result_keys)
            fingerprint = records_fingerprint(page_records)
            if page_records and fingerprint in seen_page_fingerprints:
                pages.append(data)
                stop_reason = "repeated_page"
                break
            if page_records:
                seen_page_fingerprints.add(fingerprint)

            pages.append(data)
            records.extend(page_records)

            total_pages = as_int(data.get("total_pages"))
            current_page = as_int(data.get("current_page")) or page
            total_count = as_int(data.get("total_count"))

            nested_pagination = data.get("sentence_pagination")
            if isinstance(nested_pagination, dict):
                total_pages = as_int(nested_pagination.get("total_pages")) or total_pages
                current_page = as_int(nested_pagination.get("current_page")) or current_page
                total_count = as_int(nested_pagination.get("total_sentences")) or total_count

            if total_pages and current_page >= total_pages:
                stop_reason = "total_pages"
                pagination_complete = True
                break
            if total_count and len(records) >= total_count:
                stop_reason = "total_count"
                pagination_complete = True
                break
            if not page_records:
                stop_reason = "empty_page"
                pagination_complete = True
                break
            if len(page_records) < limit:
                stop_reason = "short_page"
                pagination_complete = True
                break

            page += 1

        return {
            "endpoint": endpoint,
            "params": params,
            "limit": limit,
            "pages_retrieved": len(pages),
            "records_retrieved": len(records),
            "pagination_complete": pagination_complete,
            "pagination_stop_reason": stop_reason,
            "pages": pages,
            "records": records,
        }


def as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_records(data: Dict[str, Any], preferred_keys: Iterable[str]) -> List[Any]:
    for key in preferred_keys:
        value = data.get(key)
        if isinstance(value, list):
            return value
    for key in ("results", "sentence_evidence", "associated_traits", "varieties", "genes", "traits"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def records_fingerprint(records: List[Any]) -> str:
    serialized = json.dumps(records, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def parse_params(items: List[str]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Parameter must be key=value: {item}")
        key, value = item.split("=", 1)
        params[key] = value
    return params


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch RiceMind API endpoints with optional full pagination.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--endpoint", required=True, help="Endpoint name such as search-by-trait")
    parser.add_argument("--param", action="append", default=[], help="Query parameter as key=value; repeatable")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--backoff", type=float, default=1.0)
    parser.add_argument("--all-pages", action="store_true")
    parser.add_argument(
        "--allow-full-vocabulary",
        action="store_true",
        help="Allow full pagination of /all-genes/ or /all-traits/ only when the user explicitly requested it",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    endpoint_name = args.endpoint.strip("/").lower()
    if args.all_pages and endpoint_name in RESTRICTED_VOCABULARY_ENDPOINTS and not args.allow_full_vocabulary:
        parser.error(
            f"--all-pages is blocked for /{endpoint_name}/. "
            "Use --allow-full-vocabulary only for an explicit user request for the complete vocabulary."
        )

    client = RiceMindClient(args.base_url, retries=args.retries, backoff=args.backoff)
    params = parse_params(args.param)
    if args.all_pages:
        payload = client.fetch_all(
            args.endpoint,
            limit=args.limit,
            max_pages=args.max_pages,
            allow_full_vocabulary=args.allow_full_vocabulary,
            **params,
        )
    else:
        payload = client.get(args.endpoint, limit=args.limit, **params)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
