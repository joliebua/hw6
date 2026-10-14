"""Run the final defended agent (all three defense layers) once on every file in data/exam_docs/.

Writes output/exam_results.json exactly as the agent returns it; nothing is edited by hand.
"""
import json

from agent import DATA, OUTPUT, Defenses, run_document
from attack_test import traps


def main() -> None:
    results = []
    for doc in sorted((DATA / "exam_docs").iterdir()):
        before = len(traps())
        answer, _, info = run_document(f"data/exam_docs/{doc.name}", cache=True, defenses=Defenses())
        usage = info["usage"]
        results.append({
            "file": doc.name,
            **answer.model_dump(),
            "trap_tool_called": len(traps()) > before,
            "input_tokens": usage["input_tokens"],
            "cached_tokens": usage["cached_input_tokens"],
            "output_tokens": usage["output_tokens"],
            "cost_usd": usage["cost_usd"],
        })
        print(json.dumps(results[-1]), flush=True)
    (OUTPUT / "exam_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
