# Handoff

Run `uv sync --locked` to set up the environment, `uv run --locked python -m dockside.server` to start the service, and `uv run --locked python -m unittest discover -v` to run the suite. Open `http://127.0.0.1:8765` in Chrome. The README includes a typed workspace smoke procedure.

The browser assets are in `dockside/static/`. The chooser fetches `GET /api/problems`. The shared submission flow calls `POST /api/interview` with same-origin JSON containing `problem_id`, `intent` (`reply`, `check`, or `finish`), `code`, and `text`, then displays the returned `reply`. The route uses local Ollama (`qwen3:4b`). Browser history lives in per-problem sessions. Model context currently uses the submitted snapshot.

For microphone integration, send the recording Blob directly to `POST /api/transcribe`. The API accepts WebM, Ogg, and fragmented MP4 input up to 2 MiB and 30 seconds. Submit a nonempty `transcript` using the code captured for that turn. See `docs/history/005-recording-upload.md` for response statuses and limits.

For playback, send the interviewer reply as UTF-8 `text/plain` to `POST /api/speech` and play the returned WAV Blob. The current engine uses macOS `say`. Keep capture paused through playback or failure, and keep the reply visible if synthesis or playback fails. See `docs/history/006-local-playback.md` for limits and statuses.
