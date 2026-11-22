# Recording upload

## Summary

`POST /api/transcribe` accepts a raw browser audio recording and returns JSON containing a `transcript` string.

## Motivation

The browser needs to display transcription progress and decide whether there is speech to send with the canvas snapshot.

## Design

Send the recording as the raw request body with its `audio/webm`, `audio/ogg`, or `audio/mp4` media type. Codec parameters are accepted. The POST requires the exact loopback Host and matching Origin, and a single Content-Length. The upload limit is 2 MiB and the decoded audio limit is 30 seconds.

## Implementation

A successful transcription returns HTTP 200, with an empty transcript when no speech is recognized. Malformed recordings return 400, oversized uploads return 413, unsupported media types return 415, and local engine failures return 503.

## Files Changed

`dockside/server.py` routes recording uploads through the existing local transcription pipeline. `tests/test_server.py` verifies request validation and response handling.

## Tradeoffs

The browser makes a second request when recognized speech should reach the interviewer. This lets it show distinct transcription and thinking states and skip empty turns.

## Future Work

Wire browser recording controls to the upload endpoint and send recognized speech with the current canvas snapshot.
