"""Small logging adapter for standalone repository commands."""

from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os,sys
import fire
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log_info = logging.info
log_error = logging.error
log_trace = logging.debug
log_warning = logging.warning
