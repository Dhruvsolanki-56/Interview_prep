# Interview Prep — Analyst Interview Lab

A realistic interview-training system for Data Analyst, Product Analyst and BI Analyst roles.

## Current release

**V13 — Monetization & Entitlements**

V13 adds optional Stripe-ready monetization on top of the complete V12 public-beta product while keeping monetization **disabled by default**.

### V13 adds
- Interview Week one-time access pass
- Pro monthly subscription
- optional Founding Annual plan
- server-side entitlement enforcement
- Stripe-hosted Checkout and billing portal
- verified/idempotent Stripe webhooks
- free-tier meters for mixed mocks, advanced drills and Answer Coach
- referral premium unlocks
- Plans & billing UI
- active billing signals in the private operator dashboard
- Supabase-backed durable entitlement mirror
- recurring-subscription safety before account deletion

### Existing product capabilities retained
- generated and validated SQL interview questions
- alternative-correct SQL grading
- SQL Academy, debugging, optimization and robustness testing
- Excel, statistics, dashboard/chart and business-case rounds
- Data Investigation and take-home assignments
- Data Modeling and Metric Design rounds
- JD-specific interviews and three-person mock panels
- natural voice, hands-free listening and pressure profiles
- Answer Coach and role-readiness analytics
- Supabase-ready accounts, applications and study plans
- beta onboarding, privacy-safe readiness sharing and referrals
- in-product feedback and private beta operator dashboard

## Repository layout

The V12 full packaged build remains under `releases/`.

The V13 release delta is reviewable under:

```text
v13/
  V13_RELEASE_NOTES.md
  STRIPE_BILLING_SETUP.md
  source/
    monetization_engine.py
    static/v13.js
    static/v13.css
  tests/test_v13_monetization.py
  patches/server.py.patch
  patches/integration.patch
```

The downloadable V13 build generated from this release is named:

`Analyst_Interview_Lab_V13_Monetization_Entitlements.zip`

## Run locally

1. Start from the V12 packaged source or the latest assembled product tree.
2. Apply the V13 source/integration changes.
3. Copy `.env.example` to `.env`.
4. Add your own API/config values locally. Never commit `.env`.
5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Start:

```bash
python server.py
```

7. Open `http://localhost:8000`.

## Monetization safety

Payments and gating remain off unless explicitly enabled:

```env
MONETIZATION_ENABLED=0
MONETIZATION_ENFORCED=0
```

See [`v13/STRIPE_BILLING_SETUP.md`](v13/STRIPE_BILLING_SETUP.md) before enabling Stripe.

## Repository policy

This repository is the source-of-truth target for completed Interview Prep product releases going forward.

Secrets, `.env`, local databases, runtime state, Stripe secrets and API keys must never be committed.
