# Push-to-talk

## Summary

Hold a pointer, Space, or Enter to record and release to send the transcript. Toggle dictation remains available for editing the transcript before sending.

## Motivation

Candidates can give a spoken response with one gesture and continue editing their code while the interviewer responds.

## Design

Push-to-talk shares the existing MediaRecorder and transcription flow. A hold and its capture belong to the same input. Dragging off the button, losing pointer capture, pressing Escape, or losing keyboard focus cancels it. Manual recording, hands-free capture, and preview are mutually exclusive with push-to-talk.

## Implementation

Release stops the microphone before transcription, and submission uses the code snapshot taken when the transcript is ready. Holds under 250 ms of recording are discarded. At 25 seconds, the microphone closes and the captured audio waits for release. If permission is still pending when the user releases, a stream arriving later is immediately closed.

## Files Changed

- `dockside/static/index.html`, `workspace.css`, and `workspace.js` add the control and connect it to capture and submission.
- `README.md`, `.ai/STATUS.md`, and `.ai/HANDOFF.md` record operation and verification.

## Tradeoffs

While a browser permission request is unresolved, the app keeps competing capture and preview controls unavailable. Chrome owns dismissal of that prompt.

## Future Work

Verify the physical microphone and native permission prompt. Headless Chrome used real browser recording with synthetic audio, simulated permission outcomes, and stubbed transcription and interviewer replies.
