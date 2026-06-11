# Builder feedback — Bitrefill agentic-commerce hackathon dry run

Running log of friction, bugs, and "huh?" moments found while building a real submission, so the brief,
docs, and onboarding can be tightened before the event. Newest issues at the bottom.

Legend: 🔴 blocker · 🟡 confusing/rough · 🟢 worked well · 💡 suggestion

---

## Found before writing any code (from the brief + docs alone)

- 🔴 **No guidance on which AI agent to use.** The brief lists Bitrefill's *surfaces* (MCP, CLI, Skills,
  x402, REST) but never states that a builder also needs an **AI model/agent** to drive them, nor which
  free ones exist. For a newcomer this is the very first blocker. *Fix: add a "pick your AI agent" section
  with free options + links (Claude Code, Google AI Studio/Gemini, OpenRouter, Vercel AI Gateway, Ollama).
  Drafted in this repo's README.*

- 🟡 **Contradictory test-product story.** The brief says: use **`delos-syldavia`**, pay with crypto/x402,
  and *avoid store credit because it debits*. But the docs' **Test Products** page describes a **different**
  set — `test-gift-card-code`, `test-gift-card-link`, `test-phone-refill` (+ `-fail` variants) — that are
  **balance-only, cost nothing, and hidden behind `include_test_products=true`**. Two unrelated test
  mechanisms with opposite payment rules and no cross-link. A builder won't know which applies to the MCP.
  *Fix: one table — "test product → which surface → which payment method" — and link it from the brief.*

- 🟡 **No self-host guidance for the MCP.** The brief offers `bitrefill-mcp-server` as a self-host option,
  but the eCommerce-MCP doc only documents the hosted URL. *Fix: add a self-host quickstart or drop the
  option from the brief.*

- 🟡 **OAuth vs key-in-URL isn't explained.** The hosted MCP defaults to OAuth (browser sign-in), but the
  scriptable/agent-friendly path is the key-in-URL form `api.bitrefill.com/mcp/<KEY>`. This is the single
  most useful onboarding tip for agent builders and it's buried. *Fix: lead with it for the hackathon.*

- 💡 **"Free key" vs "costs money" ambiguity.** It wasn't obvious that the **Bitrefill developer key is
  free** and that the only thing that can cost money is a hosted **LLM**. New builders may assume they need
  to pay Bitrefill. *Fix: one sentence — "the Bitrefill key is free; you only pay (optionally) for your AI
  model, and there are free ones."*

---

## Found while building / running — 2026-06-11 live run against the hosted MCP

**TL;DR:** the shop-on-command flow *does* work end-to-end (we delivered a real test gift-card code with
no payment), but **only by ignoring the documented happy path**. The brief's headline test product and
the standard `search → get-product-details → buy` sequence both break. Details below.

### 🔴 Blockers

- 🔴 **The brief's headline test product `delos-syldavia` does not exist on a normal key.** Both
  `search-products` (query `delos`, `syldavia`, `delos-syldavia`, with and without
  `include_test_products`) and `get-product-details` return nothing/`RESOURCE_NOT_FOUND`. The actual test
  products that exist are differently named (see below). *Fix: correct the brief — give the exact, current
  slug(s), or grant the key whatever flag `delos-syldavia` lives behind.*

- 🔴 **`get-product-details` is broken for ALL test products.** For any test slug
  (`test-gift-card-code`, `test-esim-data-syldavia`, …) it returns
  *"Product '<slug>' was not found. Did you mean one of these?"* and then **suggests the exact same slug
  you just passed**, with a valid `product_url`. An agent following the documented flow gets stuck in an
  infinite `did-you-mean(X) → call(X) → not-found, did-you-mean(X)` loop. It works fine for real products
  (`amazon_com-usa` returned full details). `include_test_products:true` does not help. *This will hang
  live demos.* *Fix: make `get-product-details` resolve test slugs (the catalog clearly knows them — it
  suggests them).*

- 🟡 **No way to discover a test product's valid denominations.** Because `get-product-details` fails, the
  only way we found the package values was to call `buy-products` with a wrong `package_id` and read the
  error: *"Available denominations: 10, 20, 30, 50, 100."* That's a hacky workaround for what should be a
  details lookup.

### 🟡 Confusing / undocumented

- 🟡 **Two unrelated test-product families, neither matching the brief.**
  - `test-gift-card-code` / `-link` / `test-phone-refill` (+ `-fail`): only surface as *suggestions* from
    the broken details call; **do not** appear in `search-products` even with `include_test_products:true`.
  - `test-esim-product`, `test-esim-data-syldavia`, `test-esim-duration-syldavia`,
    `test-esim-subscription-pro-syldavia`: these **do** appear in `search-products` with
    `include_test_products:true` (all country `KN`). So "syldavia" is real — but as an *eSIM* suffix, not a
    gift card called `delos-syldavia`.
  *Fix: one canonical, documented list of MCP test slugs + which appear in search vs details.*

- 🟡 **`include_test_products` is required but unmentioned for the MCP.** Test products are hidden from
  `search-products` unless you pass `include_test_products:true`. The brief/MCP docs never say this.

- 🟡 **Brief's payment guidance contradicts what actually works.** The brief says test products take "~5s
  to deliver to give you time to see the pending state" and to pay with crypto (not balance). In practice
  `test-gift-card-code` with `payment_method:usdc_base` delivered **instantly** (`created` 21:25:57.582 →
  `delivered` 21:25:58.085, ~0.5s) and **completed with no payment sent** (`incoming_tx_ids` empty,
  `status: complete`). Good news (no money moved), but **there was no observable pending window** to film.
  Meanwhile the *docs'* Test Products page says these are **balance-only** — yet a crypto method worked and
  cost nothing. The three sources (brief, docs, reality) disagree.

