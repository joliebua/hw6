# Handbook Token & Cost Estimate

**File:** `data/shop_handbook.md` (Campus Customs Shop Handbook, v2026.10)
**Model:** `gpt-6-luna`
**Prices:** `data/prices.json`

## 1. Token count: **10,058 tokens**

I counted the handbook two independent ways, and both gave the same number.

| Method | How | Result |
|---|---|---|
| Offline tokenizer | Read the file and encoded it with `tiktoken`'s `o200k_base` encoding (the tokenizer used by OpenAI's GPT-4o/GPT-5-family models) | **10,058 tokens** (28,903 characters) |
| Live API measurement | Sent `gpt-6-luna` (via Portkey) a call with an **empty** system message, then a call with the **handbook** as the system message, both with the same user message. Read `usage.prompt_tokens` from each response and subtracted. | 10,073 − 15 = **10,058 tokens** |

The live API check matters because it shows the number `gpt-6-luna` actually bills, not just what a tokenizer predicts. The 15 baseline tokens are message formatting plus the short user message. They are not part of the handbook.

Rule-of-thumb check: 28,903 characters ÷ ~4 characters per token ≈ 7,226 tokens. The real count is about 39% higher, because the handbook has many tables, pipes, codes, emails, and numbers, and those tokenize less efficiently than plain prose. This is why I measured the count instead of estimating it.

Script: `count_handbook_tokens.py`. Output from the run:

```
tiktoken o200k_base: 10058 tokens (28903 characters)
API baseline prompt (empty system message): 15 tokens
API prompt with handbook, call 1: 10073 tokens (0 cached)
API prompt with handbook, call 2: 10073 tokens (10070 cached)
Handbook as billed by gpt-6-luna: 10058 tokens
```

The second call shows caching working in practice: 10,070 of the 10,073 prompt tokens were served from cache.

## 2. Prices (per 1M tokens, from `prices.json`)

| Price type | $ per 1M tokens | $ per token |
|---|---|---|
| Input (uncached) | $0.10 | $0.0000001 |
| Cached input (cache hit) | $0.01 | $0.00000001 |
| Cache write | $0.125 | $0.000000125 |
| Output | $0.50 | *(not used; this estimate covers only the handbook, which is input)* |

Formula: **cost = tokens × (price per 1M ÷ 1,000,000)**

## 3. Cost of the handbook alone

### Without caching

Every call pays the full input price for all 10,058 tokens.

- **One call:** 10,058 × $0.10 ÷ 1,000,000 = **$0.0010058** (about $0.001, a tenth of a cent)
- **1,000 calls:** 1,000 × $0.0010058 = **$1.0058** (about **$1.01**)

### With caching

The first call writes the handbook into the cache at the cache-write price. Every later call that reuses the same prefix reads it at the cached-input price.

- **Cache write (first call):** 10,058 × $0.125 ÷ 1,000,000 = **$0.00125725**
- **Cache hit (each later call):** 10,058 × $0.01 ÷ 1,000,000 = **$0.00010058**

**One call:**
- If it is the first call (cache write): **$0.00125725**. This is slightly *more* than uncached ($0.0010058), because writing to the cache costs a premium.
- If it is a repeat call (cache hit): **$0.00010058**, 10× cheaper than uncached.

**1,000 calls** (1 cache write + 999 cache hits):

```
  1 × $0.00125725  = $0.00125725
999 × $0.00010058  = $0.10047942
                     -----------
Total              = $0.10173667  ≈ $0.10
```

### Summary

| Scenario | 1 call | 1,000 calls |
|---|---|---|
| Without caching | $0.0010058 | **$1.0058** (≈ $1.01) |
| With caching | $0.00125725 (first call, cache write) / $0.00010058 (cache hit) | **$0.10173667** (≈ $0.10) |
| **Savings from caching** | | $1.0058 − $0.1017 = **$0.9041 (≈ 89.9% cheaper)** |

## Assumptions

- **Handbook only.** These figures leave out the vendor document, the instructions, and the model's output tokens on each call. A real call will cost more.
- **The cache stays warm.** The 1,000 calls happen close enough together that the cache doesn't expire. If it expires, each refill costs one more cache write ($0.00125725).
- **The handbook comes first in the prompt.** Caching only matches an identical prefix, so the handbook must be sent at the start of every call (for example, as the system message), before anything that changes from call to call. It is also well over the 1,024-token minimum that caching requires.
- **Cache-write pricing.** I charged the cache-write price from `prices.json` on the first call. In the live test the cache read showed up in the usage numbers, but the API doesn't report write charges separately. If writes were actually billed at the normal input price, the 1,000-call cached total would be $0.0010058 + $0.10047942 = $0.10148522. The difference is negligible.
