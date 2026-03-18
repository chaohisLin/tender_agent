from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_mode: str = "auto"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.2
    knowledge_base_dir: Path = Path("./data/demo_kb")
    output_dir: Path = Path("./data/output")
    max_requirements_per_section: int = 8
    max_evidences_per_section: int = 2
    evidence_snippet_chars: int = 120


def get_settings() -> Settings:
    load_dotenv(override=True)
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_api_mode=os.getenv("OPENAI_API_MODE", "auto"),
        model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        temperature=float(os.getenv("TEMPERATURE", "0.2")),
        knowledge_base_dir=Path(os.getenv("KNOWLEDGE_BASE_DIR", "./data/demo_kb")),
        output_dir=Path(os.getenv("OUTPUT_DIR", "./data/output")),
        max_requirements_per_section=int(os.getenv("MAX_REQUIREMENTS_PER_SECTION", "8")),
        max_evidences_per_section=int(os.getenv("MAX_EVIDENCES_PER_SECTION", "2")),
        evidence_snippet_chars=int(os.getenv("EVIDENCE_SNIPPET_CHARS", "120")),
    )
