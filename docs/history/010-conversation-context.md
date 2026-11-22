# Interview conversation context

## Summary

The interviewer receives recent discussion with each current code snapshot.

## Motivation

A follow-up or a request for feedback can refer to the approach the candidate already discussed.

## Design

The browser sends up to six recent messages in chronological order from the selected problem. Each message contains a candidate or interviewer role and up to 400 UTF-8 bytes of text. Existing API callers can omit history.

## Implementation

The browser truncates old message text at a Unicode character boundary and preserves the full transcript on screen. The server validates history before passing it to Ollama as interview material. The prompt asks one focused question on reply or check turns, allows offering a hint, and reserves giving a hint for when the candidate asks. The finish prompt requests empathetic feedback with a concrete next step.

## Files Changed

- Browser turn submission in `dockside/static/workspace.js`
- Turn validation and model prompting in `dockside/interviewer.py`
- HTTP contract coverage in `tests/test_server.py`
- Setup notes in `README.md` and project records in `.ai/`

## Tradeoffs

Long messages contribute their opening text and older exchanges fall out of the window. The current response and editor snapshot retain their existing limits.

## Future Work

Play interviewer replies in the browser and keep hands-free capture paused until playback ends.
