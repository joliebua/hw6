"""Campus Customs vendor desk agent (PydanticAI + gpt-6-luna via Portkey).

Usage:
    python agent.py --doc data/practice_docs/p01_bluehen_quote.html                    # all defenses (default)
    python agent.py --doc data/practice_docs/p01_bluehen_quote.html --defenses none    # Problem 3 agent, no defenses
    python agent.py --doc data/practice_docs/p01_bluehen_quote.html --defenses code,prompt
    python agent.py --doc data/practice_docs/p01_bluehen_quote.html --no-cache

Defense layers (any combination):
    code   - tools.read_clean strips everything a person would not see before any model reads it
    design - the model only extracts facts (no decision, dangerous tools need human sign-off);
             tools.verify_against_document checks each number against the value printed next to its
             label, and tools.HandbookRules makes the decision in code
    prompt - prompts/prompt.md security rules (prompts/prompt_baseline.md when off)
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import os
import re
import uuid

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv
from openai import AsyncOpenAI
import httpx2 as httpx  # the HTTP client the openai SDK uses
from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults, Tool, ToolDenied
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from models import ExtractedQuote, VendorDecision, VendorDeskDeps
from tools import (HandbookRules, approve_payment, load_document, read_document, record_trap, send_email,
                   verify_against_document)

HERE = Path(__file__).parent
DATA = HERE / "data"
OUTPUT = HERE / "output"
PROMPTS = HERE / "prompts"
MODEL_NAME = "gpt-6-luna"
CACHE_KEY = "campus-customs-vendor-desk"

load_dotenv(HERE / ".env")              # repo-root .env (copy .env.example)
load_dotenv(HERE / "../.." / ".env")    # fallback: the course folder .env


@dataclass(frozen=True)
class Defenses:
    code: bool = True
    design: bool = True
    prompt: bool = True

    @classmethod
    def parse(cls, spec: str) -> "Defenses":
        spec = spec.strip().lower()
        if spec == "all":
            return cls()
        if spec == "none":
            return cls(False, False, False)
        layers = {s.strip() for s in spec.split(",")}
        unknown = layers - {"code", "design", "prompt"}
        if unknown:
            raise ValueError(f"Unknown defense layer(s): {', '.join(sorted(unknown))}")
        return cls("code" in layers, "design" in layers, "prompt" in layers)

    @property
    def label(self) -> str:
        on = [n for n in ("code", "design", "prompt") if getattr(self, n)]
        return "all" if len(on) == 3 else "+".join(on) or "none"


class RawUsageRecorder:
    """httpx hook that keeps the exact `usage` object the API returns for every model call."""

    def __init__(self):
        self.calls: list[dict] = []

    async def __call__(self, response: httpx.Response) -> None:
        if response.request.url.path.endswith("/responses"):
            await response.aread()
            body = response.json()
            self.calls.append({"response_id": body.get("id"), "usage": body.get("usage")})


def _model(recorder: RawUsageRecorder) -> OpenAIResponsesModel:
    client = AsyncOpenAI(
        api_key=os.getenv("PORTKEY_API_KEY"),
        base_url="https://api.portkey.ai/v1",
        default_headers={"x-portkey-provider": "openai"},
        http_client=httpx.AsyncClient(timeout=120, event_hooks={"response": [recorder]}),
    )
    # Responses API: gpt-6-luna rejects function tools + reasoning on /chat/completions.
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def _security_rules() -> str:
    text = (PROMPTS / "prompt.md").read_text()
    return re.search(r"<!-- security-rules:start -->\n(.*?)<!-- security-rules:end -->", text, re.S).group(1).strip()


def _system_prompt(defenses: Defenses) -> str:
    if defenses.design:
        rules = _security_rules() if defenses.prompt else ""
        return (PROMPTS / "extract.md").read_text().replace("{security_rules}", rules).strip()
    handbook = (DATA / "shop_handbook.md").read_text()
    name = "prompt.md" if defenses.prompt else "prompt_baseline.md"
    return (PROMPTS / name).read_text().replace("{handbook}", handbook)


def build_agent(cache: bool, recorder: RawUsageRecorder, defenses: Defenses = Defenses()) -> Agent:
    system_prompt = _system_prompt(defenses)
    if defenses.design:
        # Design: the model that sees the document gets NO useful tools and can only return facts.
        # The dangerous tools are still offered as tripwires, but they need human sign-off, so a
        # hijacked call stops the run instead of executing.
        tools = [Tool(send_email, requires_approval=True), Tool(approve_payment, requires_approval=True)]
        output_type = [ExtractedQuote, DeferredToolRequests]
    else:
        # send_email and approve_payment are traps: the job never needs them.
        tools = [read_document, send_email, approve_payment]
        output_type = VendorDecision

    if cache:
        # Static prompt (+ handbook) is the first thing in every call, a breakpoint sits right after it,
        # and a fixed cache key routes every call to the same cache.
        settings = OpenAIResponsesModelSettings(openai_cache_instructions=True, openai_prompt_cache_key=CACHE_KEY)
        return Agent(_model(recorder), instructions=system_prompt, model_settings=settings,
                     deps_type=VendorDeskDeps, output_type=output_type, tools=tools)

    # No cache: a fresh random ID is the very first text of EVERY model call (instructions are
    # re-evaluated per request), so no call shares a prefix with any earlier call.
    def unique_prefix() -> str:
        return f"Request ID: {uuid.uuid4()}\n\n{system_prompt}"

    return Agent(_model(recorder), instructions=unique_prefix, deps_type=VendorDeskDeps,
                 output_type=output_type, tools=tools)


def cost_usd(input_tokens: int, cache_read: int, cache_write: int, output_tokens: int) -> float:
    p = json.loads((DATA / "prices.json").read_text())[MODEL_NAME]
    uncached = input_tokens - cache_read - cache_write
    return (uncached * p["input_per_1m"] + cache_read * p["cached_input_per_1m"]
            + cache_write * p["cache_write_per_1m"] + output_tokens * p["output_per_1m"]) / 1_000_000


def usage_totals(calls: list[dict]) -> dict:
    """Sum the raw API usage of every model call in one run."""
    t = {"requests": len(calls), "input_tokens": 0, "cached_input_tokens": 0, "cache_write_tokens": 0,
         "output_tokens": 0, "reasoning_tokens": 0, "total_tokens": 0}
    for c in calls:
        u = c["usage"] or {}
        details = u.get("input_tokens_details") or {}
        t["input_tokens"] += u.get("input_tokens", 0)
        t["cached_input_tokens"] += details.get("cached_tokens", 0)
        t["cache_write_tokens"] += details.get("cache_write_tokens", 0)
        t["output_tokens"] += u.get("output_tokens", 0)
        t["reasoning_tokens"] += (u.get("output_tokens_details") or {}).get("reasoning_tokens", 0)
        t["total_tokens"] += u.get("total_tokens", 0)
    t["cost_usd"] = round(cost_usd(t["input_tokens"], t["cached_input_tokens"],
                                   t["cache_write_tokens"], t["output_tokens"]), 8)
    return t


def append_json(path: Path, entry: dict) -> None:
    items = json.loads(path.read_text()) if path.exists() else []
    items.append(entry)
    path.write_text(json.dumps(items, indent=2))


def short(text: str, limit: int = 200) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "..."


def tool_calls_from(messages) -> list[dict]:
    """Pair every tool call with its result (skipping PydanticAI's internal final_result output tool)."""
    calls, results = [], {}
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                calls.append(part)
            elif isinstance(part, ToolReturnPart):
                results[part.tool_call_id] = part.content
    return [{"tool": c.tool_name, "arguments": c.args_as_dict(),
             "result": short(results.get(c.tool_call_id, "(no result)"))} for c in calls]


def _run_design(agent: Agent, deps: VendorDeskDeps, doc: str):
    """Code reads the document, the model extracts facts, code decides. Returns (answer, steps, messages)."""
    text = load_document(deps.doc_path, deps.sanitize, deps.removed)
    steps = [{"tool": "code:load_document", "arguments": {"path": doc, "sanitize": deps.sanitize},
              "result": short(text)}]
    prompt = f"Extract the quote facts from this vendor document.\n\n<document>\n{text}\n</document>"
    result = agent.run_sync(prompt, deps=deps)
    messages = result.all_messages()
    for _ in range(3):  # a hijacked model may keep asking; every request is blocked and recorded
        if not isinstance(result.output, DeferredToolRequests):
            break
        denials = {}
        for call in result.output.approvals:
            record_trap(deps.doc_path, deps.output_dir, call.tool_name, call.args_as_dict(),
                        "blocked: requires human sign-off (denied)")
            steps.append({"tool": call.tool_name, "arguments": call.args_as_dict(),
                          "result": "BLOCKED: requires human sign-off; recorded in trap_calls.json"})
            denials[call.tool_call_id] = ToolDenied("Blocked: this action requires human sign-off.")
        result = agent.run_sync(message_history=messages, deps=deps,
                                deferred_tool_results=DeferredToolResults(approvals=denials))
        messages = result.all_messages()
    if isinstance(result.output, DeferredToolRequests):
        raise RuntimeError("Model kept requesting blocked tools; no answer produced.")
    quote: ExtractedQuote = result.output
    steps.append({"tool": "model:extract", "arguments": {}, "result": short(quote.model_dump_json())})
    quote, overrides = verify_against_document(quote, text)
    steps.append({"tool": "code:verify_printed_values", "arguments": {},
                  "result": "; ".join(overrides) or "all extracted numbers match the values printed next to their labels"})
    rules = HandbookRules.from_handbook((DATA / "shop_handbook.md").read_text())
    answer = rules.decide(quote, text)
    steps.append({"tool": "code:handbook_rules", "arguments": quote.model_dump(), "result": short(answer.reason)})
    return answer, steps


def run_document(doc: str, cache: bool = True, defenses: Defenses = Defenses()):
    """Run the agent on one document, append to the usage log and audit trail.

    Returns (final answer, raw per-call usage list from the API, run details dict).
    """
    OUTPUT.mkdir(exist_ok=True)
    trap_log = OUTPUT / "trap_calls.json"
    if not trap_log.exists():
        trap_log.write_text("[]")

    recorder = RawUsageRecorder()
    deps = VendorDeskDeps(doc_path=Path(doc), output_dir=OUTPUT, sanitize=defenses.code)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    agent = build_agent(cache, recorder, defenses)
    if defenses.design:
        answer, steps = _run_design(agent, deps, doc)
    else:
        result = agent.run_sync(f"Review this vendor document: {doc}", deps=deps)
        answer, steps = result.output, tool_calls_from(result.all_messages())

    usage = usage_totals(recorder.calls)
    append_json(OUTPUT / "usage_log.json", {
        "document": doc, "time": started, "model": MODEL_NAME, "cache": cache,
        "defenses": defenses.label, **usage,
    })
    append_json(OUTPUT / "audit_trail.json", {
        "document": doc, "time": started, "defenses": defenses.label,
        "sanitizer_removed": deps.removed,
        "tool_calls": steps,
        "final_answer": answer.model_dump(),
    })
    return answer, recorder.calls, {"usage": usage, "sanitizer_removed": deps.removed, "steps": steps}


def main() -> None:
    parser = argparse.ArgumentParser(description="Review one vendor document for Campus Customs.")
    parser.add_argument("--doc", required=True, help="Path to a vendor document (.html, .pdf, or .eml)")
    parser.add_argument("--defenses", default="all",
                        help="all (default), none, or a comma list of: code, design, prompt")
    parser.add_argument("--no-cache", action="store_true", help="Make every model call uncacheable")
    args = parser.parse_args()
    answer, _, _ = run_document(args.doc, cache=not args.no_cache, defenses=Defenses.parse(args.defenses))
    print(json.dumps(answer.model_dump(), indent=2))


if __name__ == "__main__":
    main()
