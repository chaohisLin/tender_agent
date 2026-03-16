from __future__ import annotations

import json
from pathlib import Path
from app.agents.parser_agent import ParserAgent, TenderDocumentReader
from app.agents.writer_agent import WriterAgent
from app.core.config import Settings
from app.core.llm import OpenAITextGenerator
from app.rag.loader import load_kb_documents
from app.rag.retriever import BM25Retriever


class BidDemoOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.parser = ParserAgent()
        docs = load_kb_documents(settings.knowledge_base_dir)
        self.retriever = BM25Retriever(docs)
        self.llm = OpenAITextGenerator(settings)
        self.writer = WriterAgent(self.llm, self.retriever)
        settings.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, tender_path: Path) -> dict:
        raw_text = TenderDocumentReader.read(tender_path)
        requirements = self.parser.parse_requirements(raw_text)
        outline = self.parser.build_outline(requirements)
        matrix = self.parser.build_response_matrix(requirements, outline)
        drafts = [self.writer.write_section(section, requirements) for section in outline if section.related_requirements]
        matrix = self.writer.fill_response_matrix(drafts, matrix)

        result = {
            "requirements": [r.model_dump() for r in requirements],
            "outline": [s.model_dump() for s in outline],
            "response_matrix": [m.model_dump() for m in matrix],
            "drafts": [d.model_dump() for d in drafts],
        }
        self._save(result)
        return result

    def _save(self, result: dict) -> None:
        out = self.settings.output_dir
        (out / "requirements.json").write_text(json.dumps(result["requirements"], ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "outline.json").write_text(json.dumps(result["outline"], ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "response_matrix.json").write_text(json.dumps(result["response_matrix"], ensure_ascii=False, indent=2), encoding="utf-8")
        md = []
        for draft in result["drafts"]:
            md.append(f"# {draft['title']}\n\n{draft['content']}\n")
        (out / "draft.md").write_text("\n".join(md), encoding="utf-8")
