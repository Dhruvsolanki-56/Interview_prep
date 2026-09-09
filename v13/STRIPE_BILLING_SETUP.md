# V13 Stripe billing setup

V13 adds optional monetization. Nothing is charged or gated unless you explicitly enable it.

## Plans in the build

- **Free** — readiness diagnostic, SQL Academy, core SQL practice, limited mixed mocks and limited advanced drills.
- **Interview Week** — one-time payment, 10 days by default. Unlocks JD interviews, mock panel, Interview Day, take-homes, investigations, advanced labs and expanded coaching.
- **Pro** — recurring monthly subscription. Requires sign-in so access follows the user's account across devices.
- **Founding Annual** — optional recurring annual plan. It is hidden unless `STRIPE_PRICE_FOUNDING_ANNUAL` is configured.
- **Referral Pass** — 48-hour premium reward by default after 2 distinct referred users complete the readiness diagnostic.

## 1. Create Stripe products/prices

In Stripe Dashboard, create prices for the offers you want to enable. Keep the actual price IDs in server environment variables, never frontend JavaScript.

Recommended initial product structure:

- Interview Week: one-time USD price
- Pro: recurring monthly USD price
- Founding Annual: recurring yearly USD price (optional)

## 2. Configure `.env`

```env
MONETIZATION_ENABLED=1
# Keep enforcement off while testing Checkout and webhooks.
MONETIZATION_ENFORCED=0

PUBLIC_BASE_URL=https://YOUR_PUBLIC_APP_URL

STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_INTERVIEW_WEEK=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_FOUNDING_ANNUAL=

INTERVIEW_WEEK_DISPLAY_PRICE=$7.99
PRO_MONTHLY_DISPLAY_PRICE=$14.99
FOUNDING_ANNUAL_DISPLAY_PRICE=$49
INTERVIEW_WEEK_DAYS=10
REFERRAL_REWARD_HOURS=48
```

Do not commit `.env`.

## 3. Run the V13 Supabase schema update

Run `supabase_schema.sql` again in Supabase SQL Editor. V13 adds `billing_entitlements` as a server-managed RLS table. There is intentionally no browser policy for that table.

For durable entitlement mirroring on Render, configure:

```env
SUPABASE_SERVICE_ROLE_KEY=...
```

The service-role key must exist only on the Python server.

## 4. Configure the Stripe webhook

Create an endpoint pointing to:

```text
https://YOUR_PUBLIC_APP_URL/api/billing/webhook
```

Subscribe at minimum to:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

Copy the endpoint signing secret into `STRIPE_WEBHOOK_SECRET`.

V13 verifies the raw request body against the `Stripe-Signature` header before processing an event. Webhook event IDs are stored so duplicate delivery is idempotent.

## 5. Test before enforcement

Keep:

```env
MONETIZATION_ENFORCED=0
```

Then test:

1. Open **Plans**.
2. Start Interview Week Checkout in Stripe test mode.
3. Return to the app after successful Checkout.
4. Verify `/api/billing/status` shows `interview_week`.
5. Sign in and test Pro Checkout.
6. Use the Stripe customer portal from Plans & billing.
7. Verify the private operator dashboard shows billing signals.
8. Test webhook retries and duplicate delivery.

The success-return flow also confirms the Checkout Session directly with Stripe and validates its `client_reference_id`. Webhooks remain the canonical lifecycle mechanism for recurring subscriptions.

## 6. Turn on enforcement

Only after test-mode Checkout/webhooks work:

```env
MONETIZATION_ENFORCED=1
```

Current free-tier enforcement:

- 1 mixed full/resume mock per ISO week
- 3 free advanced drills per UTC day across SQL Debugging / Chart / Statistics
- 2 Answer Coach uses per UTC day
- diagnostic and SQL Academy remain free

Paid-only surfaces when enforcement is on:

- JD-specific interview
- Mock Panel
- Interview Day
- Optimization
- Data Investigation
- Take-home Simulator
- Data Modeling
- Metric Design

Natural voice retains the existing API usage guard rather than being hard-paywalled in V13.

## 7. Account deletion rule

A user with an active recurring Pro/Annual subscription cannot delete the account from the app until they manage/cancel the active subscription in the Stripe billing portal. This prevents a login from disappearing while billing continues invisibly.

One-time Interview Week access does not have this recurring-billing restriction.

## 8. Development testing without Stripe

In local mode only:

```http
POST /api/billing/dev-grant
{"plan":"interview_week"}
```

This is rejected when `HOSTED_MODE=1`.

## Security boundaries

- Stripe-hosted Checkout collects payment details; the app never needs full card numbers.
- Secret key and webhook secret are server-only.
- Subscription access is checked server-side on protected endpoints.
- Frontend lock icons/buttons are presentation only and are not the security boundary.
- Recurring Pro requires authentication.
- Guest Interview Week can be purchased, but its entitlement is browser/client-bound. Sign in before purchase if cross-device continuity matters.
