# V12 — Public Beta Launch Operations

V12 adds the beta launch layer on top of the interview platform.

## Highlights

- First-visit role onboarding without requiring signup.
- Privacy-safe readiness share links.
- Referral attribution from shared diagnostic results.
- In-product beta feedback queue.
- Private `/admin.html` beta operator dashboard protected by a server-side token.
- Launch-readiness checks for hosted mode, Supabase, persistence, admin access and optional AI/telemetry.
- Durable server-managed beta events, shares, referrals and feedback schema.
- Hosted-mode smoke tests and regression coverage.

## Validation

26 automated regression tests passed in the packaged build, plus the existing end-to-end product self-test.

## Security

The release archive excludes `.env`, API keys, local SQLite databases, runtime cache and guest history.
