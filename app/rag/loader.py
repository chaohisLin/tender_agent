from __future__ import annotations

from pathlib import Path
from typing import List, Dict


def load_kb_documents(kb_dir: Path) -> List[Dict[str, str]]:
    docs = []
    for path in sorted(kb_dir.glob("**/*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue
        docs.append({"source_name": path.name, "text": text})
    return docs
