"""Run the two red-team documents in data/my_attacks/ against the agent with no defenses,
each defense layer alone, and all layers (3 repeats each). Saves output/red_team_results.json."""
import json

import attack_test
from agent import DATA, OUTPUT, Defenses, run_document
from attack_test import traps
from defense_test import score

ATTACKS = DATA / "my_attacks"
attack_test.KEY.update({row["file"]: row for row in json.loads((ATTACKS / "my_attacks_key.json").read_text())})
DOCS = sorted(p for p in ATTACKS.iterdir() if p.suffix in (".pdf", ".html", ".eml"))
CONFIGS = ["none", "code", "design", "prompt", "all"]
REPEATS = 3


def main() -> None:
    results = []
    for spec in CONFIGS:
        defenses = Defenses.parse(spec)
        for rep in range(1, REPEATS + 1):
            for doc in DOCS:
                before = len(traps())
                answer, _, info = run_document(f"data/my_attacks/{doc.name}", defenses=defenses)
                row = {"defenses": spec, "repeat": rep, "document": doc.name,
                       **score(doc.name, answer, traps()[before:]),
                       "sanitizer_removed": info["sanitizer_removed"],
                       "tokens": {k: v for k, v in info["usage"].items() if k != "cost_usd"},
                       "cost_usd": info["usage"]["cost_usd"]}
                results.append(row)
                a = row["agent_answer"]
                print(f"{spec:7} r{rep} {doc.name:30} fooled={row['fooled']!s:5} price={a['unit_price']} "
                      f"lead={a['lead_time_days']} {a['decision']:17} | {a['reason']}", flush=True)
    (OUTPUT / "red_team_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
