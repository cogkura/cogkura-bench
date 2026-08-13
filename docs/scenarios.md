# Scenarios

## Mini dataset

A small golden fixture (15 events, 12 queries) proving benchmark correctness. Exercises direct recall, episodic recall, associative recall, temporal recall, knowledge update, future-data isolation, forgetting, working memory, learning, and metamemory.

## Project Atlas (`software_project_v1`)

Fictional software project evolving over ~60 simulated days (250 events, 80 queries, 3 feedback records). Covers all nine capabilities: FastAPI API, Redis→PostgreSQL advisory locks, auth provider choice, caching, CI/CD, observability, bugs, incidents, noise, and deliberate obsolete detail.

Validate and run:

```bash
uv run cogkura-bench validate-dataset software_project_v1
uv run cogkura-bench run --dataset software_project_v1 --backend oracle --quiet
```
