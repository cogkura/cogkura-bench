# Embedded Core 0.19.5 candidate validation

Bench's development dependency is pinned to Core commit `f289035351e3c101fd932f4d6d9e9cd56583ace0`. Its package metadata still says `0.18.4`; the exact Git identity, not that version string, identifies the candidate. No dataset, original frozen gold, retrieval algorithm or benchmark score was changed for this validation.

## Tests and workloads

The PostgreSQL-enabled Bench suite passed on Python 3.11.15, 3.12.13 and 3.13.14, with 326 tests per runtime. All 13 datasets validated and ran with Oracle; the mini token-overlap run and all configured CogKura CLI smoke profiles passed.

The four-workload three-backend comparison exercised the complete in-memory, SQLite and PostgreSQL storage bundles. SQLite was also closed and reopened after each preparation. On all three Python versions, the raw comparison found only the three previously reviewed supporting-event order differences; the explicit `f289035` approval accounts for those exact fingerprints without changing the raw reports. The mini and persistent-inhibition workloads match exactly. All compared aggregate metrics, use signatures and source-assessment observations match. Separate repeated mini runs on the same PostgreSQL database pass under all three Python versions and check that tenant learning state does not leak between runs.

| Python | Raw three-backend report | Reviewed comparison | PostgreSQL repeat |
| --- | --- | --- | --- |
| 3.11 | [raw](data/embedded-core-0.19.5-threeway-311-raw.json) | [reviewed](data/embedded-core-0.19.5-threeway-311-reviewed.json) | [repeat](data/embedded-core-0.19.5-postgres-repeat-311.json) |
| 3.12 | [raw, including repeat](data/embedded-core-0.19.5-threeway-312-raw.json) | [reviewed](data/embedded-core-0.19.5-threeway-312-reviewed.json) | included in raw report |
| 3.13 | [raw](data/embedded-core-0.19.5-threeway-313-raw.json) | [reviewed](data/embedded-core-0.19.5-threeway-313-reviewed.json) | [repeat](data/embedded-core-0.19.5-postgres-repeat-313.json) |

## Frozen comparison and Python 3.11

The exact Git-installed candidate passes the original frozen comparison on [Python 3.12](data/embedded-core-0.19.5-frozen-312.json) and [Python 3.13](data/embedded-core-0.19.5-frozen-313.json), with only the separately approved `ac-q-c20` correction. The reports preserve the original raw failure and show no unapproved differences. PostgreSQL source diagnostics pass and diagnostic-on/off comparisons match.

The same original frozen comparison **does not pass on Python 3.11**: its [candidate report](data/embedded-core-0.19.5-frozen-311.json) retains 16 unapproved run-level differences after the approved correction. These include very small floating-point differences in aggregate metrics; for example, one precision value is `0.2375` on Python 3.11 and `0.23750000000000002` on Python 3.12. This report also has differing query fingerprints, so the aggregate examples alone are not a complete diagnosis.

To distinguish runtime effects from the embedded changes, the unchanged previous Core commit `93cb7f6a6daae30333008600f3556e6af4f99b3d` was independently rerun under the same Python 3.11 build. Its [historical raw report](data/embedded-core-0.18.4-frozen-311-historical.json) has the same 16 unapproved run-level differences. The [same-runtime comparison](data/embedded-core-0.19.5-frozen-311-paired.json) checks all 22 run signatures, metrics and use signatures and finds **no change** between old and new Core. This additional comparison does not approve the Python 3.11 differences against the original gold or replace the original strict check.

CI runs the original strict frozen gate on Python 3.12 and 3.13. On Python 3.11 it preserves the raw frozen failure and requires exact equality with the digest-pinned historical Python 3.11 report. All three versions still run the Bench tests and three-backend comparison. No tolerance or new golden expectation is substituted for the original frozen baseline.

## Limits

The three-backend comparison covers four representative workloads rather than every Bench dataset. SQLite reopenings occur inside one Bench process, while Core separately tests fresh-process reopening. These findings do not establish parity on every workload, filesystem or hardware configuration. At the time of these recorded runs the Bench workflow and documentation were uncommitted, and hosted CI had not run for those changes.
