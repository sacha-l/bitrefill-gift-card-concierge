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
no payment), but **only by ignoring the documented happy path**. The standard
`search → get-product-details → buy` sequence breaks (search hides test/`KN` products; details loops on
the `test-gift-card-*` family). *Correction 2026-06-12: the brief's headline slug `delos-syldavia` is
NOT broken — it resolves fine via `get-product-details`/`buy`; it's only invisible to `search`. The
original "non-existent slug" finding below is retracted.* Details below.

### 🔴 Blockers

- ~~🔴 **The brief's headline test product `delos-syldavia` does not exist on a normal key.**~~
  **❌ RETRACTED 2026-06-12 — this was wrong; the slug DOES resolve.** See the 2026-06-12 correction
  below ("`delos-syldavia` DOES resolve after all"): `get-product-details("delos-syldavia",
  currency:USD)` and `buy-products` both work on this same key. The original probe (query `delos`,
  `syldavia`, `delos-syldavia` via `search-products`, and `get-product-details`) returned
  nothing/`RESOURCE_NOT_FOUND`, but that was either a since-fixed provisioning gap or the same
  `get-product-details` bug under a different code path. **The slug is only invisible to
  `search-products`** (known-slug-only) — it is fully usable once you pass the exact slug. *Net: the
  brief's headline slug works; the real fix is to index it in search, not to replace it.*

- 🔴 **`get-product-details` loops on the `test-gift-card-*` family.** ~~broken for ALL test products~~
  *(narrowed 2026-06-12 — see correction below: `delos-syldavia` resolves cleanly, so it's NOT all test
  products; the loop is specific to the `test-gift-card-*` family).* For an affected slug
  (`test-gift-card-code`, …) it returns *"Product '<slug>' was not found. Did you mean one of these?"* and
  then **suggests the exact same slug you just passed**, with a valid `product_url`. An agent following the
  documented flow gets stuck in an infinite `did-you-mean(X) → call(X) → not-found, did-you-mean(X)` loop.
  It works fine for real products (`amazon_com-usa`) and for `delos-syldavia`. `include_test_products:true`
  does not help. *This will hang live demos.* *Fix: make `get-product-details` resolve the `test-gift-card-*`
  slugs (the catalog clearly knows them — it suggests them).*

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
    `include_test_products:true` (all country `KN`). So "syldavia" is real. ~~but as an *eSIM* suffix, not a
    gift card called `delos-syldavia`.~~ *Correction 2026-06-12: `delos-syldavia` IS a real gift card
    (resolves via `get-product-details`/`buy`) — it just never appears in `search`. So "syldavia" spans
    both a gift card and the eSIM suffixes.*
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
on (1) the headline test product being **undiscoverable via `search-products`** (it resolves only if you
already know the exact slug — see the 2026-06-12 correction; not "non-existent" as originally written) and
(2) a `get-product-details` loop on the `test-gift-card-*` family. Fixing those two things is the
highest-leverage pre-hackathon change.

---

## Official Agent Skill — `npx skills add bitrefill/agents` (second dogfooding pass)

