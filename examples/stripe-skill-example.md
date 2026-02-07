<!--
  This is an example of what /learn stripe would generate.
  Notice how the api-client type emphasizes auth setup, endpoint tables,
  error codes, and rate limits — compared to the framework-focused Hono example.
-->

---
name: stripe
description: Stripe payment processing SDK for Node.js/TypeScript. Use when integrating payments, creating charges, managing subscriptions, handling webhooks, issuing refunds, working with Stripe Checkout, creating payment intents, managing customers, or processing payouts.
version: "17.5.0"
generated: "2026-02-07"
language: typescript
type: api-client
tags: [payments, api, webhooks, sdk, billing, subscriptions, checkout]
---

# Stripe Skill

## When to Use This Skill

Use this skill when the user needs to:
- Integrate Stripe payments into an application
- Create payment intents or charges
- Set up and manage subscriptions and billing
- Handle Stripe webhooks securely
- Create Stripe Checkout sessions
- Manage customers, payment methods, and invoices
- Issue refunds or handle disputes
- Connect accounts (Stripe Connect / marketplace)
- Configure Stripe for different currencies and regions

## Overview

Stripe is a payment processing platform with a comprehensive API for accepting payments, managing subscriptions, and handling complex financial workflows. The Node.js SDK provides a typed, promise-based interface to all Stripe API endpoints. It supports idempotency keys, automatic retries, pagination, and webhook signature verification.

**Key links:**
- Docs: https://docs.stripe.com
- GitHub: https://github.com/stripe/stripe-node
- Package: https://www.npmjs.com/package/stripe

## Prerequisites

- Runtime: Node.js >= 14
- API keys: Secret key (`sk_test_...` / `sk_live_...`) from Stripe Dashboard
- Peer dependencies: none
- Related skills: `hono` or `express` (for webhook endpoints)

## Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| Payment Intents | `stripe.paymentIntents.create()` | Create a payment |
| Customers | `stripe.customers.create()` | Create a customer |
| Subscriptions | `stripe.subscriptions.create()` | Start a subscription |
| Checkout Sessions | `stripe.checkout.sessions.create()` | Hosted checkout page |
| Webhooks | `stripe.webhooks.constructEvent()` | Verify webhook signature |
| Refunds | `stripe.refunds.create()` | Refund a payment |
| Products | `stripe.products.create()` | Create a product |
| Prices | `stripe.prices.create()` | Create a price for a product |
| Invoices | `stripe.invoices.create()` | Create an invoice |
| Payment Methods | `stripe.paymentMethods.attach()` | Attach to customer |

## Installation & Setup

```bash
npm install stripe
```

**Initialize with API key:**
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-12-18.acacia',
})
```

**Environment variables:**
```bash
# .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...  # client-side only
```

**Gotcha:** Never expose `STRIPE_SECRET_KEY` to the client. Use `STRIPE_PUBLISHABLE_KEY` for client-side Stripe.js.

## Core Concepts

- **Payment Intents** — the recommended way to accept payments. Tracks the lifecycle of a payment from creation through confirmation and capture. Replaces the older Charges API.
- **Customers** — represent your users. Attach payment methods to customers for reuse. Required for subscriptions.
- **Webhooks** — Stripe sends events (e.g., `payment_intent.succeeded`, `invoice.paid`) to your server. Always verify the signature. Don't rely solely on client-side confirmation.
- **Idempotency** — pass an `idempotencyKey` to prevent duplicate charges on retries. Critical for payment operations.
- **Test mode vs Live mode** — keys starting with `sk_test_` hit the test API. Switch to `sk_live_` for production. No code changes needed.

## API Reference

### Payment Intents

Create and manage payments with the Payment Intents API.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `amount` | `number` | Yes | — | Amount in smallest currency unit (e.g., cents) |
| `currency` | `string` | Yes | — | Three-letter ISO currency code (e.g., `'usd'`) |
| `customer` | `string` | No | — | Customer ID to charge |
| `payment_method` | `string` | No | — | Payment method ID |
| `confirm` | `boolean` | No | `false` | Immediately confirm the intent |
| `automatic_payment_methods` | `object` | No | — | `{ enabled: true }` to accept all configured methods |
| `metadata` | `object` | No | — | Key-value pairs for your records |
| `idempotencyKey` | `string` | No | — | Prevent duplicate payments |

**Returns:** `Stripe.PaymentIntent` — includes `id`, `status`, `client_secret`, `amount`

**Example:**
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000, // $20.00
  currency: 'usd',
  automatic_payment_methods: { enabled: true },
  metadata: { orderId: 'order_123' },
}, {
  idempotencyKey: 'order_123_payment',
})

// Send client_secret to frontend for confirmation
console.log(paymentIntent.client_secret)
```

