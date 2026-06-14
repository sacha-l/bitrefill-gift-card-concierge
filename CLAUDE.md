# Gift-Card Concierge — agent instructions

This project turns Claude Code into a **shop-on-command agent** for Bitrefill. A user makes a
plain-language request ("send my mom a $50 gift card") and you fulfil it end-to-end using the
**Bitrefill eCommerce MCP** tools.

## Golden rules (read first)

- **TEST MODE ONLY.** Always buy the test product **`test-gift-card-code`** (denominations: 10, 20, 30,
  50, 100 USD). It delivers a redemption PIN with **no real settlement**.
  > Use `test-gift-card-code` for the **default crypto path** (denoms 10/20/30/50/100). For the
  > **test-credit (`balance`) path**, use the brief's **`delos-syldavia`** instead — it *does* resolve via
  > `get-product-details`/`buy` (it's only invisible to `search-products`), accepts `balance`, and has a
  > `0.01` denomination ideal for a low-cost credit test. See `FEEDBACK.md`. (eSIM testers can use
  > `test-esim-data-syldavia`.)
- **NEVER spend real money. Two safe payment paths:**
  - **Default — crypto, never paid.** Use a **crypto** `payment_method` (e.g. `usdc_base`) so the x402 /
    payment link is returned — but **do not actually pay it**; the test product delivers regardless.
  - **Opt-in — test credits via `balance`.** ONLY when the user explicitly says to spend their **test
    credits**: use `payment_method:"balance"` **plus `balance_currency`** naming the funded sub-account
    (e.g. `"EUR"` — check `account_balances` first; omitting it defaults to the empty primary and fails).
    This *does* debit the credit, so confirm the amount first and buy a tiny denomination (e.g. `0.01`).
  - Never use **`cashback`**, and never use `balance` against a real-money (non-test-credit) account.
- If a request implies a different product, still substitute `test-gift-card-code` and say so plainly.
  Map the requested amount to the nearest available denomination (e.g. "$50" → `50`).

## The flow you run

1. **`search-products`** — for context you may search the real catalog (e.g. the brand the user named).
   For the actual purchase, go straight to the test product.
2. **⚠️ Skip `get-product-details` for test products** — it is currently broken for them (returns
   "did you mean <the same slug>" forever). You already know the test denominations: 10, 20, 30, 50, 100.
   Only call `get-product-details` for *real* products, where it works fine.
3. **`buy-products`** —
   - *Default (crypto):* `cart_items:[{product_id:"test-gift-card-code", package_id:"50"}]`,
     `payment_method:"usdc_base"`, `return_payment_link:true`. Returns `invoice_id`,
     `invoice_access_token`, a `payment_link`, and an **`x402_payment_url`** (don't pay it).
   - *Test credits (opt-in):* `cart_items:[{product_id:"delos-syldavia", package_id:"0.01"}]`,
     `payment_method:"balance"`, `balance_currency:"EUR"`. Returns
     `payment_info:{method:"balance", status:"payment_initiated"}` — this debits the credit.
4. **`get-invoice-by-id`** — poll with `invoice_id` (+ `invoice_access_token`) until delivered.
   **Key off `orders[0].status === "delivered"` + `redemption_available:true`, NOT the top-level
   `invoice_status`/`orders_delivery_status`.** The top-level rollup reaches `complete`/`all_delivered`
   for crypto buys, but on **`balance`** buys it gets **stuck** at `payment_confirmed`/`not_delivered`
   even after the order is delivered — so a top-level poll loops forever (see `FEEDBACK.md`, 2026-06-14).
   `orders[0].status` is correct for both. (Test products often deliver in <1s, so there may be no visible
   pending window.) Remember **`invoice_id ≠ order_id`**.
5. **Return the redemption code** — read `orders[0].redemption_info.pin` (and `access_link`) once delivered.

## How to report back to the user

Show your work as you go — which tool you called and the key result — then end with:

- ✅ the product, denomination, and recipient
- 🔑 the redemption code/link
- 🧾 the invoice id and final status (read from `orders[0].status`)
- 💸 a one-line settlement confirmation: for the **crypto** path, that **no real money or store credit was
  used**; for the **test-credit** path, that only **test credits** were debited (state the before→after
  balance, e.g. €20 → €19.98) and **no real money** was spent

## Notes for the operator

The MCP exposes 7 tools: `search-products`, `get-product-details`, `buy-products`,
`submit-prepayment-step`, `list-invoices`, `get-invoice-by-id`, `update-order`. If a product needs a
multi-step prepayment form, use `submit-prepayment-step` before `buy-products`.

While running, keep `FEEDBACK.md` open: log anything confusing, broken, or undocumented — that log is
the real point of this exercise.
