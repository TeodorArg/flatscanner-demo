# Plan 030 - Triangle Geo Context Fix

1. Lock in the live `tri_angle` location shape that currently slips through the
   adapter (`coordinates`, `locationSubtitle`, string `location`).
2. Patch Airbnb normalization to read coordinates from the `coordinates`
   object and derive coarse location labels from subtitle-style fields.
3. Harden prompt construction so empty enrichment payloads are skipped instead
   of rendered as false zero-count facts.
4. Add focused regression tests and run the relevant test subset.
5. Deploy the fix to the server and run a live smoke against the affected
   Airbnb listing.