**Gotcha:** `amount` is in the smallest currency unit. For USD, 2000 = $20.00, NOT $2000.

### Customers

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `email` | `string` | No | — | Customer email |
| `name` | `string` | No | — | Customer full name |
| `payment_method` | `string` | No | — | Default payment method |
| `metadata` | `object` | No | — | Key-value pairs |

**Returns:** `Stripe.Customer` — includes `id`, `email`, `name`, `default_source`

**Example:**
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

const customer = await stripe.customers.create({
  email: 'user@example.com',
  name: 'Jane Doe',
  metadata: { userId: 'usr_abc123' },
})

// Attach a payment method
await stripe.paymentMethods.attach('pm_card_visa', {
  customer: customer.id,
})

// Set as default
await stripe.customers.update(customer.id, {
  invoice_settings: { default_payment_method: 'pm_card_visa' },
})
```

### Checkout Sessions

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `mode` | `string` | Yes | — | `'payment'`, `'subscription'`, or `'setup'` |
| `line_items` | `array` | Yes | — | Products/prices to charge |
| `success_url` | `string` | Yes | — | Redirect URL after success |
| `cancel_url` | `string` | Yes | — | Redirect URL after cancel |
| `customer` | `string` | No | — | Existing customer ID |
| `customer_email` | `string` | No | — | Pre-fill email for new customers |

**Returns:** `Stripe.Checkout.Session` — includes `id`, `url`, `payment_intent`

**Example:**
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

const session = await stripe.checkout.sessions.create({
  mode: 'payment',
  line_items: [
    {
      price_data: {
        currency: 'usd',
        product_data: { name: 'Premium Plan' },
        unit_amount: 4999, // $49.99
      },
      quantity: 1,
    },
  ],
  success_url: 'https://example.com/success?session_id={CHECKOUT_SESSION_ID}',
  cancel_url: 'https://example.com/cancel',
})

// Redirect user to session.url
```

**Gotcha:** `{CHECKOUT_SESSION_ID}` is a template literal that Stripe replaces — don't interpolate it yourself.

### Webhooks

**Example:**
```typescript
import Stripe from 'stripe'
import { Hono } from 'hono'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)
const app = new Hono()

app.post('/webhooks/stripe', async (c) => {
  const body = await c.req.text()
  const sig = c.req.header('stripe-signature')!

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(
      body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!
    )
  } catch (err) {
    return c.json({ error: 'Invalid signature' }, 400)
  }

  switch (event.type) {
    case 'payment_intent.succeeded': {
      const intent = event.data.object as Stripe.PaymentIntent
      console.log(`Payment ${intent.id} succeeded: $${intent.amount / 100}`)
      break
    }
    case 'invoice.paid': {
      const invoice = event.data.object as Stripe.Invoice
      console.log(`Invoice ${invoice.id} paid`)
      break
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object as Stripe.Subscription
      console.log(`Subscription ${sub.id} canceled`)
      break
    }
  }

  return c.json({ received: true })
})

export default app
```

**Gotcha:** You MUST use the raw request body (not parsed JSON) for signature verification. If your framework auto-parses JSON, use `c.req.text()` or `express.raw()`.

### Subscriptions

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `customer` | `string` | Yes | — | Customer ID |
| `items` | `array` | Yes | — | `[{ price: 'price_...' }]` |
| `trial_period_days` | `number` | No | — | Free trial days |
| `payment_behavior` | `string` | No | `'allow_incomplete'` | `'default_incomplete'` for SCA |
| `default_payment_method` | `string` | No | — | Payment method to use |

**Returns:** `Stripe.Subscription` — includes `id`, `status`, `current_period_end`, `items`

**Example:**
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

const subscription = await stripe.subscriptions.create({
  customer: 'cus_abc123',
  items: [{ price: 'price_monthly_pro' }],
  trial_period_days: 14,
  payment_behavior: 'default_incomplete',
  expand: ['latest_invoice.payment_intent'],
})

