# Local interviewer playback

## Summary

The service renders interviewer replies as mono 22.05 kHz PCM WAV using macOS `say`.

## Motivation

Both voice modes need browser-controlled playback so capture can stay paused until the interviewer finishes speaking.

## Design

POST UTF-8 reply text to `/api/speech` with `Content-Type: text/plain; charset=utf-8`. The request requires the loopback Host and a matching Origin. A successful response contains `audio/wav`. Errors use JSON. The route returns 400 for invalid text, 413 above 4 KiB, 415 for an unsupported content type, and 503 when synthesis fails.

## Implementation

The local engine reads reply text from stdin. Square brackets are removed from the spoken input to prevent embedded speech commands. The engine has a 15-second deadline. The service reads up to 4 MiB of WAV data and cleans up temporary audio on exit.

## Files Changed

- `dockside/speech.py` renders replies.
- `dockside/server.py` exposes the protected route.
- `tests/test_server.py` covers request validation and engine failures.

## Tradeoffs

The browser requests audio separately so it can display the text immediately and keep the interview usable when speech synthesis fails.

## Future Work

Play the WAV in the interview workspace. Keep capture paused through audio playback and release the pause when playback ends or fails.
