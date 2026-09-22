"""Small Google AI fixtures; no paid requests in tests."""

from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os,sys
import fire
from src.utils.util_log import log_info, log_error, log_trace, log_warning


def fake_answer() -> List[Dict[str, Any]]:
    return [{"answer_text": "Some video search tools.", "citations": [
        {"url": "https://example.com/tool", "cited": True},
        {"url": "https://www.v-modal.com/ignored", "cited": False},
        {"url": "https://example.com/tool#details", "cited": True},
        {"url": "https://github.com/v-modal/vmodal_sdk_flutter", "cited": True},
        {"url": "https://www.v-modal.com/", "cited": True},
    ]}]
