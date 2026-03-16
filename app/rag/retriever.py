from __future__ import annotations

import re
from typing import List
from rank_bm25 import BM25Okapi
from app.core.models import EvidenceItem


def tokenize(text: str) -> List[str]:
    return re.findall(r"[\u4e00-\u9fff]{1,}|[A-Za-z0-9_\-]+", text.lower())


class BM25Retriever:
    def __init__(self, docs: List[dict]):
        self.docs = docs
        self.corpus = [tokenize(d["text"]) for d in docs]
        self.bm25 = BM25Okapi(self.corpus) if self.corpus else None

    def retrieve(self, query: str, top_k: int = 3) -> List[EvidenceItem]:
        if not self.docs or self.bm25 is None:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        items: List[EvidenceItem] = []
        for idx, score in ranked:
            text = self.docs[idx]["text"]
            snippet = text[:220].replace("\n", " ")
            items.append(
                EvidenceItem(
                    evidence_id=f"EV-{idx+1:03d}",
                    source_name=self.docs[idx]["source_name"],
                    snippet=snippet,
                    score=float(score),
                    metadata={},
                )
            )
        return items
