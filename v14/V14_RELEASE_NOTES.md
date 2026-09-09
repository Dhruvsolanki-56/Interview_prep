# V14 — Retention & Outcome Intelligence

V14 turns the product from a collection of strong interview modes into a repeatable preparation loop tied to a real job application.

## Weekly Benchmark
- One locked comparable mixed interview per ISO week.
- Uses the same validated interview engine and final hiring/debrief pipeline as normal sessions.
- Can be grounded in a saved target application's role, company, resume and JD.
- Benchmark history tracks score/verdict/skill breakdown and is mirrored into Supabase for signed-in users.
- Users practice freely between benchmarks rather than repeatedly retaking the weekly checkpoint.

## Application Cockpit
Each saved target job now gets a cockpit with:
- countdown to interview
- weekly benchmark due/completed state
- next best action
- spaced-repetition comeback queue
- study-plan adherence and overdue work
- benchmark trend
- readiness-evidence confidence
- personal mock-to-real outcome calibration
- privacy-thresholded company/role process intelligence when enough aggregate evidence exists

## Outcome calibration
- Pairs a reported real interview outcome with the latest relevant completed mock for the same application.
- Tiny samples are explicitly labeled insufficient.
- A descriptive personal bar appears only after enough paired outcomes exist.
- This is not a pass-probability model or market benchmark.

## Anonymous process intelligence
Candidates may optionally contribute only structured fields:
- company
- role
- round type
- outcome
- perceived difficulty
- duration bucket
- topic labels

The aggregate layer does **not** accept exact questions, candidate answers, SQL, resume/JD text, voice transcript, email or private notes.

Company/role groups remain hidden until `PROCESS_INTELLIGENCE_MIN_SAMPLES` is met (default 5). Evidence is labeled `early`, `developing` or `stronger` based on sample size.

## Operator dashboard
The private beta dashboard now shows:
- number of structured process reports
- number of company/role groups above the privacy threshold
- thresholded top topics for visible groups

## Validation
- 42 regression tests passing.
- Legacy full product self-test still passes.
- Live HTTP smoke test verified application → weekly benchmark → session completion → weekly trend.
- Privacy smoke test verified 4 reports remain hidden and the 5th matching report unlocks only aggregate evidence.
