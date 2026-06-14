# 🎁 Gift-Card Concierge

A tiny, reproducible **agentic-commerce demo** for the Bitrefill hackathon. You type a plain-language
request — *"send my mom a $50 gift card"* — and an AI agent searches Bitrefill, buys the item, waits for
delivery, and hands back the redemption code. No checkout, no clicking around.

This build uses **Claude Code as the agent** (no paid LLM key required) driving the **Bitrefill
eCommerce MCP**. It's a valid hackathon submission in the **Shop on command** direction, and it
doubles as a getting-started guide for builders.

---

## What it does

```
"send my mom a $50 gift card"
        │
        ▼
  search-products ──► get-product-details ──► buy-products ──► poll get-invoice-by-id ──► 🔑 code
        │                                                          (unpaid → … → complete, ~5s)
        └── all driven autonomously by the AI agent ──────────────────────────────────────┘
```

Everything runs against the test product **`test-gift-card-code`**, which delivers a redemption PIN with
**no real payment**. You can demo the full flow safely. (A real run is captured in [`DEMO-RUN.md`](./DEMO-RUN.md).)

> **Heads up — the brief is slightly off.** It names `delos-syldavia`, but that slug doesn't resolve on a
> standard key, and `get-product-details` is currently broken for test products. This repo uses the path
> that actually works; every discrepancy is logged in [`FEEDBACK.md`](./FEEDBACK.md).

---

## Step 1 — Pick your AI agent (all free)

The hackathon gives you Bitrefill's surfaces, but you still need an **AI agent** to drive them. Here are
free options — pick one:

| Option | Why pick it | Get started |
| --- | --- | --- |
| **Claude Code** *(used here)* | Anthropic's CLI; first-class MCP support via `claude mcp add`. Also Claude Desktop / Cowork plugin. | https://claude.com/claude-code |
| **Google Gemini (AI Studio)** | Free API key, **no credit card**, generous free tier, supports tool-calling. Great with the Vercel AI SDK (`@ai-sdk/google`). | https://aistudio.google.com/apikey |
| **OpenRouter** | One free account → many models, several `:free` ones support tool-calling. | https://openrouter.ai/ |
| **Vercel AI Gateway** | Unified routing + free monthly credits; on Vercel deploys, OIDC means no key in code. | https://vercel.com/docs/ai-gateway |
| **Ollama** | Fully **local & offline, $0**, no account. Tool-calling varies by model (try `llama3.1`, `qwen2.5`). | https://ollama.com/ |
| **Cursor / ChatGPT Atlas** | Bitrefill's capability-aware skill supports these via a residential-IP browser channel. | https://github.com/bitrefill/agents |

> This repo is wired for **Claude Code**. To build a web app instead, the same MCP works with the Vercel
> AI SDK's `createMCPClient` and any of the model providers above.

---

## Step 2 — Get a free Bitrefill API key

1. Go to **https://www.bitrefill.com/account/developers**
2. Create a developer API key (free — this is *not* the thing that costs money).
3. Copy it.

```bash
cp .env.example .env
# then paste your key into .env as BITREFILL_API_KEY=...
```

---

## Step 3 — Connect the Bitrefill MCP

This repo ships a project-scoped `.mcp.json` that reads `${BITREFILL_API_KEY}` from your environment, so
the simplest path is just to open Claude Code in this folder and approve the server.

If you prefer the CLI (adds it explicitly):

```bash
# loads the key from .env into your shell first
export $(grep -v '^#' .env | xargs)

claude mcp add --transport http bitrefill "https://api.bitrefill.com/mcp/$BITREFILL_API_KEY"
```

> **Why the key-in-URL form?** The hosted MCP defaults to OAuth (browser sign-in). Putting the key in the
> URL path (`/mcp/<KEY>`) gives you painless, scriptable, no-popup access — ideal for agents.

Verify it connected:

```bash
claude mcp list
```

You should see `bitrefill` with 7 tools (`search-products`, `get-product-details`, `buy-products`,
`submit-prepayment-step`, `list-invoices`, `get-invoice-by-id`, `update-order`).

---

## Step 4 — Run it

In Claude Code, from this folder:

```
/shop send my mom a $50 gift card
```

The agent will search, buy the test product, poll until it's delivered, and return the redemption code —
narrating each step. `CLAUDE.md` holds the agent's instructions (test-mode only, never real money).

---

## Safety / test mode

- By default buys **`test-gift-card-code`** with a **crypto** method and **never pays the link** — a test
  product that delivers a redemption PIN without real settlement.
- Never uses `cashback`, and only uses `balance` for the **test-credit** path (see below) — never against
  a real-money account.

## Testing your own integration

Building your own app on the Bitrefill MCP? **[`TESTING.md`](./TESTING.md)** is a generic,
framework-agnostic guide to exercising the full purchase flow without spending real money — covering both
the **crypto (never-paid)** path and the **test-credit (`balance`)** path.

> **Test credits are granted manually — contact a member of the Bitrefill team to have them added** to
> your account. Without them, use the crypto path, which needs no extra setup.

---

## Project layout

```
.mcp.json                # Bitrefill MCP server config (reads ${BITREFILL_API_KEY})
CLAUDE.md                # agent instructions: the shop-on-command flow + safety rules
.claude/commands/shop.md # the /shop slash command
scripts/mcp.py           # tiny Streamable-HTTP MCP client (used to dogfood the flow without a session restart)
DEMO-RUN.md              # captured proof of a successful end-to-end run
TESTING.md               # framework-agnostic guide to testing any Bitrefill MCP integration
.env.example             # copy to .env, add your free key
README.md                # this guide
FEEDBACK.md              # running log of friction/issues found while building
```

---

## Submission checklist (per the hackathon brief)

- [x] Uses a Bitrefill surface — **eCommerce MCP** (+ Agent Skills).
- [x] Shows it **working** — real end-to-end run captured in [`DEMO-RUN.md`](./DEMO-RUN.md) (delivered PIN, no payment). Record the `/shop` run for the video.
- [x] Feedback captured — see [`FEEDBACK.md`](./FEEDBACK.md).
- [x] Solo build.
