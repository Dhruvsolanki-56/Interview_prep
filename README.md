# Interview Prep — Analyst Interview Lab

A realistic interview-training system for Data Analyst, Product Analyst and BI Analyst roles.

## Current release

**V12 — Public Beta Launch Operations**

Includes:
- generated and validated SQL interview questions
- alternative-correct SQL grading
- SQL Academy, debugging, optimization and robustness testing
- Excel, statistics, dashboard/chart and business-case rounds
- Data Investigation and take-home assignments
- JD-specific interviews and three-person mock panels
- natural voice, hands-free listening and pressure profiles
- Answer Coach and role-readiness analytics
- Supabase-ready accounts, applications and study plans
- beta onboarding, privacy-safe readiness sharing and referrals
- in-product feedback and private beta operator dashboard

The complete V12 source package is stored at:

`releases/Analyst_Interview_Lab_V12_Beta_Launch_Ops.zip`

## Run locally

1. Extract the V12 release archive.
2. Copy `.env.example` to `.env`.
3. Add your own API/config values locally. Never commit `.env`.
4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Start:

```bash
python server.py
```

6. Open `http://localhost:8000`.

## Repository policy

This repository is the source-of-truth target for completed Interview Prep product releases going forward.

Secrets, `.env`, local databases, runtime state and API keys must never be committed.
