# Typed interview turns

## Summary

The loopback service accepts typed responses, code review requests, and finish requests at `POST /api/interview`, then returns the local interviewer's text.

## Motivation

The browser and voice workflows need a shared way to turn a candidate's explanation and canvas snapshot into an interviewer response.

## Design

Use the existing exact Host and Origin checks and single-request HTTP server. Send the selected problem and candidate material to qwen3:4b on loopback with thinking disabled and a 4,096-token context. Candidate code is passed as text for review and is never executed.

## Implementation

Send JSON with `problem_id`, `intent`, `code`, and `text`. Choose `reply`, `check`, or `finish` for the intent. A reply requires nonempty text. The service returns a JSON object with a `reply` string on success or an `error` string on validation or model failure. The request body is limited to 32 KiB. The model call uses curl with a 60-second subprocess timeout and a 64 KiB response limit. It requires a running local Ollama instance with qwen3:4b installed.

## Files Changed

`dockside/interviewer.py` handles model requests and turn validation. `dockside/server.py` exposes the route. `tests/test_server.py` covers HTTP validation, reply delivery, and unavailable-model handling.

## Tradeoffs

Each request uses the current code and candidate text. Conversation history is outside the current endpoint contract.

## Future Work

Connect the browser and voice controls and include recent interview turns in the model context.
