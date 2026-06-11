# Demo run — "send my mom a $50 gift card"

Captured 2026-06-11 against the hosted Bitrefill eCommerce MCP (`api.bitrefill.com/mcp`). The agent
fulfilled the request end-to-end with **no payment made and no store credit debited**. Tool calls shown
via the repo's `scripts/mcp.py` Streamable-HTTP client (same MCP the `/shop` command uses inside Claude Code).

## 1. Buy the test gift card (x402 chain, no payment)

```
buy-products
  cart_items   = [{ product_id: "test-gift-card-code", package_id: "50" }]
  payment_method = "usdc_base"
  return_payment_link = true
→
  invoice_id        = e060de87-e99a-406b-9533-68698c91aff3
  payment_link      = https://www.bitrefill.com/checkout/e060de87-…#tojT6TlTF7Hoad6fWfHy
  x402_payment_url  = https://api.bitrefill.com/x402/invoice/pay
  payment_info      = USDC on Base → 0x253D0AE528613F65f35Ab49DE1b1BB3246618a2F  ($52.49)
```

## 2. Poll until delivered

```
get-invoice-by-id (invoice_id, invoice_access_token)
→
  invoice_status          = complete
  orders_delivery_status  = all_delivered
  created_time            = 2026-06-11T21:25:57.582Z
  delivered_time          = 2026-06-11T21:25:58.085Z   (~0.5s — no real payment sent)
  detected_payment_info.incoming_tx_ids = []            (nothing paid)
```

## 3. Redemption code returned

```
orders[0]
  product      = Test Gift Card Code 50 USD
  status       = delivered
  redemption_info.pin = 9453835738330852
  access_link  = https://www.bitrefill.com/account/6a2b27e5f31d75af09872d87#r54BWW8DGOvonm5kfkKm
```

✅ Product: Test Gift Card Code, $50 · 🔑 PIN: `9453835738330852` · 🧾 invoice `e060de87…` = complete
💸 Paid: **nothing** — `usdc_base` invoice left unpaid; test product auto-delivered. Store credit untouched.

> ⚠️ This run **bypassed `get-product-details`** (broken for test products) and used `test-gift-card-code`
> instead of the brief's `delos-syldavia` (which doesn't resolve). Denominations were discovered from a
> deliberate `buy-products` error. See `FEEDBACK.md` for the full list of issues.
