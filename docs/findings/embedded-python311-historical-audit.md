# Python 3.11 historical-gold audit (in progress)

The [field-level raw audit](data/embedded-core-0.19.5-release-frozen-311-audit.json) compares original frozen gold, the previously recorded Core 0.18.4 same-runtime run, and the public Core 0.19.5 run. The input digests are included. It enumerates every differing metric and query fingerprint without changing gold or approving a result. Reproduce it with:

```bash
uv run python scripts/audit_python311_frozen.py \
  --gold tests/golden/cogkura_0182_frozen.json \
  --previous docs/findings/data/embedded-core-0.18.4-frozen-311-historical.json \
  --current docs/findings/data/embedded-core-0.19.5-release-frozen-311.json \
  --output results/python311-audit.json
```

The comparison lists 71 differing fields across 17 runs: 61 numeric metric values and 10 query fingerprints. Every current field equals the earlier Core's corresponding value under the same recorded Python 3.11 environment. The largest absolute numeric difference is approximately `2.22e-16`; small magnitude alone does not authorise a tolerance. One fingerprint is the separately approved `ac-q-c20` correction; the other nine fingerprints remain unexplained, as hashes alone cannot reveal which ranked identity, ordering, score or rendered detail differs.

The 16 other run-level frozen failures and these nine fingerprints remain unapproved. A complete diagnosis still requires captured query-level details against historical gold and controlled reruns demonstrating determinism. Do not treat same-runtime equality with the earlier Core as proof that every difference is representational or harmless.
