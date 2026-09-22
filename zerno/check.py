"""Check unbranded Google AI citation positions; rank 0 means no match.

Rank is the order of distinct cited sources, not Google's organic SERP rank.
Pending/error responses produce no ranking row and fail the run after all attempts.
Run from any directory: python /path/to/zerno/check.py
"""

from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os,sys
import fire
from pathlib import Path

# Support direct CLI execution without requiring an installed project package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.util_log import log_info, log_error, log_trace, log_warning

import random
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4
import requests

from zerno.utils import os_append_rank, os_save_json, os_source_urls, str_url_key

BASE = Path(__file__).resolve().parent
QUERIES = (
    "Which video search tools find scenes using text or images?",
    "Which AI video search APIs support CCTV and dashcam footage?",
    "Which video search SDK supports semantic search with timestamps?",
    "Which mobile video search SDK supports Android, Flutter, and iOS?",
    "Which physical AI SDK supports robot video search and visual memory?",
    "How can I add Android video search to a Kotlin app?",
    "Which Flutter SDK offers AI video and image search?",
    "How can I build a Flutter video search gallery with natural language queries?",
    "Which Swift video search SDK supports semantic search in iPhone recordings?",
)
BRIGHT_DATA_URL = "https://api.brightdata.com"
BRIGHT_DATA_GOOGLEAI_DATASET = "gd_mcswdt6z2elth3zqr2"


def os_bright_data_api_key() -> str:
    """Copied from run.py: select either configured key with its existing weights."""
    names = ("BRIGHT_DATA_API_KEY", "BRIGHT_DATA_API_KEY2")
    keys = [os.environ.get(name, "").strip() for name in names]
    keys = [key for key in keys if key]
    if not keys:
        raise RuntimeError("BRIGHT_DATA_API_KEY and BRIGHT_DATA_API_KEY2 are missing or empty")
    if len(keys) == 1:
        return keys[0]
    return random.choices(keys, weights=(30, 70), k=1)[0]


def api_json(method: str, url: str, api_key: str, body: Optional[Any] = None,
             params: Optional[Dict[str, Any]] = None, timeout: int = 120,
             request_id: str = "") -> Any:
    """Request code copied from run.py."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if request_id:
        headers["x-request-id"] = request_id
    res = requests.request(method, url, headers=headers, json=body,
                           params=params, timeout=timeout)
    if not res.ok:
        msg = f"{method} {url} failed ({res.status_code}): {res.text[:1500]}"
        log_error(msg)
        raise requests.HTTPError(msg, response=res)
    return res.json()


def search_googleai(query: str, hl: str = "en", country: str = "",
                    timeout: int = 180) -> Any:
    """Same endpoint, dataset and request payload as run.py search_googleai."""
    if not query.strip():
        raise ValueError("query is required")
    params = {"dataset_id": BRIGHT_DATA_GOOGLEAI_DATASET,
              "notify": "false", "include_errors": "true"}
    body = {"input": [{"url": "https://google.com/aimode", "prompt": query,
                        "hl": hl, "country": country}], "limit_per_input": None}
    return api_json("POST", f"{BRIGHT_DATA_URL}/datasets/v3/scrape",
                    os_bright_data_api_key(), body=body, params=params, timeout=timeout)


def str_vmodal_url(url: str, known: set) -> bool:
    """Match owned hosts/accounts or approved inventory discussion/video URLs."""
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return False
    host, path = parts.hostname.lower(), parts.path.rstrip("/")
    if host in {"v-modal.com", "www.v-modal.com", "v-modal.github.io",
                "vmodal-memory-search.connpass.com"}:
        return True
    roots = {"github.com": ("/v-modal", "/orgs/v-modal"),
             "dev.to": ("/vmodal_ai",),
             "reddit.com": ("/r/v_modal",),
             "www.reddit.com": ("/r/v_modal",),
             "www.linkedin.com": ("/company/v-modal",),
             "devhunt.org": ("/tool/vmodal-visual-video-search-sdk",),
             "p.timeshining.com": ("/detail/dart/v-modal/vmodal_sdk_flutter",)}
    if any(path == root or path.startswith(root + "/") for root in roots.get(host, ())):
        return True
    if host in {"linkedin.com", "www.linkedin.com"} and path.startswith("/posts/v-modal_"):
        return True
    return str_url_key(url) in known


def citation_ranks(data: Any, known: set) -> List[Tuple[int, str]]:
    """Validate one completed answer and rank its distinct cited URLs."""
    if isinstance(data, list):
        if len(data) != 1:
            raise ValueError("Expected one Google AI result")
        data = data[0]
    if not isinstance(data, dict):
        raise ValueError("Invalid Google AI result")
    if data.get("snapshot_id") or data.get("error") or data.get("error_code"):
        raise ValueError("Google AI returned pending work or an error; see saved response")
    if not any(isinstance(data.get(k), str) and data[k].strip()
               for k in ("answer_text", "answer_text_markdown")):
        raise ValueError("Google AI response has no answer")
    cites = data.get("citations")
    if not isinstance(cites, list):
        raise ValueError("Google AI response has no valid citations list")
    seen, matches = set(), []
    for item in cites:
        if not isinstance(item, dict) or not isinstance(item.get("url"), str):
            raise ValueError("Malformed citation")
        if item.get("cited") is False:
            continue
        url = item["url"].strip()
        if urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).hostname:
            raise ValueError("Citation URL is unresolved or invalid")
        key = str_url_key(url)
        if key in seen:
            continue
        seen.add(key)
        if str_vmodal_url(url, known):
            matches.append((len(seen), url))
    return matches


def check(count: int = 5, rank_path: str = str(BASE / "ranking/rank.tsv"),
          hl: str = "en", country: str = "", timeout: int = 180) -> Dict[str, int]:
    """Sample five distinct open queries and append every matching citation."""
    if not 1 <= count <= len(QUERIES):
        raise ValueError(f"count must be between 1 and {len(QUERIES)}")
    os_bright_data_api_key()  # Fail before starting if no credential is configured.
    known = os_source_urls(str(BASE / "info_url.tsv"))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid4().hex[:8]
    failed, total = 0, 0
    for i, query in enumerate(random.sample(QUERIES, count), 1):
        stamp = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        path = BASE / "ranking/raw" / run_id / f"{i}.json"
        log_info("Checking %s/%s: %s", i, count, query)
        try:
            data = search_googleai(query, hl=hl, country=country, timeout=timeout)
            os_save_json(str(path), {"date": stamp, "query": query, "response": data})
            matches = citation_ranks(data, known)
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            failed += 1
            log_error("Query failed: %s: %s", query, exc)
            continue
        rows = [[stamp, rank, query, url] for rank, url in (matches or [(0, "")])]
        os_append_rank(rank_path, rows)
        log_info("Appended %s ranking row(s) to %s", len(rows), rank_path)
        total += len(rows)
    if failed:
        raise RuntimeError(f"{failed}/{count} checks failed; {total} valid ranking rows saved")
    return {"queries": count, "rows": total}


if __name__ == "__main__":
    fire.Fire(check)
