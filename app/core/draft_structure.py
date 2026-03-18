from __future__ import annotations

import re

from app.core.models import DraftBlock


def parse_markdown_to_blocks(markdown: str) -> list[DraftBlock]:
    lines = markdown.strip().splitlines() if markdown.strip() else []
    blocks: list[DraftBlock] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue

        if _is_table_line(stripped):
            table_lines = []
            while i < len(lines) and _is_table_line(lines[i].strip()):
                table_lines.append(lines[i].strip())
                i += 1
            rows = [_split_table_row(line) for line in table_lines if not _is_separator_row(line)]
            if rows:
                blocks.append(DraftBlock(block_type="table", rows=rows))
            continue

        if re.match(r"^-{3,}$", stripped):
            i += 1
            continue

        heading = _parse_heading(stripped)
        if heading:
            blocks.append(heading)
            i += 1
            continue

        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            blocks.append(DraftBlock(block_type="bullet_list", items=items))
            continue

        number_match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if number_match:
            rows: list[list[str]] = []
            while i < len(lines):
                current = lines[i].strip()
                item_match = re.match(r"^(\d+)\.\s+(.+)$", current)
                if not item_match:
                    break
                number = item_match.group(1)
                title = item_match.group(2).strip()
                i += 1

                body_lines: list[str] = []
                while i < len(lines):
                    nxt = lines[i].strip()
                    if not nxt:
                        i += 1
                        if body_lines:
                            break
                        continue
                    if (
                        _is_table_line(nxt)
                        or _parse_heading(nxt)
                        or re.match(r"^[-*]\s+", nxt)
                        or re.match(r"^\d+\.\s+", nxt)
                        or re.match(r"^-{3,}$", nxt)
                    ):
                        break
                    body_lines.append(nxt)
                    i += 1
                rows.append([number, title, "\n".join(body_lines).strip()])
            blocks.append(DraftBlock(block_type="number_list", rows=rows))
            continue

        paragraph_lines = []
        while i < len(lines):
            current = lines[i].strip()
            if not current:
                break
            if _is_table_line(current) or _parse_heading(current) or re.match(r"^[-*]\s+", current) or re.match(r"^\d+\.\s+", current) or re.match(r"^-{3,}$", current):
                break
            paragraph_lines.append(current)
            i += 1
        if paragraph_lines:
            blocks.append(DraftBlock(block_type="paragraph", text="\n".join(paragraph_lines)))
        else:
            i += 1
    return blocks


def _parse_heading(line: str) -> DraftBlock | None:
    m = re.match(r"^(#{1,6})\s*(.+)$", line)
    if m:
        text = _strip_inline_marks(m.group(2).strip())
        return DraftBlock(block_type="heading", level=max(1, len(m.group(1)) - 1), text=text)

    m = re.match(r"^\*\*(.+)\*\*$", line) or re.match(r"^__(.+)__$", line)
    if m:
        inner = m.group(1).strip()
        num = re.match(r"^(\d+(?:\.\d+)*)[\.]?\s+(.+)$", inner)
        if num:
            return DraftBlock(
                block_type="heading",
                level=max(1, len(num.group(1).split("."))),
                number=num.group(1),
                text=_strip_inline_marks(num.group(2).strip()),
            )
        return DraftBlock(block_type="heading", level=1, text=_strip_inline_marks(inner))

    m = re.match(r"^(\d+\.\d+(?:\.\d+)*)\s+(.+)$", line)
    if m:
        text = m.group(2).strip()
        if not _looks_like_heading_text(text):
            return None
        return DraftBlock(
            block_type="heading",
            level=max(1, len(m.group(1).split("."))),
            number=m.group(1),
            text=_strip_inline_marks(text),
        )

    return None


def _looks_like_heading_text(text: str) -> bool:
    plain = re.sub(r"[*_`#]", "", text).strip()
    if len(plain) > 28:
        return False
    if re.search(r"[。；：？！]$", plain):
        return False
    return True


def _strip_inline_marks(text: str) -> str:
    text = re.sub(r"^\*\*(.+)\*\*$", r"\1", text)
    text = re.sub(r"^__(.+)__$", r"\1", text)
    return text.strip()


def _is_table_line(line: str) -> bool:
    return line.startswith("|") and line.endswith("|") and line.count("|") >= 2


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip("|").split("|")]


def _is_separator_row(line: str) -> bool:
    return all(part.strip().replace("-", "").replace(":", "") == "" for part in line.strip("|").split("|"))
