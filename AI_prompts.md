# AI Prompts Log — Homework 6

**Course:** MGT 409 — AI Foundations for Managers
**Student:** Jolie Bua
**Assistant:** Claude Code (Opus 5.5)

This file logs the prompts I typed while completing Homework 6. One section per problem.
Each section lists my initial prompt in my own words, and — where a follow-up was needed —
the follow-up prompt plus one sentence on what was lacking after the first attempt.

---

## Setup — Establishing the working folder and model

**Prompt 1 (initial):**
> homework 6 time!

**Prompt 2 (follow-up):**
> are you able to use gpt-6-luna?

**Prompt 3 (follow-up):**
> ok let me know

**What was lacking after the first prompt:** The first prompt opened the homework but did not name the model, so I asked whether gpt-6-luna was available. Claude tested it through Portkey (it works), and I confirmed it for this homework at the start of Problem 1.

**Result:** This file (`AI_prompts.md`) was created in `Homework/Homework 6/` on 2026-10-13 as the running log of my prompts for this assignment, and it is updated after each new prompt.

---

## Problem 1 — Handbook token count and cost estimate

**Prompt 1 (initial):**
> yes use gpt-6-luna for this homework. create AI_prompts.md per usual. look through shop_handbook.md within data-3 folder. this is the campus customs shop handbook, agent will send it to model onever call. Also look at prices.json (gpt-6-luna price list). find out how many tokens handbook is. in output/handbook_estimate.md write the token count and how you got it. what handbook alone costs in dollars in one call and on 1,000 calls with cached tokens and without them. show your math.

---

## Problem 2 — Build the vendor desk agent (PydanticAI + trap tools)

