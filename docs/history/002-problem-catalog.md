# 002 Problem catalog

## Summary

The loopback service publishes three original interview problems at `GET /api/problems`.

## Motivation

The candidate workspace and interviewer need a shared source for problem IDs and specifications.

## Design

Each catalog entry includes an ID, title, prompt, constraints, worked input and output, and Python starter code. The problems cover interval overlap, shortest paths, and contiguous ranges.

## Implementation

The route supports GET and HEAD and inherits the service's Host and Origin checks. Set up and verify the project with uv:

```sh
uv sync --locked
uv run --locked python -m unittest discover -v
uv run --locked python -m dockside.server
```

Open `http://127.0.0.1:8765/api/problems` to inspect the catalog.

## Files Changed

- `dockside/problems.py` defines the prompts.
- `dockside/server.py` serves the catalog.
- `tests/test_server.py` covers the response and access checks.
- `pyproject.toml` and `uv.lock` define a dependency-free Python 3.11+ environment.

## Tradeoffs

The small catalog ships with the application and changes with the source.

## Future Work

Load the catalog in the candidate workspace and resolve the selected problem ID when creating interview sessions.