- 🟢 **One-line install just works.** Installed to `.agents/skills/bitrefill` and symlinked for Claude Code,
  Cursor, Copilot. Ships 9 reference docs (mcp/cli/api/browse/safeguards/troubleshooting/capability-matrix/
  openclaw/headless-auth). **This is dramatically more accurate and complete than the hackathon brief** — it
  correctly documents the Cloudflare-403-on-datacenter-IP issue, per-host MCP gotchas (Cursor 40-tool cap,
  ChatGPT Developer Mode, Claude free tier can't add MCP), OAuth-loop fixes, and output-truncation caps.
  *Suggestion: point hackathon participants at this skill as the primary onboarding, not the brief's prose.*

- 🟡 **`delos-syldavia` appears nowhere in the official skill either.** ~~Strong confirmation the brief's
  test-product slug is simply wrong/outdated.~~ *Update 2026-06-12: the slug is NOT wrong — it resolves via
  `get-product-details`/`buy` (correction below); it's just undocumented in the skill AND invisible to
  `search`.* The skill (`references/api.md`) lists `test-gift-card-code` as the example and links the docs'
  Test Products page. *Fix: add `delos-syldavia` to the skill's test-product list so it's discoverable from
  docs even though search won't surface it.*

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

## 2026-06-11 — OAuth in-session flow drops the whole MCP server

- 🔴 **Completing the hosted-MCP OAuth flow mid-session disconnected the entire Bitrefill server.**
  Ran the agent against the **OAuth** transport (not the key-in-URL form). `authenticate` returned the
  authorize URL fine; the user approved and pasted back the `localhost:3118/callback?code=…` URL. But by
  that point the MCP server had **disconnected**, taking *all* `mcp__bitrefill__*` tools with it —
  including `complete_authentication`, so there was no way to submit the callback code. Net result: the
  authorization succeeded in the browser but the agent could not finish the handshake, and no purchase
  tool (`buy-products`, `get-invoice-by-id`) was reachable. The run stalled at auth with nothing to retry.
  *Likely interaction with the known "MCP added mid-session isn't usable until restart" gotcha — the
  OAuth callback round-trip appears to require the server to re-handshake, which a live agent session
  can't drive.* *Fix: (a) keep `complete_authentication` available even after the server drops, or hold the
  connection open across the callback; (b) for hackathon/agent use, lead with the **key-in-URL** form
  (`api.bitrefill.com/mcp/<KEY>`) which sidesteps the browser OAuth round-trip entirely — see the earlier
  note that this is the agent-friendly path. The OAuth path is a poor fit for headless/agent drivers.*

## 2026-06-11 (run 2) — OAuth completed in-session this time, but the paste-back is awkward UX

- 🟢 **OAuth round-trip worked end-to-end this run** — contrast with the note directly above where the
  same flow *dropped the entire server*. `authenticate` returned the authorize URL; the user approved and
  pasted back the `localhost:60403/callback?code=…` URL; the `mcp__bitrefill__*` purchase tools
  (`buy-products`, `get-invoice-by-id`, …) then loaded **automatically** and the run completed (delivered
  `test-gift-card-code` $50, PIN `0668399175871606`, invoice `complete`/`all_delivered`). So the earlier
  "OAuth drops the whole server" failure is **intermittent, not deterministic** — which is arguably *worse*
  for a live demo, because you can't predict which behaviour you'll get.

- 🟡 **Notable: `complete_authentication` was never called.** The loopback listener on
  `localhost:60403/callback` appears to have captured the `code` on its own — tools appeared the instant the
  browser hit the redirect, before any paste was processed. So the "copy the callback URL and paste it back
  to the agent" step may be **redundant whenever the loopback succeeds**; it's really a *fallback* for when
  the redirect page errors, but the prompt presents it as a required step. *Fix: word the instruction as
  "only paste the URL back if the redirect page shows a connection error."*

- 🟡 **Human-in-the-loop auth is at odds with "shop on command" (builder's observation — fair).** An
  autonomous agent ideally runs with zero human taps; the OAuth path needs a human to (1) open a browser,
  (2) approve consent, and (3) sometimes paste a URL back. Two pieces of nuance, though:
  - It's a **one-time, setup-time** cost, not per-purchase — once authed, subsequent buys in the session
    need no interaction. So the demo isn't "basic" so much as front-loaded with a one-time handshake.
  - The consent screen is a *feature* for **real-money** spend — you genuinely want a human to authorize an
    agent that can charge a card. So the right framing is: **OAuth for interactive/human-present demos;
    key-in-URL (`api.bitrefill.com/mcp/<KEY>`) for headless/cron/server agents** that must run untouched.
    This reinforces the earlier "lead with key-in-URL for agent builders" note — it's the zero-touch path.
  *Fix: offer both transports side-by-side in onboarding with a one-line "which should I pick?" decision
  rule (human present → OAuth; autonomous → key-in-URL).*

## 2026-06-12 — `delos-syldavia` DOES resolve after all (correction to the 🔴 blocker above)

Prompted by the builder sharing the live URL `bitrefill.com/kn/en/gift-cards/delos-syldavia/`, re-tested
the slug against the **same** hosted MCP key/session used above.

- 🟢 **`get-product-details("delos-syldavia", currency:USD)` returns full, valid data.** Name
  *"Delos-Test Vouchers X0!"*, `country_code: KN`, category `gifts`, `recipient_type: none`, `in_stock: true`,
  16 payment methods (incl. `balance`/`cashback`), and **9 packages**: `0.01, 10, 20, 50, 100, 200, 500,
  1000`, plus a weird `"Value 244"`. Prices carry a markup (face `10` → `payment_price 11.58`). **This
  directly contradicts the earlier 🔴 "`delos-syldavia` does not exist on a normal key."** Either it was
  provisioned since, or the earlier probe hit the same details bug under a different code path. *Action:
  downgrade that blocker — the brief's headline slug works for `get-product-details` and `buy-products`.*
- 🟡 **…but it's still invisible to `search-products`.** `search-products(query:"delos", country:KN,
  in_stock:false)` → `found: 0`. So the product is only reachable **if you already know the exact slug** —
  a search-first agent (the documented flow) never discovers it. *Fix: index test/`KN` products in search,
  or document "known-slug-only" products.*
- 🟢 **No "did you mean" loop here.** Unlike `test-gift-card-code`, `get-product-details` resolved
  `delos-syldavia` cleanly on the first call. So the infinite-loop bug is specific to the
  `test-gift-card-*` family, not all test products — worth narrowing in the blocker write-up above.
- 🔴 **Can't test "account/test credits" on this session — every balance reads 0.** `account_balances` for
  both `amazon_com-usa` and `delos-syldavia` show `balance` (XBT/EUR/USD) and `cashback` all `0`. The
  builder says the credits live on **`sacha@joinwebzero.com`**, but this MCP session's OAuth login is a
  *different* account (or the credits aren't surfaced as `balance`/`cashback`). *Open question / likely
  doc gap: how do Bitrefill "test credits" appear to the API — a normal balance sub-account, or a separate
  mechanism? If the former, you must be OAuth'd into the account that holds them; the MCP has no `whoami`
  tool to confirm which account you're on.*

## 2026-06-12 — No way to switch accounts mid-session (OAuth transport)

Trying to move the session from the first-authed account to `sacha@joinwebzero.com` (which holds the
test credits) exposed a dead-end for agent drivers:

- 🟡 **No `logout` / `switch-account` / `whoami` tool.** Once authenticated, the MCP **stops exposing**
  `authenticate` and `complete_authentication` (confirmed: ToolSearch returns no match for them), and there
  is no tool to drop the token or even read *which* account you're on. So an agent that authed into the
  wrong account cannot recover in-session — it can't tell it's wrong (every balance just reads 0, which is
  ambiguous between "wrong account" and "empty account") and can't re-auth. *Fix: expose a `whoami`
  (returns account email/id) and a `logout`/`reauthenticate` tool, or keep `authenticate` available so a
  second call can force account selection.*
- 🟡 **OAuth silently reuses the browser's Bitrefill session.** Re-running the authorize URL just
  re-confirms whoever is logged into bitrefill.com in the browser — there's no account-picker on the
  consent screen. To switch accounts you must (a) log out of bitrefill.com in the browser and log in as the
  target account, then (b) clear the MCP's stored OAuth token client-side (`/mcp` → bitrefill → clear/
  reconnect in Claude Code) to re-trigger the flow. Neither step is discoverable from the agent side.
  *Fix: document the account-switch procedure, and ideally force `prompt=select_account` on the authorize
  URL so the consent screen lets the user choose.*
- 💡 **Reinforces "lead with key-in-URL for agents."** The key-in-URL transport (`api.bitrefill.com/mcp/
  <KEY>`) ties the session to a specific account deterministically — no browser-session ambiguity, no
  switch dance. For multi-account or headless testing this is strictly better than OAuth.
- ✅ **RESOLVED 2026-06-14 (see section below).** Test credits **do** surface as a normal `balance`
  sub-account — they appeared as **€20 in the EUR sub-account** on `delos-syldavia`'s `account_balances`,
  and a `payment_method:"balance"` + `balance_currency:"EUR"` buy delivered a PIN and debited the credit
  (€20 → €19.98). No separate mechanism. The earlier all-zero reads were just the wrong OAuth account.

## 2026-06-14 — credit path PROVEN, but the documented poll loop hangs on balance buys

First run paid from **account balance / test credits** (every prior run was crypto-never-paid). The MCP
session is now OAuth'd into the account holding the credits.

- ✅ **Test credits = a normal `balance` sub-account.** `get-product-details("delos-syldavia")`
  `account_balances` showed four sub-accounts: **EUR 20** (funded), XBT 0 (primary), USD 0, cashback 0.
  So credits are not a separate API concept — they're an ordinary `balance` sub-account, and you must be
  OAuth'd into the account that holds them (no `whoami` to confirm which account — still a gap).
- ✅ **Credit-path buy works.** `buy-products(delos-syldavia, "0.01", payment_method:"balance",
  balance_currency:"EUR")` → `payment_info:{method:"balance", status:"payment_initiated"}` → delivered.
  PIN `0860810352585415167`, invoice `46fc9d9c-d361-491d-b06d-496e33e64772`, order
  `6a2e7dcbda3d223eb840d8dc`. **`balance_currency` is required** — omit it and it defaults to the primary
  XBT sub-account (balance 0) and the buy would fail; you must name the funded sub-account explicitly.
- ✅ **Real settlement confirmed.** EUR balance dropped **20 → 19.98** between before/after
  `get-product-details`. Unlike the crypto test runs (which "complete" with no money moved), a balance buy
  genuinely debits the credit.
- 🔴 **The documented poll-until-`complete` loop HANGS on balance buys.** Across two polls the top-level
  `invoice_status` stayed `payment_confirmed` and `orders_delivery_status` stayed `not_delivered` — they
  never advanced to `complete`/`all_delivered`, **even though `orders[0].status` was `delivered` with a PIN
  the entire time.** An agent following `CLAUDE.md`'s "poll until `invoice_status:complete` /
  `all_delivered`" rule loops forever. *Fix (driver side): treat `orders[0].status === "delivered"` +
  `redemption_available:true` as the completion signal, not the top-level rollup. Fix (server side): make
  the invoice rollup reflect delivered orders for balance payments.* NB: the earlier crypto runs DID reach
  top-level `complete`/`all_delivered`, so this rollup desync looks **specific to `payment_method:balance`.**
- 🟡 **Reported price ≠ actual debit.** The `0.01` USD package showed `detected_payment_info.price:"0.01"
  EUR`, but the EUR balance fell by **0.02** (20 → 19.98). Sub-cent, but the invoice's stated price and the
  real charge disagree — verify the actual debit from the balance delta, not the `price` field.
- 🟢 **Richer redemption payload on `delos-syldavia` than the test-gift-card.** Besides `pin`, the order
  returned `barcodeFormat:"CODE128"`, an `access_link`, and an iTunes-style `redemptionLink`.

## 2026-06-12 — clean `/shop` run reconfirms instant-deliver + phantom "payment confirmed"

Third end-to-end `test-gift-card-code` $50 purchase over the hosted MCP (`usdc_base`,
`return_payment_link:true`). Went straight to `buy-products` (skipped the known-broken
`get-product-details` for the test slug) → single `get-invoice-by-id` poll came back
`complete`/`all_delivered`. PIN `1643265852450786`, invoice `b7bbbb07-555c-48b0-9c49-b948d0282cd6`,
order `6a2b32f44efdda1fc75918f3`.

- 🟢 **Two-call flow is rock-solid** when you know to skip `get-product-details` — `buy → poll` is all
  it takes, and the `agent_instructions` string on the buy response again spelled out next steps + the
  `invoice_id ≠ order_id` gotcha. Best surface of the set, confirmed a third time.
- 🟡 **Phantom payment confirmation, reconfirmed.** `created 22:13:08.495 → delivered 22:13:09.364`
  (~0.9s), and the invoice reported `payment_confirmed_time 22:13:09.047` + `detected_payment_info.status:
  complete` with **`incoming_tx_ids` empty** — i.e. it claims payment was confirmed when nothing was ever
  sent. Harmless for the test product (no money moved, intended), but for any agent that *gates logic on
  `payment_confirmed`* this is a landmine: you can't distinguish "test product auto-confirms" from "a real
  payment landed." *Fix: for test products, either suppress `payment_confirmed_time`/`detected_payment_info`
  or flag the invoice as `is_test: true` so drivers don't treat the confirmation as real settlement.*
- 🟡 **Still no observable pending window.** Same as the earlier run — sub-second delivery means there's no
  pending state to demo/film, contradicting the brief's "~5s to see the pending state."

## Highest-leverage fixes before the event (ranked)

1. **Index `delos-syldavia` (and other `KN`/test slugs) in `search-products`.** The slug *does* resolve via
   `get-product-details`/`buy-products` (correction logged 2026-06-12) — it's just invisible to search, so a
   search-first agent never discovers it. Either index it, or document the known-slug-only set
   (`delos-syldavia`; `test-gift-card-code` 10/20/30/50/100; `test-esim-data-syldavia` for eSIM) plus the
   required `include_test_products:true` + a working payment method.
2. **Fix `get-product-details` for test slugs** (the infinite "did you mean <same slug>" loop) — it will hang
   live agent demos.
3. **Point participants at `npx skills add bitrefill/agents`** as the canonical onboarding; it's better than
   the brief. Then reconcile the brief with it.
4. **Add the "pick your AI agent" guidance** (free options + links) the brief currently lacks.
5. **Document the agent-friendly setup tips**: key-in-URL form to skip OAuth, `User-Agent` required to avoid
   the `/mcp` 403, and "restart Claude Code after `claude mcp add`."
