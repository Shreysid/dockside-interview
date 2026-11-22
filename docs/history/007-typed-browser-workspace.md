# Typed browser workspace

## Summary

Dockside serves a responsive dark workspace with a problem chooser, Python editor, typed conversation, code review, and finish feedback.

## Motivation

Candidates need a single browser page to read the prompt, write their solution, and talk through it.

## Design

The loopback HTTP server exposes an explicit list of local assets alongside the existing APIs. The browser keeps each problem's draft and conversation in memory and submits the current source and response with each action.

## Implementation

The workspace loads problem metadata from `GET /api/problems` and sends reply, check, and finish actions to `POST /api/interview`. An in-flight request prevents concurrent submission. Errors keep the candidate's draft available to retry. Successful finish shows the feedback and makes the session read-only.

## Files Changed

- `dockside/server.py` and `dockside/static/` serve and implement the workspace.
- `tests/test_server.py` checks asset delivery and the loopback access policy.
- `README.md` and `.ai/` describe setup, verification, and project state.

## Tradeoffs

The editor uses a native textarea and needs no browser dependencies. Refreshing the page starts fresh sessions. The interviewer receives the current turn while browser history stays on screen.

## Future Work

Add microphone capture and browser playback, then pass bounded recent context to the interviewer.
