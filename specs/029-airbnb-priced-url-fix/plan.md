# Plan 029 - Airbnb Priced URL Fix

1. Reproduce the live price failure against the current adapter path and lock in
   the root cause with a small matrix of actor-input cases.
2. Fix the `tri_angle` actor input builder:
   - strip query params from the room URL used in `startUrls`
   - pass stay dates and occupancy fields explicitly
3. Extend normalized price data for dated stays:
   - preserve exact total
   - preserve stay dates and number of nights
   - capture nightly rate when it can be derived safely
   - capture service / cleaning fees from the actor breakdown
4. Improve downstream price usage:
   - enrich the AI prompt with stay-level price context
   - add exact stay-price rendering to Telegram output
5. Add focused regression tests plus full-suite validation.
6. Open PR, drive checks to green, merge, deploy, and smoke on the server.
