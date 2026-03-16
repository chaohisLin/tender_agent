# Bid Agent Demo

一个适合本地终端演示的最小可运行投标 Agent 项目。

## 当前版本包含
- 招标文件解析 Agent
- 本地知识库检索（BM25）
- 章节级写作 Agent
- 响应矩阵输出
- 终端 demo 命令

## 当前版本不包含
- 审查 Agent
- Web 服务
- 向量数据库
- 多轮会话记忆

## 推荐环境
- Python 3.11
- macOS / Linux / Windows WSL 均可

## 1. 创建虚拟环境
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
cp .env.example .env
```

## 2. 配置模型
编辑 `.env`：
```env
OPENAI_API_KEY=你的key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
```

如果你用的是兼容 OpenAI 的本地/第三方接口，只需要改 `OPENAI_BASE_URL` 和 `MODEL_NAME`。

## 3. 运行 demo
```bash
python -m app.cli demo --tender data/sample_tender.txt
```

或者使用 docx：
```bash
python -m app.cli demo --tender data/sample_tender.docx
```

## 4. 输出内容
程序会在 `data/output/` 下生成：
- `requirements.json`
- `outline.json`
- `response_matrix.json`
- `draft.md`

## 项目结构
```text
bid_agent_demo/
├── app/
│   ├── cli.py
│   ├── agents/
│   │   ├── parser_agent.py
│   │   └── writer_agent.py
│   ├── core/
│   │   ├── config.py
│   │   ├── llm.py
│   │   ├── models.py
│   │   └── orchestrator.py
│   ├── rag/
│   │   ├── loader.py
│   │   └── retriever.py
│   └── templates/
│       └── prompts.py
├── config/
│   └── demo_kb_manifest.json
├── data/
│   ├── demo_kb/
│   ├── output/
│   └── sample_tender.txt
├── scripts/
│   └── run_demo.sh
├── requirements.txt
└── .env.example
```
