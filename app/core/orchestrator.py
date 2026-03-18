from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from app.agents.parser_agent import ParserAgent, TenderDocumentReader
from app.agents.writer_agent import WriterAgent
from app.core.config import Settings
from app.core.draft_exporter import build_markdown, export_docx
from app.core.draft_structure import parse_markdown_to_blocks
from app.core.llm import OpenAITextGenerator
from app.core.models import DraftDocument, DraftSection
from app.rag.loader import load_kb_documents
from app.rag.retriever import BM25Retriever


class BidDemoOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.parser = ParserAgent()
        docs = load_kb_documents(settings.knowledge_base_dir)
        self.retriever = BM25Retriever(docs)
        self.llm = OpenAITextGenerator(settings)
        self.writer = WriterAgent(
            self.llm,
            self.retriever,
            max_requirements_per_section=settings.max_requirements_per_section,
            max_evidences_per_section=settings.max_evidences_per_section,
            evidence_snippet_chars=settings.evidence_snippet_chars,
        )
        settings.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, tender_path: Path) -> dict:
        raw_text = TenderDocumentReader.read(tender_path)
        metadata = self.parser.extract_metadata(raw_text)
        requirements = self.parser.parse_requirements(raw_text)
        outline = self.parser.build_outline(requirements)
        matrix = self.parser.build_response_matrix(requirements, outline)
        drafts = []
        self._save(
            {
                "metadata": metadata,
                "tender_path": str(tender_path),
                "requirements": [r.model_dump() for r in requirements],
                "outline": [s.model_dump() for s in outline],
                "response_matrix": [m.model_dump() for m in matrix],
                "drafts": [],
            }
        )

        for section in outline:
            if not section.related_requirements:
                continue
            draft = self.writer.write_section(section, requirements)
            drafts.append(draft)
            matrix = self.writer.fill_response_matrix(drafts, matrix)
            self._save(
                {
                    "metadata": metadata,
                    "tender_path": str(tender_path),
                    "requirements": [r.model_dump() for r in requirements],
                    "outline": [s.model_dump() for s in outline],
                    "response_matrix": [m.model_dump() for m in matrix],
                    "drafts": [d.model_dump() for d in drafts],
                }
            )

        result = {
            "metadata": metadata,
            "tender_path": str(tender_path),
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
        draft_doc = self._build_draft_document(result)
        (out / "draft.json").write_text(json.dumps(draft_doc.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "draft.md").write_text(build_markdown(draft_doc), encoding="utf-8")
        export_docx(draft_doc, str(out / "draft.docx"))

    @staticmethod
    def _display_title(idx: int, title: str) -> str:
        numbers = ["第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章", "第九章", "第十章"]
        prefix = numbers[idx - 1] if 0 < idx <= len(numbers) else f"第{idx}章"
        return f"{prefix} {title}"

    def _build_draft_document(self, result: dict) -> DraftDocument:
        outline_map = {item["section_id"]: item for item in result["outline"]}
        sections: list[DraftSection] = []
        for idx, draft in enumerate(result["drafts"], start=1):
            outline_item = outline_map.get(draft["section_id"], {})
            content = draft["content"].strip()
            sections.append(
                DraftSection(
                    section_id=draft["section_id"],
                    title=draft["title"],
                    display_title=self._display_title(idx, draft["title"]),
                    content_md=content,
                    content_text=content,
                    blocks=parse_markdown_to_blocks(content),
                    related_requirements=outline_item.get("related_requirements", []),
                    evidence_ids=draft.get("evidence_ids", []),
                )
            )

        metadata = result.get("metadata", {})
        return DraftDocument(
            project_name=metadata.get("project_name", ""),
            project_number=metadata.get("project_number", ""),
            purchaser=metadata.get("purchaser", ""),
            agency=metadata.get("agency", ""),
            bidder_name="",
            tender_path=result.get("tender_path", ""),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sections=sections,
            notes=[
                "本稿为自动生成初稿，供人工校核、补证与排版使用。",
                "系统内部以 JSON 作为标准中间格式，Markdown 与 DOCX 为展示和交付格式。",
            ],
        )
