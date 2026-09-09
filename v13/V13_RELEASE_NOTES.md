# V13 — Monetization & Entitlements

## Goal
Convert the zero-budget beta into a product that can test willingness to pay without destroying the useful free experience.

## Added

- Stripe-hosted Checkout integration using server-side price IDs.
- Interview Week one-time access pass (10 days by default).
- Pro recurring monthly access.
- Optional Founding Annual recurring plan.
- Server-side entitlement enforcement.
- Stripe webhook signature verification and duplicate-event protection.
- Checkout return confirmation against Stripe before granting access.
- Stripe customer billing portal support.
- Free-tier meters for mixed mocks, advanced drills and Answer Coach.
- Referral reward: 2 completed diagnostic referrals can unlock a 48-hour premium pass.
- Plans & billing navigation/UI.
- Current-plan status inside Account and Dashboard.
- Upgrade modal for gated features.
- Billing events and active entitlement counts in the private beta operator dashboard.
- Durable `billing_entitlements` Supabase service-role mirror.
- Recurring-subscription guard before account deletion.
- Payment/privacy language added to beta Privacy/Terms pages.
- Development grant endpoint that is disabled in hosted mode.

## Default safety

V13 does not automatically introduce a paywall.

```env
MONETIZATION_ENABLED=0
MONETIZATION_ENFORCED=0
```

With those defaults, all previous V12 functionality continues to work.

## Suggested launch experiment

Do not enable enforcement until real beta usage exists. When ready, start with:

- Free
- Interview Week: $7.99 one time
- Pro: $14.99/month

Treat those as pricing experiments, not validated market-optimal prices.

## Verification

- Full pytest regression suite passes.
- Legacy `self_test.py` passes.
- Enforced HTTP smoke test confirmed:
  1. first free mixed mock allowed,
  2. second weekly mixed mock gated,
  3. premium Optimization gated,
  4. local Interview Week grant applied,
  5. Optimization immediately unlocked.
