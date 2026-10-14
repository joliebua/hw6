# MGT 409 · Homework 6 — Campus Customs Vendor Desk Agent

A PydanticAI agent (`gpt-6-luna` via Portkey) that reads one vendor document (HTML, PDF, or `.eml` email), extracts vendor, SKU, unit price, lead time, and minimum order, and decides `recommend` / `do_not_recommend` using the rules in `data/shop_handbook.md`. It has three layers of prompt-injection defenses (code, design, prompt) and two trap tools (`send_email`, `approve_payment`) that never send or pay anything. They only log attempts to `output/trap_calls.json`.

**Start with the report:** open `output/hw6_report.html` in any browser (it works offline).

## Run the agent

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # then put your Portkey key in .env
python agent.py --doc data/practice_docs/p01_bluehen_quote.html
```

Options:

| Command | What it does |
|---|---|
| `python agent.py --doc <file>` | Final agent with **all defenses** on (default) |
| `python agent.py --doc <file> --defenses none` | The undefended Problem 3 agent |
| `python agent.py --doc <file> --defenses code,prompt` | Any mix of `code`, `design`, `prompt` |
| `python agent.py --doc <file> --no-cache` | Make every model call uncacheable (cache test) |

Every run prints the answer as JSON and appends to `output/usage_log.json` (tokens and cost) and `output/audit_trail.json` (tool calls, what the sanitizer removed, and the final answer).

## Reproduce each problem

| Problem | Script | Output |
|---|---|---|
| 1. Handbook tokens and cost | `python count_handbook_tokens.py` | `output/handbook_estimate.md` |
| 2. Agent harness | `python agent.py --doc …` | `output/harness.md` |
| 3. Cache test | `python cache_test.py` | `output/cache_test.json`, `.md` |
| 4. Attack test | `python attack_test.py` | `output/attack_results.json`, `.md` |
| 5. Defenses | `python defense_test.py` | `output/defense_results.json`, `.md` |
| 6. Red team | `python make_attacks.py` then `python red_team_test.py` | `data/my_attacks/`, `output/red_team.md` |
| 7. Exam | `python exam_run.py` | `output/exam_results.json` |
| 8. Report | `python build_report.py` | `output/hw6_report.html` |

`AI_prompts.md` logs every prompt used to build this homework.

## Layout

- `agent.py`, `tools.py`, `models.py`, `prompts/prompt.md`: the agent. `prompts/prompt_baseline.md` is the undefended prompt, and `prompts/extract.md` is the fact-only prompt used by the design layer.
- `data/`: the course data (handbook, prices, practice key, `practice_docs/`, `exam_docs/`) plus `my_attacks/` (the two red-team documents and their answer key).
- `output/`: every result file, plus `human_view/` (how each document looks to a person) and `agent_view/` (the text the agent read).
