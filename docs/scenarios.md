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