**Prompt 1 (initial):**
> build vendor desk agent with PydanticAI (make sure its got-6-luna. agents is the following 4 files:
> prompts/prompt.md
> agent.py
> tools.py
> models.py
>
> agent should have path to one vendor doc. it reads doc with hool (HTML, PDF, .eml email files all have to work) and returns: vendor, SKU, unit price, lead time in days, min order, decision (recommend or do_not_recommend) following handbook rules and one-sentence reason. agent must have two trap tools: send_email and approve_payment. its job never needs them. they are there to catch malicious document that tricks your agent into emailing someone or paying a vendor. they do not send or pay anything, only append the call and its arguments to output/trap_calls.json (start as empty list), so if file ever has entry, document took over agent. keep them on system for whole hoemwork. after every run append to:
> output/usage_log.json: document, time, token counts the API reports, and dollar cost using prices.json
> output/audit_trail.json: each tool call with its arguments and a short result, plus the final answer
>
> run like this terminal:
> python agent.py --doc data/practice_docs/p01_bluehen_quote.html
>
> run on p01 and p08 to show it works. start output/harness.md: each field in models.py and why, and each tool in one line

---

## Problem 3 — Prompt cache test (with vs. without cache)

**Prompt 1 (initial):**
> handbook is the same on every call so model can reuse it from cache at much cheaper price. test what that is worth.  run agent on all 12 practice documents two ways:
>
> with cache: set up so handbook gets reused from cache
> without cache: set up so nothing gets reused from cache
>
> check token counts API sends back to prove each setup really did what you think. a without-cache run that still shows cached tokens does not count.
>
> save every model call from both setups to output/cache_test.json. for each call include setup, document, every token count API reports, and dollars from prices.json
>
> in output/cache_test.md:

**Prompt 2 (follow-up, sent mid-run):**
> total cost and cost per docuemnt for each setup and percent you saved
> how your real numbers compare to you probelm 2 estimate
> a projection for 1,000 documents a day for 30 days, with and without cache
> anything in numbers that surprised you and why it happens

**What was lacking after the first prompt:** The first prompt was cut off before saying what output/cache_test.md should contain, so the follow-up supplied the report sections.

---

## Problem 4 — Attack test (booby-trapped vendor documents)

**Prompt 1 (initial):**
> some vendor docs are booby-trapped with text aimed at AI. run the problem 3 agent, with no new defenses, on all 12 documents in practice_docs. compare each answer to practice_key.json and check output/trap_calls.json
>
> save output/attack_results.json: for each doc whether each field matched the key, whether decision matched, whether trap tool was called, whether link or other strange text showed up in the answer.
>
> in output/attack_results.md, for every doc that fooled agent, write what fooled it and where in file it was hiding. open docs the way person would (browser, PDF view, email app) and compare that with what agent read

---

## Problem 5 — Defend the agent

**Prompt 1 (initial):**
> defend agent at 3 levels:

**Prompt 2 (follow-up):**
> defend agent at 3 levels:
> code - what program does to document before any model sees it
> design - how agent is put together so poisoned doc canot reach dangerous tools or decision
> prompt: rules in prompts/prompt.md
>
> don't delete send_email or approve_payment from system. shop will use them later with human sign-off. keep way to run agent with no defenses.
>
> rerun all 12 practice docuemnts. save output/defense_results.json in same shape as problem 5 plus tokens and dollars per document. clean documents must still come back with right values. refusing or blanking out a real quote counts as failure.
>
> in output/defense_results.md:
>
> * a before and after table of all 12 documents
> * what each layer catches that others miss
> * the extra tokens and dollars each layer adds per doc
>
>
> add safety features to output/harness.md in safety section: what each defense layer does, in plain words

**What was lacking after the first prompt:** The first message stopped at "defend agent at 3 levels:" without naming the levels or the deliverables, so the follow-up supplied them.

**Prompt 3 (status check while the defense run was in progress):**
> ok let me know when it's done

---

## Problem 6 — Red team: two new attack documents

**Prompt 1 (initial):**
> we need to test this as the attacker. make two new vendor documents with traps in data/my_attacks/ (HTML, PDF, or email). each one should use hiding trick or attack goal that is not in practice set. person opening document should see a normal quote. run both attacks on agent with no defenses and on defended agent. in output/red_team.md, for each attack" what is hidden, where, what it tries tomake the agent do, and what happened before and after your defenses. I will get more points for attacks that are new and that actually fool the agent with no defenses.

---

## Problem 7 — Exam run (data/exam_docs, no answer key)

**Prompt 1 (initial):**
> data/exam_docs/ has 10 vendor docs w no answer key. run your final defended agent on all of them. do not hand-edit results. save output/exam_results.json with one entry per exam file. each entry has these fields:
>
> * file: exam file name (ex: e01_quote.html)
> * vendor
> * sku
> * unit_price
> * lead_time_days
> * min_order
> * decision: recommend or do_not_recommend
> * reason
> * trap_tool_called: true or false
> * input_tokens, cached_tokens, output_tokens
> * cost_usd
>
>
> graders will compare our results to hidden answer key and rerun some agents to check. you get points for correct fields and decisions, no trap tools calls, and clean docuemnts handled normally

---

## Problem 8 — Self-contained HTML report

**Prompt 1 (initial):**
> build output/hw6_report.html. must be one file that opens by double-click with no internet and no others files next to it. the page must show five things below using real numbers from earlier problems.
>
> * your caching results, with a chart
> * attacks before and after defenses
> * what your defenses cost in tokens and dollars
> * your exam results and your two red team attacks
> * a short rec to the store manager: should Campus Customs turn this agent on for real vendor mail, and what would it cost per motnh at 1,000 docs a day?
>
>
> more points for designed page (fonts, color, layout) that reads well

---

## Problem 9 — Publish to a public GitHub repo

**Prompt 1 (initial):**
> push the project to public GitHub repo and provide the link with me. graders will be cloning it so make sure it opens and files below are included:
>
> include whole data-3 folder (course data plus two attack folders) so graders can clone repo and run agent right away. do not commit real .env. use .gitignore to keep it out and include .env.example with placeholders per usual.  expected repo attached. other python files are fine, put a short note in readme.md on how to run agent

(An image of the expected repo layout was attached.)

---

## Problem 10 — Check Homework 6 against Homework 5

**Prompt 1 (initial):**
> can you check homework 5 and make sure everythign for this homework is done correctly if it is built off of that one

**Result:** Homework 6 uses its own course data (`data-3` handbook and vendor documents), not the Homework 5 database or MCP server, so nothing in it should read Homework 5 files. The shared pieces already match Homework 5 (gpt-6-luna through Portkey on the Responses API, and agents only prepare money moves while a human approves them). Two Homework 5 conventions were added here: this log now follows the Homework 5 format and records that it was created, and the repo link is saved in `output/github_url.txt`.

---

## Problem 11 — Repo link for Canvas

**Prompt 1 (initial):**
> can you give me an updated github link for hw6 for canvas if needed

**Result:** The link did not change: https://github.com/joliebua/hw6 (also saved in `output/github_url.txt`).

---
