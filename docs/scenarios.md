# Scenarios

## Mini dataset

A small golden fixture (15 events, 12 queries) proving benchmark correctness. Exercises direct recall, episodic recall, associative recall, temporal recall, knowledge update, future-data isolation, forgetting, working memory, learning, and metamemory.

## Project Atlas (`software_project_v1`)

Fictional software project evolving over ~60 simulated days (61 events, 24 queries, 3 feedback records). The story covers FastAPI, Redis→PostgreSQL advisory locks, auth, caching, CI/CD, incidents, and deliberate obsolete detail. Distinct distractor events replace template filler; named story queries are tagged `core` for subset reporting.

Validate and run:

```bash
uv run cogkura-bench validate-dataset software_project_v1
uv run cogkura-bench run --dataset software_project_v1 --backend oracle --quiet
```

## Project Helios (`helios_v1`)

Fictional billing platform team over ~180 simulated days (550 events, 49 queries, 3 feedback records). Stresses paraphrase queries, current-state vs historical recall, interference from hundreds of distinct distractors, and bounded working-memory selection. Story slots include DynamoDB→PostgreSQL ledger migration, Auth0→WorkOS, polling→Debezium outbox, on-call routing, cost-cap reversal, undecided multi-region, and a post-cutoff SOC2 vendor leak. Named plot queries are tagged `core`. Core paraphrase queries may carry optional structured cues (`entity_ids`, `predicate`, `object_value`) and working-memory `goal` strings authored in the dataset—not invented by the adapter.

Validate and run:

```bash
uv run cogkura-bench validate-dataset helios_v1
uv run cogkura-bench run --dataset helios_v1 --backend oracle --quiet
uv run cogkura-bench compare cogkura token-overlap --dataset helios_v1
```