// For SCA, send client_secret to frontend
const invoice = subscription.latest_invoice as Stripe.Invoice
const paymentIntent = invoice.payment_intent as Stripe.PaymentIntent
console.log(paymentIntent.client_secret)
```

## Common Patterns

### One-Time Payment (Payment Intents + Checkout)
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

// Server: create checkout session
async function createCheckout(priceId: string, customerId: string) {
  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    customer: customerId,
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: 'https://example.com/success?session_id={CHECKOUT_SESSION_ID}',
    cancel_url: 'https://example.com/cancel',
  })
  return session.url // redirect user here
}

// Server: verify payment completed (webhook handler)
async function handlePaymentSuccess(paymentIntent: Stripe.PaymentIntent) {
  const orderId = paymentIntent.metadata.orderId
  // fulfill the order in your database
  console.log(`Order ${orderId} paid: $${paymentIntent.amount / 100}`)
}
```

### Subscription with Trial
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

async function startSubscription(email: string, paymentMethodId: string) {
  // 1. Create customer
  const customer = await stripe.customers.create({
    email,
    payment_method: paymentMethodId,
    invoice_settings: { default_payment_method: paymentMethodId },
  })

  // 2. Create subscription with trial
  const subscription = await stripe.subscriptions.create({
    customer: customer.id,
    items: [{ price: 'price_monthly_pro' }],
    trial_period_days: 14,
    expand: ['latest_invoice.payment_intent'],
  })

  return { customerId: customer.id, subscriptionId: subscription.id }
}
```

### Paginating Through Resources
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

// Auto-pagination — handles all pages automatically
async function getAllCustomers(): Promise<Stripe.Customer[]> {
  const customers: Stripe.Customer[] = []
  for await (const customer of stripe.customers.list({ limit: 100 })) {
    customers.push(customer)
  }
  return customers
}

// Manual pagination
async function getCustomerPage(startingAfter?: string) {
  const result = await stripe.customers.list({
    limit: 10,
    starting_after: startingAfter,
  })
  return {
    customers: result.data,
    hasMore: result.has_more,
    lastId: result.data[result.data.length - 1]?.id,
  }
}
```

### Issuing a Refund
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

// Full refund
const fullRefund = await stripe.refunds.create({
  payment_intent: 'pi_abc123',
})

// Partial refund
const partialRefund = await stripe.refunds.create({
  payment_intent: 'pi_abc123',
  amount: 500, // refund $5.00
})
```

## Error Handling

| Error Type | Status | Cause | Fix |
|------------|--------|-------|-----|
| `StripeCardError` | 402 | Card declined, insufficient funds, expired | Show user-friendly message, ask for different card |
| `StripeRateLimitError` | 429 | Too many API requests | Implement exponential backoff, use idempotency keys |
| `StripeInvalidRequestError` | 400 | Invalid parameters, missing required fields | Check param names/types against docs |
| `StripeAuthenticationError` | 401 | Invalid API key | Verify `STRIPE_SECRET_KEY` is set and correct |
| `StripeConnectionError` | — | Network failure | Retry with backoff, check connectivity |
| `StripeAPIError` | 500+ | Stripe server error | Retry with backoff, check status.stripe.com |
| `StripeSignatureVerificationError` | — | Webhook signature mismatch | Use raw body, verify `STRIPE_WEBHOOK_SECRET` |

**Error handling pattern:**
```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

try {
  const intent = await stripe.paymentIntents.create({
    amount: 2000,
    currency: 'usd',
  })
} catch (err) {
  if (err instanceof Stripe.errors.StripeCardError) {
    console.log(`Card declined: ${err.message}`)
    // Show user: "Your card was declined. Please try a different card."
  } else if (err instanceof Stripe.errors.StripeRateLimitError) {
    console.log('Rate limited, retrying...')
    // Implement retry logic
  } else if (err instanceof Stripe.errors.StripeInvalidRequestError) {
    console.error(`Bad request: ${err.message}`)
    // Developer error — fix the request
  } else {
    console.error('Unexpected Stripe error:', err)
    throw err
  }
}
```

## TypeScript Integration

Stripe's SDK is fully typed. Key patterns:

```typescript
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

// All responses are typed
const customer: Stripe.Customer = await stripe.customers.create({
  email: 'user@example.com',
})

