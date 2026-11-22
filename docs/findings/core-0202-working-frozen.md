# Core 0.20.2 working-tree frozen comparison

**Exploratory only; raw gate failed and no candidate is approved.** The Bench
runner used Core 0.20.2 from the editable working tree, with Core commit
`a62196b8ec37ca07f36900ea6173514083ae7d40` plus an uncommitted Core source
diff (SHA-256
`6dda332c0ad3627c92a251b2b340b8173cadbca92cf4e12354300884a9fe51ea`). Bench
was at `31da1674b18e27a761f338a4dd32ffd122f22a21` with uncommitted compatibility
changes; its tracked `src`, `pyproject.toml` and `tests` diff SHA-256 was
`26cdf1c069dbfd7e4ddc725bca70dc9f306ef26eab1192bb893e73e6014ab8fe`.
Both were run on local CPython 3.11.15 with PostgreSQL 14.18. These identities
are not a clean, exact installed candidate distribution.

The raw comparison against the original gold reports 20 unapproved run-level
mismatches and a failed release gate. Its complete run fingerprints exactly
match the previously retained 0.20.1 official-source raw report on the same
Python patch version, and its unapproved mismatch list is identical. This is a
comparison with the earlier evidence, not an approval of those mismatches for
0.20.2. Diagnostic parity and PostgreSQL parity passed; source-history v2
matched 191/191 checks and its PostgreSQL comparison passed.

[Raw report](core-0202-working-frozen-raw.json.gz) and
[complete query details](core-0202-working-frozen-details.json.gz) are retained.
Freeze and install the exact candidate, rerun the comparison, investigate all
differences and obtain a separate candidate-specific review before release.
