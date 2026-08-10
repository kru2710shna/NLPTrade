from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
import sys
from typing import Any
import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

def parse_datetime(value: str) -> datetime:
    
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def document_exit(db,source_type: str, url: str|None, title: str| None): 
    
