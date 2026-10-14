"""Run the vendor desk agent on all 12 practice documents, without and with prompt caching.

Saves every model call (raw API token counts + cost from prices.json) to output/cache_test.json.
"""
from pathlib import Path
import json

from agent import DATA, OUTPUT, Defenses, cost_usd, run_document

DOCS = sorted((DATA / "practice_docs").iterdir())
KEY = {row["file"]: row for row in json.loads((DATA / "practice_key.json").read_text())}
FIELDS = ["vendor", "sku", "unit_price", "lead_time_days", "min_order", "decision"]


def main() -> None:
    records = []
    for setup, cache in (("without_cache", False), ("with_cache", True)):
        for doc in DOCS:
            rel = f"data/practice_docs/{doc.name}"
            answer, calls, _ = run_document(rel, cache=cache, defenses=Defenses.parse("none"))
            key = KEY[doc.name]
            correct = {f: getattr(answer, f) == key[f] for f in FIELDS}
            for i, call in enumerate(calls, 1):
                u = call["usage"]
                details = u.get("input_tokens_details") or {}
                cached = details.get("cached_tokens", 0)
                written = details.get("cache_write_tokens", 0)
                records.append({
                    "setup": setup,
                    "document": doc.name,
                    "call": i,
                    "response_id": call["response_id"],
                    "usage": u,  # exactly as the API returned it
                    "uncached_input_tokens": u["input_tokens"] - cached - written,
                    "cost_usd": round(cost_usd(u["input_tokens"], cached, written, u["output_tokens"]), 8),
                    "decision": answer.decision,
                    "all_fields_match_key": all(correct.values()),
                })
            print(f"{setup:14} {doc.name:28} calls={len(calls)} decision={answer.decision:17} "
                  f"match={all(correct.values())} cached={[c['usage']['input_tokens_details']['cached_tokens'] for c in calls]}")
    (OUTPUT / "cache_test.json").write_text(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
