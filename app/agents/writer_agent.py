from __future__ import annotations

import json
from typing import List, Dict
from app.core.llm import OpenAITextGenerator
from app.core.models import RequirementItem, OutlineSection, ChapterDraft, ResponseMatrixRow
from app.rag.retriever import BM25Retriever
from app.templates.prompts import WRITER_SYSTEM_PROMPT


class WriterAgent:
    def __init__(self, llm: OpenAITextGenerator, retriever: BM25Retriever):
        self.llm = llm
        self.retriever = retriever

    def _requirements_for_section(self, section: OutlineSection, requirements: List[RequirementItem]) -> List[RequirementItem]:
        req_map = {r.req_id: r for r in requirements}
        return [req_map[rid] for rid in section.related_requirements if rid in req_map]

    def write_section(self, section: OutlineSection, requirements: List[RequirementItem]) -> ChapterDraft:
        related = self._requirements_for_section(section, requirements)
        query = section.title + "\n" + "\n".join(r.content for r in related[:5])
        evidences = self.retriever.retrieve(query=query, top_k=3)
        payload: Dict[str, object] = {
            "section": section.model_dump(),
            "requirements": [r.model_dump() for r in related],
            "evidences": [e.model_dump() for e in evidences],
            "writing_rule": "生成适合导师演示的简洁章节，不要过长，但要看起来像真实投标文件。",
        }
        content = self.llm.generate(WRITER_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, indent=2))
        return ChapterDraft(
            section_id=section.section_id,
            title=section.title,
            content=content,
            evidence_ids=[e.evidence_id for e in evidences],
        )

    def fill_response_matrix(self, drafts: List[ChapterDraft], matrix: List[ResponseMatrixRow]) -> List[ResponseMatrixRow]:
        draft_map = {d.title: d for d in drafts}
        for row in matrix:
            matched = draft_map.get(row.response_section)
            if matched:
                row.response_text = f"已在《{matched.title}》章节中进行响应。"
                row.evidence_ids = matched.evidence_ids[:]
        return matrix
