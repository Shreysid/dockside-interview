# Hands-free browser capture

## Summary

Chrome can listen for a spoken response and send it after 1.8 seconds of quiet. Hands-free capture starts only when selected.

## Motivation

Candidates can keep coding while speaking and let the workspace send the response at the end of a thought.

## Design

MediaRecorder starts before the analyser detects speech, retaining the start of the utterance within each recording window. The detector requires 240 ms above its energy threshold and resets the quiet deadline on speech or typing in either text area. Each recording lasts up to 25 seconds. Idle windows are discarded locally.

## Implementation

The hands-free control changes to **Pause mic** while enabled. **Send recording** bypasses the quiet deadline. Capture releases its microphone tracks before transcription, then sends recognized speech with the current editor snapshot. The microphone opens again after the interview request returns. Pausing discards in-progress audio and prevents the next capture.

## Files Changed

- Browser workspace and turn detector in `dockside/static/`
- Static asset routing in `dockside/server.py`
- Detector and HTTP asset tests in `tests/`
- Setup and smoke instructions in `README.md`

## Tradeoffs

The fixed energy threshold can respond to sustained background noise. Renewing idle windows bounds recording size and briefly reopens the microphone at each boundary.

## Future Work

Verify thresholds with a physical microphone and extend the microphone pause through spoken playback.
