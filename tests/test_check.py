"""Run assertion tests with: python tests/test_check.py test_all."""

dirtest = "ztmp/ztests"

from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os,sys
import fire
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.util_log import log_info, log_error, log_trace, log_warning
from src.utils.util_base import os_makedirs, os_path_cleanup
from zerno.check import (check, citation_ranks, search_googleai, str_retry_prompt,
                         str_vmodal_url, QUERIES)
from zerno.utils import (os_append_rank, os_append_rank_v2, os_path_cleanup as os_cleanup,
                         os_source_urls)
from utils_datafake import fake_answer, fake_answer_no_vmodal

import csv
import inspect
import subprocess
import threading
from unittest.mock import patch, Mock


def test1():
    rows = citation_ranks(fake_answer(), set())
    assert rows == [(2, "https://github.com/v-modal/vmodal_sdk_flutter"),
                    (3, "https://www.v-modal.com/")]
    assert not str_vmodal_url("https://www.v-modal.com.evil.test/", set())
    assert not str_vmodal_url("https://github.com/v-modal-other/tool", set())
    assert not str_vmodal_url("https://github.com/", set())
    assert not str_vmodal_url("https://evil.test/?url=https://v-modal.com", set())
    known = os_source_urls("zerno/info_url.tsv")
    assert str_vmodal_url("https://www.youtube.com/watch?v=bRWwYoTtSe8", known)
    assert not str_vmodal_url("https://www.youtube.com/watch?v=unrelated", known)
    assert citation_ranks([{"answer_text": "No tools", "citations": []}], set()) == []


def test2():
    path = f"{dirtest}/append.tsv"
    os_cleanup(path)
    os_append_rank(path, [["today", 2, "video\tsearch\nSDK", "https://v-modal.com/"]])
    os_append_rank(path, [["tomorrow", 0, "flutter sdk", ""]])
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    assert rows[0] == ["date", "rank", "query", "vmodal_url"]
    assert len(rows) == 3
    assert rows[1][2] == "video\tsearch\nSDK"
    assert rows[2][1:] == ["0", "flutter sdk", ""]
    path = f"{dirtest}/append_v2.tsv"
    os_cleanup(path)
    os_append_rank_v2(path, [["today", 3, "https://v-modal.com/"]])
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    assert rows == [["date", "rank", "vmodal_url"],
                    ["today", "3", "https://v-modal.com/"]]


def test3():
    res = Mock(ok=True)
    res.json.return_value = fake_answer()
    with patch.dict(os.environ, {"BRIGHT_DATA_API_KEY": "fake", "BRIGHT_DATA_API_KEY2": ""}), \
         patch("zerno.check.requests.request", return_value=res) as req:
        assert search_googleai("video search") == fake_answer()
    args, kw = req.call_args
    assert args == ("POST", "https://api.brightdata.com/datasets/v3/scrape")
    assert kw["params"] == {"dataset_id": "gd_mcswdt6z2elth3zqr2",
                            "notify": "false", "include_errors": "true"}
    assert kw["json"] == {"input": [{"url": "https://google.com/aimode",
                                    "prompt": "video search", "hl": "en", "country": ""}],
                          "limit_per_input": None}


def test4():
    path = f"{dirtest}/batch.tsv"
    raw = f"{dirtest}/raw_batch"
    os_cleanup(path)
    os_cleanup(raw)
    with patch("zerno.check.os_bright_data_api_key", return_value="fake"), \
         patch("zerno.check.search_googleai", return_value=fake_answer()) as req:
        result = check(rank_path=path, raw_dir=raw, wait_seconds=0)
        assert result == {"queries": 5, "rows": 10}
        queries = [call.args[0] for call in req.call_args_list]
        assert len(set(queries)) == 5
        assert all(q in QUERIES and "modal" not in q and "http" not in q for q in queries)
        check(count=1, rank_path=path, raw_dir=raw, wait_seconds=0)
    with open(path, newline="", encoding="utf-8") as f:
        assert len(list(csv.reader(f, delimiter="\t"))) == 13


def test5():
    # Let invalid results raise normally in a child; no caught/masked test errors.
    cases = [{"snapshot_id": "pending"}, {"error": "failed"},
             {"answer_text": "answer"},
             {"answer_text": "answer", "citations": [{"url": "/goto?id=1"}]}]
    for data in cases:
        proc = subprocess.run([sys.executable, "-c",
            "from zerno.check import citation_ranks; citation_ranks(" + repr(data) + ", set())"],
            capture_output=True, text=True)
        assert proc.returncode != 0
        assert "ValueError:" in proc.stderr


