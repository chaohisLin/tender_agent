from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv
from rich import print

from app.core.config import get_settings
from app.core.orchestrator import BidDemoOrchestrator


load_dotenv(override=True)


def run_demo(tender: Path) -> dict:
    settings = get_settings()
    orchestrator = BidDemoOrchestrator(settings)
    result = orchestrator.run(tender)

    print("[green]生成完成[/green]")
    print(f"requirements: {len(result['requirements'])}")
    print(f"outline sections: {len(result['outline'])}")
    print(f"draft sections: {len(result['drafts'])}")

    print("\n[yellow]章节预览[/yellow]")
    for draft in result["drafts"]:
        print(f"\n[bold]{draft['title']}[/bold]")
        preview = draft["content"][:300]
        if len(draft["content"]) > 300:
            preview += "..."
        print(preview)

    print("\n[cyan]响应矩阵预览[/cyan]")
    print(json.dumps(result["response_matrix"][:5], ensure_ascii=False, indent=2))
    return result


def run_refresh(tender: Path | None = None) -> dict:
    settings = get_settings()
    resolved_tender = tender or _load_last_tender_path(settings.output_dir)
    if resolved_tender is None:
        raise FileNotFoundError("未找到可用于重生成的 tender 路径，请通过 --tender 显式传入。")

    print(f"[blue]全量刷新输出[/blue] -> {resolved_tender}")
    return run_demo(resolved_tender)


def _load_last_tender_path(output_dir: Path) -> Path | None:
    draft_json = output_dir / "draft.json"
    if not draft_json.exists():
        return None
    payload = json.loads(draft_json.read_text(encoding="utf-8"))
    tender_path = str(payload.get("tender_path", "")).strip()
    if not tender_path:
        return None
    return Path(tender_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本地终端投标 Agent Demo")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="生成投标初稿与过程文件")
    demo_parser.add_argument("--tender", required=True, help="招标文件路径，支持 txt/docx/pdf")

    refresh_parser = subparsers.add_parser("refresh", help="按 tender 全量同步刷新 output 下所有文件")
    refresh_parser.add_argument("--tender", help="招标文件路径；不传则尝试从 data/output/draft.json 中读取上次路径")

    parser.add_argument(
        "--tender",
        help="直接运行 demo；等价于 `python -m app.cli demo --tender <path>`",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "command", None) == "demo":
        run_demo(Path(args.tender))
        return 0

    if getattr(args, "command", None) == "refresh":
        tender = Path(args.tender) if getattr(args, "tender", None) else None
        run_refresh(tender)
        return 0

    if getattr(args, "tender", None):
        run_demo(Path(args.tender))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
