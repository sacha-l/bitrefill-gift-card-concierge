# Testing Your Bitrefill Integration

**For:** anyone building on the **Bitrefill eCommerce MCP**, in any agent framework — Claude, Cursor, a
custom LangChain / LlamaIndex / Vercel AI SDK agent, or a plain MCP client. It doesn't matter what drives
the tools; the calls below are the MCP's own interface, so they're identical everywhere.

**Goal:** exercise the *full* purchase flow — search → buy → deliver → redeem — **end-to-end, without
spending real money** — so you can build and demo your app with confidence. The four-call shape you learn
here (read balance → buy → poll order → re-read balance) is exactly how a real account-balance checkout
behaves in production. Build against it with test credits, ship it with real ones.

> ### 🔑 Getting test credits
> The **`balance` (test-credit) path** in Section 3 requires test credits to be provisioned on your
> account. **These are granted manually — contact a member of the Bitrefill team to have them added.**
> Until then, use the **crypto path** in Section 2, which works on any key with no extra setup.

---

## 0. Connect to the MCP

The hosted endpoint is the same for every framework:

```
https://api.bitrefill.com/mcp/<YOUR_KEY>
```

- The **developer key is free** — sign up at <https://www.bitrefill.com/account/developers>. The only
  thing that can ever cost money is your own LLM.
- **Two transports.** **Key-in-URL** (above) ties the session to one account deterministically — best for
  agents, scripts, headless, and CI. **OAuth** (browser sign-in) is also offered but needs a human present
  and has rough edges (no account picker, can drop the connection mid-handshake) — prefer key-in-URL unless
  you specifically want human-in-the-loop authorization of spend.
- **Custom HTTP clients:** send a real `User-Agent` header, or Cloudflare may return a `403`.

The MCP exposes 7 tools: `search-products`, `get-product-details`, `buy-products`,
`submit-prepayment-step`, `list-invoices`, `get-invoice-by-id`, `update-order`.

---

## 1. Choose a test path

Two ways to test without real settlement. Both deliver a real redemption code.

| | **A — Crypto (never paid)** | **B — Test credits (`balance`)** |
| --- | --- | --- |
| Needs setup? | No — works on any key | **Yes — credits must be granted by the Bitrefill team** |
| Product | `test-gift-card-code` (10/20/30/50/100) | `delos-syldavia` (0.01/10/20/50/…) |
| `payment_method` | any crypto, e.g. `usdc_base` | `balance` + `balance_currency` |
| Real settlement? | **No** — a payment link is returned but never paid | **Yes** — debits your *test* credit (no real money) |
| Best for | The default. Proving buy → deliver → redeem | Proving the **account-balance checkout** your app will use |

Use **A** to validate the mechanics today; use **B** when you need to demo paying from an account balance.

---

## 2. Path A — Crypto (zero settlement)

Buy the test product with a crypto method and ask for the payment link:

```jsonc
// buy-products
{
  "cart_items": [{ "product_id": "test-gift-card-code", "package_id": "50" }],
  "payment_method": "usdc_base",
  "return_payment_link": true
}
```

You get back `invoice_id`, `invoice_access_token`, a `payment_link`, and an **`x402_payment_url`**.
**Do not pay any of them** — the test product delivers regardless. This lets you exercise the x402 /
payment-link surface your app integrates **without moving funds**.

> ⚠️ **Skip `get-product-details` for `test-gift-card-*` slugs** — it loops `"did you mean <the same
> slug>"`. The denominations are fixed: **10 / 20 / 30 / 50 / 100**. (Product-details works fine for real
> products and for `delos-syldavia`.)

→ Continue to **Section 4** to poll for delivery.

---

## 3. Path B — Test credits (`balance`)

> Requires test credits on your account. **Ask the Bitrefill team to provision them** — once granted they
> appear as an ordinary balance sub-account (no special API concept).

### Step 1 — Confirm the credits are visible

Read `account_balances` off any product:

```jsonc
// get-product-details  { "product_id": "delos-syldavia", "currency": "USD" }
// → account_balances.balances[] e.g.:
//   { "payment_method": "balance", "balance_currency": "EUR", "balance": 20 }
```

If **every balance reads 0**, your credits aren't on this account (or you're authed into the wrong one).
There is no `whoami` tool, so this zero-reading is your only signal — re-check with the Bitrefill team or
re-auth into the funded account.

### Step 2 — Buy, paying from the credit

```jsonc
// buy-products
{
  "cart_items": [{ "product_id": "delos-syldavia", "package_id": "0.01" }],
  "payment_method": "balance",
  "balance_currency": "EUR"          // REQUIRED — names the funded sub-account
}
```

- `balance_currency` is **mandatory**: it selects which sub-account to debit. Omit it and the call targets
  your (empty) primary sub-account and **fails**.
- Start with the smallest denomination (e.g. **`0.01`**) — it proves the entire path for a fraction of a
  credit, leaving the rest for repeated test runs.

→ Continue to **Section 4** to poll for delivery.

---

## 4. Poll for delivery — the one critical rule

```jsonc
// get-invoice-by-id  { "invoice_id": "...", "invoice_access_token": "..." }
```

✅ **Treat the order as done when `orders[0].status === "delivered"` and
`orders[0].redemption_available === true`.**

🔴 **Do not poll the top-level `invoice_status` / `orders_delivery_status`.** On **`balance`** purchases
these can get **stuck** at `payment_confirmed` / `not_delivered` *even after the order has delivered* — a
loop waiting on them never exits. The per-order `orders[0].status` is reliable for **both** paths, so
always key off it.

Read the redemption code from **`orders[0].redemption_info`** — `pin`, plus `access_link` /
`redemptionLink` / `barcodeFormat` when present.

> Note: **`invoice_id` ≠ `order_id`** — don't pass one where the other is expected.

---

## 5. (Path B) Verify the debit

Re-read `account_balances` after delivery and confirm the drop:

```
EUR 20.00 → 19.98   ✅ credit debited, order delivered
```

> ⚠️ The invoice's reported `price` may not exactly equal the actual debit — **trust the balance delta**,
> not the `price` field, when validating amounts in your app.

---

## What "good" looks like — reference run

A complete Path-B run, captured end-to-end:

1. `get-product-details(delos-syldavia)` → `account_balances` shows **EUR 20**.
2. `buy-products(delos-syldavia, "0.01", balance, EUR)` →
   `payment_info: { method: "balance", status: "payment_initiated" }`.
3. `get-invoice-by-id(...)` → `orders[0].status: "delivered"`, `redemption_info.pin` returned.
4. `get-product-details(...)` again → **EUR 19.98**. ✅ Credit debited, no real money spent.

That four-call shape — **read balance → buy → poll order → re-read balance** — is exactly how your app's
account-balance checkout will behave in production.

---

## Quick gotcha reference

| Symptom | Cause / fix |
| --- | --- |
| `get-product-details` loops "did you mean X" | `test-gift-card-*` only. Skip it; denoms are 10/20/30/50/100. |
| Poll never reaches "complete" | Top-level rollup hangs on `balance`. Use `orders[0].status`. |
| `balance` buy fails | Missing `balance_currency`, or it points at an empty sub-account. |
| All balances read 0 | No test credits on this account — **contact the Bitrefill team**; verify you're on the right account (no `whoami`). |
| Crypto test invoice "complete" with no payment | Expected — test products auto-confirm. Don't gate real logic on `payment_confirmed` in tests. |
| `delos-syldavia` missing from search | Known-slug-only: invisible to `search-products` but resolves in `get-product-details` / `buy`. Hardcode it. |
| `/mcp` returns 403 | Send a real `User-Agent` header. |