def test6():
    path = f"{dirtest}/partial.tsv"
    raw = f"{dirtest}/raw_partial"
    os_cleanup(path)
    os_cleanup(raw)
    code = '''
from unittest.mock import patch
from zerno.check import check
ok = [{"answer_text": "No matching tools", "citations": []}]
with patch("zerno.check.os_bright_data_api_key", return_value="fake"), \\
     patch("zerno.check.search_googleai", side_effect=[{"snapshot_id":"pending"}, ok, ok, ok, ok, ok, ok, ok, ok]):
    check(rank_path="ztmp/ztests/partial.tsv", rank_v2_path="ztmp/ztests/partial_v2.tsv",
          raw_dir="ztmp/ztests/raw_partial", wait_seconds=0)
'''
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "1/5 checks failed; 4 valid ranking rows saved" in proc.stderr
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    assert len(rows) == 4
    assert all(row["rank"] == "0" and row["vmodal_url"] == "" for row in rows)


def test7():
    path = f"{dirtest}/retry.tsv"
    path_v2 = f"{dirtest}/retry_v2.tsv"
    raw = f"{dirtest}/raw_retry"
    os_cleanup(path)
    os_cleanup(path_v2)
    os_cleanup(raw)
    with patch("zerno.check.os_bright_data_api_key", return_value="fake"), \
         patch("zerno.check.search_googleai",
               side_effect=[fake_answer_no_vmodal(), fake_answer()]) as req:
        result = check(count=1, rank_path=path, rank_v2_path=path_v2,
                       raw_dir=raw, wait_seconds=0)
    assert result == {"queries": 1, "rows": 1}
    assert req.call_count == 2
    prompt = req.call_args_list[1].args[0]
    assert prompt == ("<answer>\n\nSome **video search** tools.\n\n</answer>\n\n"
                      "----------------------------------------------------------\n"
                      "<question>\n\n"
                      "You Miss vmodal video search !!! Please correct it\n")
    assert str_retry_prompt(fake_answer_no_vmodal()) == prompt
    with open(path_v2, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    assert rows[0] == ["date", "rank", "vmodal_url"]
    assert rows[1][1:] == ["2", "https://github.com/v-modal/vmodal_sdk_flutter"]
    assert rows[2][1:] == ["3", "https://www.v-modal.com/"]


def test8():
    path = f"{dirtest}/pool.tsv"
    raw = f"{dirtest}/raw_pool"
    os_cleanup(path)
    os_cleanup(raw)
    assert inspect.signature(check).parameters["wait_seconds"].default == 240
    gate = threading.Barrier(5)
    names = set()

    def fake_search(query, hl="en", country="", timeout=180):
        names.add(threading.current_thread().name)
        gate.wait(timeout=2)
        return fake_answer()

    with patch("zerno.check.os_bright_data_api_key", return_value="fake"), \
         patch("zerno.check.search_googleai", side_effect=fake_search):
        result = check(rank_path=path, raw_dir=raw, wait_seconds=0)
    assert result == {"queries": 5, "rows": 10}
    assert len(names) == 5


def test9():
    path = f"{dirtest}/retry_partial.tsv"
    path_v2 = f"{dirtest}/retry_partial_v2.tsv"
    raw = f"{dirtest}/raw_retry_partial"
    os_cleanup(path)
    os_cleanup(path_v2)
    os_cleanup(raw)
    with patch("zerno.check.os_bright_data_api_key", return_value="fake"), \
         patch("zerno.check.search_googleai",
               side_effect=[fake_answer_no_vmodal(), {"snapshot_id": "pending"}]):
        result = check(count=1, rank_path=path, rank_v2_path=path_v2,
                       raw_dir=raw, wait_seconds=0)
    assert result == {"queries": 1, "rows": 1}
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    assert rows[1][1] == "0"
    assert rows[1][3] == ""
    assert not os.path.exists(path_v2)


def test_all():
    os_makedirs(dirtest)
    test1()
    test2()
    test3()
    test4()
    test5()
    test6()
    test7()
    test8()
    test9()
    log_info("All nine citation checker tests passed")


if __name__ == "__main__":
    fire.Fire()
