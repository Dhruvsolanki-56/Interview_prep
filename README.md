# Interview Prep — Analyst Interview Lab

A realistic interview-training system for Data Analyst, Product Analyst and BI Analyst roles.

## Current release

**V14 — Retention & Outcome Intelligence**

V14 turns the product into a repeatable preparation loop tied to real target applications and real interview outcomes.

### V14 adds
- one locked weekly benchmark per target application
- Application Cockpit with interview countdown and next-best action
- comeback queue driven by spaced revision, weak mastery and pressure drops
- study-plan adherence inside the cockpit
- personal mock → real interview outcome calibration
- readiness evidence-confidence separate from readiness score
- optional privacy-thresholded company/role interview-process intelligence
- Supabase persistence for signed-in weekly benchmarks
- operator visibility into structured process-report coverage

### Privacy rule for process intelligence
The aggregate layer accepts only structured company/role/round/outcome/difficulty/duration/topic labels. It does not collect exact interview questions, candidate answers, SQL, resume/JD text, transcripts, email or private notes. Company/role groups stay hidden until `PROCESS_INTELLIGENCE_MIN_SAMPLES` is met (default 5).

### Existing capabilities retained
- generated and validated SQL interview questions with alternative-correct grading
- SQL Academy, debugging, optimization, robustness and Explain Your Query
- Excel, statistics, charts/dashboards, Data Modeling and Metric Design
- Data Investigation and take-home assignment/upload grading
- JD-specific interviews and three-person panels
- natural voice, hands-free listening and pressure profiles
- Answer Coach, role readiness and pressure heatmaps
- Supabase-ready accounts, applications and study plans
- readiness sharing, referrals, feedback and beta operator dashboard
- optional Stripe-ready Interview Week / Pro entitlements from V13

## Repository layout

- `releases/` — packaged public-beta releases retained from earlier milestones
- `v13/` — monetization and entitlements release delta
- `v14/` — retention and outcome-intelligence release delta

V14's reviewable delta contains the retention engine, UI/CSS, regression tests, server/beta-ops patches and integration/schema patch.

## Validation

V14 was validated with:
- 42 passing regression tests
- the legacy full-product self-test
- live HTTP weekly-benchmark flow
- a privacy smoke test proving 4 matching process reports stay hidden and the 5th unlocks only aggregate evidence

## Run locally

Use the latest assembled product tree or packaged release, copy `.env.example` to `.env`, add your own credentials locally, install requirements, then run:

```bash
python server.py
```

Never commit `.env`, API keys, Stripe secrets, Supabase service-role keys, local databases or runtime state.

## Repository policy

This repository is the source-of-truth target for completed Interview Prep product releases going forward.
