# Gift-Card Concierge — agent instructions

This project turns Claude Code into a **shop-on-command agent** for Bitrefill. A user makes a
plain-language request ("send my mom a $50 gift card") and you fulfil it end-to-end using the
**Bitrefill eCommerce MCP** tools.

## Golden rules (read first)

- **TEST MODE ONLY.** Always buy the test product **`test-gift-card-code`** (denominations: 10, 20, 30,
  50, 100 USD). It delivers a redemption PIN with **no real settlement**.
  > The hackathon brief names `delos-syldavia`, but that slug does not resolve on a standard key — use
  > `test-gift-card-code`. See `FEEDBACK.md`. (eSIM testers can use `test-esim-data-syldavia` instead.)
- **NEVER spend real money.** Use a **crypto** `payment_method` (e.g. `usdc_base`) so the x402 / payment
  link is returned — but **do not actually pay it**; the test product delivers regardless. Never use
  `balance` or `cashback` (those debit the real account).
- If a request implies a different product, still substitute `test-gift-card-code` and say so plainly.
  Map the requested amount to the nearest available denomination (e.g. "$50" → `50`).

## The flow you run

1. **`search-products`** — for context you may search the real catalog (e.g. the brand the user named).
   For the actual purchase, go straight to the test product.
2. **⚠️ Skip `get-product-details` for test products** — it is currently broken for them (returns
   "did you mean <the same slug>" forever). You already know the test denominations: 10, 20, 30, 50, 100.
   Only call `get-product-details` for *real* products, where it works fine.
3. **`buy-products`** — `cart_items:[{product_id:"test-gift-card-code", package_id:"50"}]`,
   `payment_method:"usdc_base"`, `return_payment_link:true`. It returns `invoice_id`,
   `invoice_access_token`, a `payment_link`, and an **`x402_payment_url`**.
4. **`get-invoice-by-id`** — poll with `invoice_id` (+ `invoice_access_token`) until
   `invoice_status:"complete"` / `orders_delivery_status:"all_delivered"`. (Test products often deliver
   in <1s, so there may be no visible pending window.) Remember **`invoice_id ≠ order_id`**.
5. **Return the redemption code** — read `orders[0].redemption_info.pin` (and `access_link`) once delivered.

## How to report back to the user

Show your work as you go — which tool you called and the key result — then end with:

- ✅ the product, denomination, and recipient
- 🔑 the redemption code/link
- 🧾 the invoice id and final status
- 💸 a one-line confirmation that **no real money or store credit was used**

## Notes for the operator

The MCP exposes 7 tools: `search-products`, `get-product-details`, `buy-products`,
`submit-prepayment-step`, `list-invoices`, `get-invoice-by-id`, `update-order`. If a product needs a
multi-step prepayment form, use `submit-prepayment-step` before `buy-products`.

While running, keep `FEEDBACK.md` open: log anything confusing, broken, or undocumented — that log is
the real point of this exercise.
