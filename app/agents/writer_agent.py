from __future__ import annotations

import json
import re
from typing import List, Dict
from app.core.llm import OpenAITextGenerator
from app.core.models import RequirementItem, OutlineSection, ChapterDraft, ResponseMatrixRow
from app.rag.retriever import BM25Retriever
from app.templates.prompts import WRITER_SYSTEM_PROMPT


class WriterAgent:
    section_templates = {
        "项目理解与总体响应": [
            "1. 项目背景与目标理解",
            "2. 实施边界理解",
            "3. 总体响应承诺",
        ],
        "技术方案": [
            "2.1 方案总体思路",
            "2.2 技术响应要点",
            "2.3 实施流程与交付成果",
            "2.4 质量保障与风险控制",
        ],
        "商务与实施计划": [
            "3.1 实施计划",
            "3.2 工期与交付安排",
            "3.3 服务与售后响应",
            "3.4 商务承诺",
        ],
        "评分点应答": [
            "4.1 评分点响应说明",
            "4.2 关键评分点对照表",
            "4.3 证明材料补充建议",
        ],
        "格式与附件说明": [
            "5.1 响应文件组成",
            "5.2 编制与装订要求",
            "5.3 签章密封与提交说明",
            "5.4 附件建议清单",
        ],
    }

    def __init__(
        self,
        llm: OpenAITextGenerator,
        retriever: BM25Retriever,
        max_requirements_per_section: int = 8,
        max_evidences_per_section: int = 2,
        evidence_snippet_chars: int = 120,
    ):
        self.llm = llm
        self.retriever = retriever
        self.max_requirements_per_section = max_requirements_per_section
        self.max_evidences_per_section = max_evidences_per_section
        self.evidence_snippet_chars = evidence_snippet_chars

    def _requirements_for_section(self, section: OutlineSection, requirements: List[RequirementItem]) -> List[RequirementItem]:
        req_map = {r.req_id: r for r in requirements}
        return [req_map[rid] for rid in section.related_requirements if rid in req_map]

    def _select_key_requirements(self, requirements: List[RequirementItem]) -> List[RequirementItem]:
        ranked = sorted(
            requirements,
            key=lambda item: (
                1 if item.mandatory else 0,
                item.priority,
                item.req_id,
            ),
            reverse=True,
        )
        return ranked[: self.max_requirements_per_section]

    @staticmethod
    def _serialize_requirement(item: RequirementItem) -> Dict[str, object]:
        return {
            "req_id": item.req_id,
            "title": item.title,
            "content": item.content[:220],
            "requirement_type": item.requirement_type.value,
            "priority": item.priority,
            "mandatory": item.mandatory,
            "source": item.source.model_dump(),
        }

    def write_section(self, section: OutlineSection, requirements: List[RequirementItem]) -> ChapterDraft:
        related = self._requirements_for_section(section, requirements)
        selected = self._select_key_requirements(related)
        query = section.title + "\n" + "\n".join(r.content[:120] for r in selected[:4])
        evidences = self.retriever.retrieve(query=query, top_k=self.max_evidences_per_section)
        payload: Dict[str, object] = {
            "section": section.model_dump(),
            "section_requirement_count": len(related),
            "key_requirements": [self._serialize_requirement(r) for r in selected],
            "evidences": [
                {
                    "evidence_id": e.evidence_id,
                    "source_name": e.source_name,
                    "snippet": e.snippet[: self.evidence_snippet_chars],
                    "score": e.score,
                }
                for e in evidences
            ],
            "section_template": self.section_templates.get(section.title, []),
            "writing_rule": (
                "生成更像正式标书的章节内容；"
                "使用正式、审慎、可汇报的中文；"
                "优先覆盖关键和强制性要求；"
                "除评分点应答章节外，避免输出最上层章节标题；"
                "多用编号小节、条列和必要表格；"
                "不要逐条照抄输入，不要编造资质、业绩和参数。"
            ),
        }
        try:
            content = self.llm.generate(WRITER_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, indent=2))
        except Exception as exc:
            content = f"【自动生成失败】\n\n章节《{section.title}》生成失败：{exc}"
        content = self._normalize_content(section.title, content)
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

    @staticmethod
    def _normalize_content(section_title: str, content: str) -> str:
        lines = content.strip().splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and re.match(rf"^\s*#{1,6}\s*.*{re.escape(section_title)}\s*$", lines[0].strip()):
            lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
        return "\n".join(lines).strip()