### 🟢 Worked well

- 🟢 **Connection + auth:** `claude mcp add --transport http … /mcp/<KEY>` → `✔ Connected` first try.
  Stateless server (no `Mcp-Session-Id` needed), clean JSON-RPC over SSE.
- 🟢 **Real product flow is solid:** `search-products` and `get-product-details` for `amazon_com-usa`
  returned rich, well-structured data (packages, 16 payment methods, balances, reviews, instructions).
- 🟢 **`buy-products` is excellent for agents:** returned `invoice_id`, `payment_link`,
  **`x402_payment_url`**, raw `payment_info` (USDC-on-Base address + EIP-681 `paymentUri`), and an
  `agent_instructions` string spelling out next steps and the `invoice_id ≠ order_id` gotcha. This is the
  best-designed surface of the set.
- 🟢 **End-to-end success:** `buy-products(test-gift-card-code, 50, usdc_base)` →
  `get-invoice-by-id` → `complete`/`all_delivered` → redemption `pin` returned. No real money, no store
  credit used (account balances were all 0 anyway).

### 🔧 Friction for custom-app (non-Claude-Code) builders

- 🟡 **Cloudflare 403s the default `python-urllib` User-Agent.** Same request via `curl` (200) and with a
  custom `User-Agent` header (200) worked. A builder using a stock HTTP client may hit a confusing 403.
  *Fix: document that a `User-Agent` is required, or relax the WAF for `/mcp`.*
- 🟡 **`.mcp.json` env-var expansion needs the var in the launching shell, not `.env`.** Claude Code does
  not auto-load `.env`; committing `.mcp.json` with `${BITREFILL_API_KEY}` shows a literal-unexpanded
  endpoint and a "conflicting scopes" warning unless you `export` the key before launching. *Fix: note this
  in onboarding, or have the MCP docs show the `claude mcp add` one-liner instead.*
- 🟡 **MCP added mid-session isn't usable until restart.** After `claude mcp add`, the tools don't load into
  the running Claude Code session — you must restart. Worth telling participants so they don't think it's
  broken.

### ✅ Net assessment

A motivated builder *can* ship a working agentic-commerce demo on this stack in an afternoon — `buy-products`
+ `x402` are genuinely good. But a first-timer following the brief verbatim will **stall within 10 minutes**
on (1) a non-existent test product and (2) a `get-product-details` loop. Fixing those two things is the
highest-leverage pre-hackathon change.

---

## Official Agent Skill — `npx skills add bitrefill/agents` (second dogfooding pass)

- 🟢 **One-line install just works.** Installed to `.agents/skills/bitrefill` and symlinked for Claude Code,
  Cursor, Copilot. Ships 9 reference docs (mcp/cli/api/browse/safeguards/troubleshooting/capability-matrix/
  openclaw/headless-auth). **This is dramatically more accurate and complete than the hackathon brief** — it
  correctly documents the Cloudflare-403-on-datacenter-IP issue, per-host MCP gotchas (Cursor 40-tool cap,
  ChatGPT Developer Mode, Claude free tier can't add MCP), OAuth-loop fixes, and output-truncation caps.
  *Suggestion: point hackathon participants at this skill as the primary onboarding, not the brief's prose.*

- 🟡 **`delos-syldavia` appears nowhere in the official skill either.** Strong confirmation the brief's
  test-product slug is simply wrong/outdated. The skill (`references/api.md`) lists `test-gift-card-code`
  as the example and links the docs' Test Products page.

- 🟡 **Skill's MCP reference drifts from the live MCP.** `references/mcp.md` calls the detail tool
  `product-details` (the live tool is **`get-product-details`**) and says `package_id` has the form
  `{product_id}<&>{value}`, while the live `buy-products` schema says to pass **only the value** (e.g. `"50"`)
  — and that `<&>` form is what `get-product-details` returns for *real* products. Minor, but an agent
  copying the doc verbatim could mis-call. *Fix: regenerate the skill's MCP doc from the live tool schemas.*

- 🟡 **"Test products are Business/Affiliate only" — but our key bought one.** `references/api.md` says test
  products are Business/Affiliate-tier only; the docs' Test Products page implies balance-only on Personal.
  Yet this key purchased `test-gift-card-code` over the **MCP** with a **crypto** method and it delivered
  free. So the actual gating rules for test products are unclear and stated three different ways across
  brief / docs / skill. *Fix: state one clear rule: "which tiers/surfaces can use which test products, with
  which payment methods."*

---

## Highest-leverage fixes before the event (ranked)

1. **Fix or replace the test-product instruction in the brief** — `delos-syldavia` doesn't resolve; give the
   real slug(s) (`test-gift-card-code` 10/20/30/50/100; `test-esim-data-syldavia` for eSIM) and the required
   `include_test_products:true` + a working payment method.
2. **Fix `get-product-details` for test slugs** (the infinite "did you mean <same slug>" loop) — it will hang
   live agent demos.
3. **Point participants at `npx skills add bitrefill/agents`** as the canonical onboarding; it's better than
   the brief. Then reconcile the brief with it.
4. **Add the "pick your AI agent" guidance** (free options + links) the brief currently lacks.
5. **Document the agent-friendly setup tips**: key-in-URL form to skip OAuth, `User-Agent` required to avoid
   the `/mcp` 403, and "restart Claude Code after `claude mcp add`."
