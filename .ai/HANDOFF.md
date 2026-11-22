# Handoff

Run `uv sync --locked` to set up the environment, `uv run --locked python -m dockside.server` to start the service, and `uv run --locked python -m unittest discover -v` to run the suite. Use `http://127.0.0.1:8765` as the browser origin.

The workspace can fetch `/api/problems` for problem IDs, prompts, constraints, examples, and starter code. Keep GET and HEAD read-only and retain the exact Origin requirement for future POST routes. Set route-specific body limits and engine deadlines before accepting interview submissions. Local engine behavior still needs verification.

Submit typed turns to `POST /api/interview` with same-origin JSON containing `problem_id`, `intent` (`reply`, `check`, or `finish`), `code`, and `text`. Read the `reply` property on success. The route calls local Ollama through curl. Use the same interviewer function after voice transcription. The current prompt uses the submitted snapshot, with conversation history pending.

For the audio upload route, call `dockside.transcription.transcribe(audio, media_type)`. It accepts WebM, Ogg, and fragmented MP4 input up to 2 MiB and 30 seconds, raises `InvalidRecording` for unsupported or malformed recordings and `TranscriberUnavailable` for engine failures, and returns an empty string when no words are detected. Stop browser capture before the server duration limit and skip the interviewer call when the transcript is empty.

For browser integration, POST the recording Blob directly to `/api/transcribe` with its recording media type. Read the response's `transcript` property. For a nonempty transcript, submit it as `text` with the code snapshot to `/api/interview`. See `docs/history/005-recording-upload.md` for response statuses and limits.

For playback, POST the interviewer reply as UTF-8 `text/plain` to `/api/speech` and play the returned WAV Blob. Keep capture paused until playback ends or fails. Show the text reply even when synthesis or playback fails. See `docs/history/006-local-playback.md` for limits and statuses.