// Use expand + type assertions for nested objects
const subscription = await stripe.subscriptions.retrieve('sub_123', {
  expand: ['latest_invoice.payment_intent'],
})
const invoice = subscription.latest_invoice as Stripe.Invoice
const intent = invoice.payment_intent as Stripe.PaymentIntent

// Webhook event typing
function handleEvent(event: Stripe.Event) {
  switch (event.type) {
    case 'payment_intent.succeeded':
      const pi = event.data.object as Stripe.PaymentIntent
      break
    case 'customer.subscription.created':
      const sub = event.data.object as Stripe.Subscription
      break
  }
}

// List params are typed
const params: Stripe.CustomerListParams = {
  limit: 10,
  created: { gte: Math.floor(Date.now() / 1000) - 86400 },
}
```

**Key types to know:**
| Type | Purpose |
|------|---------|
| `Stripe.PaymentIntent` | Payment intent object |
| `Stripe.Customer` | Customer object |
| `Stripe.Subscription` | Subscription object |
| `Stripe.Invoice` | Invoice object |
| `Stripe.Event` | Webhook event envelope |
| `Stripe.Checkout.Session` | Checkout session object |
| `Stripe.PaymentIntentCreateParams` | Create params (typed) |
| `Stripe.errors.StripeCardError` | Card error class |

## Testing

Use Stripe's test mode and test card numbers:

```typescript
import Stripe from 'stripe'
import { describe, it, expect, beforeAll } from 'vitest'

// Use test key
const stripe = new Stripe('sk_test_...')

describe('Stripe integration', () => {
  let customerId: string

  beforeAll(async () => {
    const customer = await stripe.customers.create({
      email: 'test@example.com',
    })
    customerId = customer.id
  })

  it('creates a payment intent', async () => {
    const intent = await stripe.paymentIntents.create({
      amount: 1000,
      currency: 'usd',
      customer: customerId,
    })
    expect(intent.status).toBe('requires_payment_method')
    expect(intent.amount).toBe(1000)
  })

  it('creates a checkout session', async () => {
    const session = await stripe.checkout.sessions.create({
      mode: 'payment',
      customer: customerId,
      line_items: [{ price_data: { currency: 'usd', product_data: { name: 'Test' }, unit_amount: 500 }, quantity: 1 }],
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
    })
    expect(session.url).toContain('checkout.stripe.com')
  })
})
```

**Test card numbers:**
| Card | Number | Behavior |
|------|--------|----------|
| Success | `4242424242424242` | Always succeeds |
| Decline | `4000000000000002` | Always declines |
| Requires auth | `4000002500003155` | Triggers 3D Secure |
| Insufficient funds | `4000000000009995` | Insufficient funds error |

## Deprecated / Avoid

| Deprecated API | Replacement | Since Version |
|----------------|-------------|---------------|
| `stripe.charges.create()` | `stripe.paymentIntents.create()` | v2019-02+ |
| `stripe.tokens.create()` (server-side) | Client-side Stripe.js `confirmCardPayment()` | PCI compliance |
| Source objects (`src_...`) | Payment Methods (`pm_...`) | v2020+ |
| `stripe.subscriptions.del()` | `stripe.subscriptions.cancel()` | v14.0.0 |

**Common mistakes to avoid:**
- Using Charges API instead of Payment Intents — Charges don't support SCA/3D Secure
- Creating tokens server-side — violates PCI compliance; use Stripe.js on the client
- Not verifying webhook signatures — anyone could send fake events to your endpoint
- Parsing webhook body as JSON before verification — signature check requires raw body

## Important Rules

1. **Always use Payment Intents, not Charges** — Charges API doesn't handle SCA/3D Secure and will fail in EU regions
2. **Verify webhook signatures** — use `stripe.webhooks.constructEvent()` with the raw body. Never trust unverified webhook data.
3. **Use idempotency keys for mutations** — pass `idempotencyKey` on create/update operations to prevent duplicate charges on retries
4. **Amount is in cents** — `amount: 2000` means $20.00. Off-by-100x errors are the #1 Stripe bug.
5. **Never log or expose secret keys** — use environment variables, never hardcode `sk_live_...`
6. **Use `expand` sparingly** — expanded objects increase response size and latency. Only expand what you need.
7. **Handle async payment flows** — not all payments succeed immediately. Listen for `payment_intent.succeeded` webhook instead of assuming success after create.
8. **Set `apiVersion` explicitly** — pin to a specific API version to avoid breaking changes on Stripe's rolling updates
