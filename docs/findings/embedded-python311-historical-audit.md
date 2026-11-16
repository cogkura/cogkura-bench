# Python 3.11 historical-gold audit (in progress)

The [field-level raw audit](data/embedded-core-0.19.5-release-frozen-311-audit.json) compares original frozen gold, the previously recorded Core 0.18.4 same-runtime run, and the public Core 0.19.5 run. The input digests are included. It enumerates every differing metric and query fingerprint without changing gold or approving a result. Reproduce it with:

```bash
uv run python scripts/audit_python311_frozen.py \
  --gold tests/golden/cogkura_0182_frozen.json \
  --previous docs/findings/data/embedded-core-0.18.4-frozen-311-historical.json \
  --current docs/findings/data/embedded-core-0.19.5-release-frozen-311.json \
  --output results/python311-audit.json
```

The comparison lists 71 differing fields across 17 runs: 61 numeric metric values and 10 query fingerprints. Every current field equals the earlier Core's corresponding value under the same recorded Python 3.11 environment. The largest absolute numeric difference is approximately `2.22e-16`; small magnitude alone does not authorise a tolerance. One fingerprint is the separately approved `ac-q-c20` correction; the other nine fingerprints required the query-detail investigation below; hashes alone cannot reveal the differing fields.

The 16 other run-level frozen failures and these nine fingerprints remain unapproved. Controlled repeated runs and any candidate-specific acceptance remain necessary. Do not treat same-runtime equality with the earlier Core as proof that every difference is representational or harmless.

A follow-up [query-detail audit](data/embedded-core-0.19.5-macos311-312-query-differences.json) regenerated the public Core results on macOS with Python 3.11 and 3.12. Before comparing details, it verified that each Python 3.12 signature reproduced the original gold fingerprint and each Python 3.11 signature reproduced the recorded raw result. For all nine unapproved query fingerprints, the 52 differing fields are floating-point activation or assessment-signal values; the maximum absolute difference is `4.44e-16`. Retrieved identities, ordering, text, and other fields of these nine query signatures match. The earlier same-runtime Core comparison also matched all 22 complete runs. This characterises the observed differences; it does not approve any tolerance, establish that all possible environments behave similarly, or change the raw frozen gate.

The archived full signatures are reproducible inputs. To repeat the field-level check (which verifies hashes first and does not approve differences):

```bash
uv run python scripts/compare_frozen_query_details.py \
  --gold tests/golden/cogkura_0182_frozen.json \
  --report docs/findings/data/embedded-core-0.19.5-release-frozen-311.json \
  --gold-details docs/findings/data/embedded-core-0.19.5-macos312-details.json.gz \
  --actual-details docs/findings/data/embedded-core-0.19.5-macos311-details.json.gz \
  --output results/python311-query-details.json
```
