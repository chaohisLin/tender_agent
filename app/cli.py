from __future__ import annotations
from dotenv import load_dotenv
load_dotenv(override=True)  # override=True 的意思是：不管系统里有什么，强行用我的 .env 覆盖！

from pathlib import Path
import json
import typer
from rich import print
from app.core.config import get_settings
from app.core.orchestrator import BidDemoOrchestrator

app = typer.Typer(help="本地终端投标 Agent Demo")


@app.command()
def demo(tender: str = typer.Option(..., help="招标文件路径，支持 txt/docx/pdf")):
    settings = get_settings()
    orchestrator = BidDemoOrchestrator(settings)
    result = orchestrator.run(Path(tender))
    print("[green]生成完成[/green]")
    print(f"requirements: {len(result['requirements'])}")
    print(f"outline sections: {len(result['outline'])}")
    print(f"draft sections: {len(result['drafts'])}")
    print("\n[yellow]章节预览[/yellow]")
    for draft in result["drafts"]:
        print(f"\n[bold]{draft['title']}[/bold]")
        print(draft["content"][:300] + ("..." if len(draft["content"]) > 300 else ""))
    print("\n[cyan]响应矩阵预览[/cyan]")
    print(json.dumps(result["response_matrix"][:5], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
