"""File utilities for the daily citation check."""

from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os,sys
import fire
from src.utils.util_log import log_info, log_error, log_trace, log_warning

import csv
import json
import shutil
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def str_url_key(url: str) -> str:
    """Ignore fragments and common tracking parameters for source matching."""
    from urllib.parse import parse_qsl, urlencode
    parts = urlsplit(url.strip())
    args = [(k, v) for k, v in parse_qsl(parts.query)
            if not k.startswith("utm_") and k not in
            {"screen_view_count", "ext-referrer", "share_id", "banner"}]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                       parts.path.rstrip("/"), urlencode(sorted(args)), ""))


def os_source_urls(path: str) -> set:
    """Load public discussion/video URLs; other inventory hosts are not trusted."""
    with open(path, encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f, delimiter="\t")
        urls = [row["url"] for row in rows]
    return {str_url_key(url) for url in urls if
            (urlsplit(url).hostname in {"reddit.com", "www.reddit.com"}
             and "/comments/" in urlsplit(url).path)
            or (urlsplit(url).hostname in {"youtube.com", "www.youtube.com"}
                and (urlsplit(url).path == "/watch"
                     or urlsplit(url).path.startswith("/shorts/")))}


def os_append_rank(path: str, rows: List[List[Any]]) -> None:
    """Append TSV records and write one header, refusing incompatible files."""
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "rank", "query", "vmodal_url"]
    exists = dst.exists() and dst.stat().st_size > 0
    if exists:
        with dst.open(encoding="utf-8", newline="") as f:
            if next(csv.reader(f, delimiter="\t"), []) != fields:
                raise ValueError(f"Unexpected TSV header: {path}")
    with dst.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        if not exists:
            writer.writerow(fields)
        writer.writerows(rows)


def os_save_json(path: str, data: Any) -> None:
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")


def os_makedirs(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def os_path_cleanup(path: str) -> None:
    if Path(path).is_dir():
        shutil.rmtree(path)
    elif Path(path).exists():
        Path(path).unlink()
