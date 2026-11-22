# Handoff

Run `uv sync --locked` to set up the environment, `uv run --locked python -m dockside.server` to start the service, and `uv run --locked python -m unittest discover -v` to run the suite. Use `http://127.0.0.1:8765` as the browser origin.

The workspace can fetch `/api/problems` for problem IDs, prompts, constraints, examples, and starter code. Keep GET and HEAD read-only and retain the exact Origin requirement for future POST routes. Set route-specific body limits and engine deadlines before accepting interview submissions. Local engine behavior still needs verification.
