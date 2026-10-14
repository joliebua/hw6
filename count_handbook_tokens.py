"""Count tokens in the Campus Customs handbook two ways:
1. Offline with tiktoken (o200k_base, the GPT-4o/GPT-5-family tokenizer).
2. Live: ask gpt-6-luna and read the prompt_tokens it bills, minus a baseline call.
"""
from pathlib import Path
import os

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")              # repo-root .env (copy .env.example)
load_dotenv(HERE / "../.." / ".env")    # fallback: the course folder .env
handbook = (HERE / "data" / "shop_handbook.md").read_text()

offline = len(tiktoken.get_encoding("o200k_base").encode(handbook))
print(f"tiktoken o200k_base: {offline} tokens ({len(handbook)} characters)")

client = OpenAI(
    api_key=os.getenv("PORTKEY_API_KEY"),
    base_url="https://api.portkey.ai/v1",
    default_headers={"x-portkey-provider": "openai"},
)


def prompt_usage(system_text):
    response = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": "Reply with exactly: OK"},
        ],
        max_completion_tokens=20,
    )
    details = response.usage.prompt_tokens_details
    cached = details.cached_tokens if details else 0
    return response.usage.prompt_tokens, cached


baseline, _ = prompt_usage("")
with_handbook, cached_1 = prompt_usage(handbook)
repeat, cached_2 = prompt_usage(handbook)

print(f"API baseline prompt (empty system message): {baseline} tokens")
print(f"API prompt with handbook, call 1: {with_handbook} tokens ({cached_1} cached)")
print(f"API prompt with handbook, call 2: {repeat} tokens ({cached_2} cached)")
print(f"Handbook as billed by gpt-6-luna: {with_handbook - baseline} tokens")
