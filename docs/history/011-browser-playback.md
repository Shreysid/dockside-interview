# Spoken interviewer replies

## Summary

Chrome can read interviewer replies and finish feedback aloud when the candidate enables **Speak interviewer replies**.

## Motivation

Hands-free interviews need spoken feedback without feeding interview audio back through the microphone.

## Design

The checkbox starts a Web Audio context during a user gesture. Each reply appears in the conversation as soon as it arrives. The interview turn stays pending through synthesis and playback, so hands-free capture resumes only after playback ends or fails.

## Implementation

The workspace submits the reply to the local speech endpoint, decodes the WAV, and plays it using the active context. The status indicates when audio is being prepared or played. An audio error leaves the turn and any finish feedback visible.

## Files changed

- `dockside/static/index.html` and `dockside/static/workspace.js` add the playback preference and lifecycle.
- `README.md` describes setup and the manual playback smoke test.

## Tradeoffs

Playback extends the time before the next turn can begin. It is opt-in and uses the existing macOS speech engine.

## Future work

Switch the default speech engine to Kokoro and verify capture and playback with a physical microphone.
