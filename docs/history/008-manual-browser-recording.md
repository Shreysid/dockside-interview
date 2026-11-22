# Manual browser recording

## Summary

Users can dictate an interview response in Chrome and review the transcript in the composer before sending.

## Motivation

The transcription endpoint needed a browser workflow that keeps typed drafts intact and lets users correct transcription errors before submitting a turn.

## Design

A button starts microphone capture and stops it on a second press or after 25 seconds. Permission, recording, and transcription have visible statuses. The editor and draft remain editable during capture, while problem switching and interview actions wait until transcription completes.

## Implementation

MediaRecorder negotiates a format accepted by the local API. Dockside releases the microphone before uploading the clip and appends recognized words to the current draft. Sending uses the latest code snapshot.

## Files Changed

- `dockside/static/` contains the recording control, styles, and browser capture flow.
- `README.md` describes microphone setup and the Chrome smoke procedure.
- `.ai/` records the current implementation and remaining work.

## Tradeoffs

Manual dictation adds a review step before sending, which gives users control over recognition errors.

## Future Work

Add opt-in silence detection and spoken replies, and verify capture with a physical microphone.
