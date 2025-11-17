# Athena v1

Personal AI assistant with:

- Single-agent orchestration over tools
- Structured memory in a relational DB (SQLite / Postgres)
- Basic semantic memory scaffolding
- Clean tool registry / auto-discovery

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -r requirements.txt

export OPENAI_API_KEY=your_key_here

python -m athena.api.cli
