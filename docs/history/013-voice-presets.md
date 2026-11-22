# Kokoro voice presets and preview

## Summary

Choose Heart, Bella, or Michael for spoken interviewer replies and hear a sample from the voice controls.

## Motivation

A fixed sample lets candidates compare voices before enabling spoken replies or waiting for an interview turn.

## Design

Preview and reply playback share the same local speech endpoint and Web Audio path. The optional `X-Dockside-Voice` request header accepts one allowlisted preset. Requests that omit the header use Heart. All presets use Kokoro at 0.96× speed.

## Implementation

The browser disables preview while recording or hands-free listening is active. A preview blocks new capture and interview submissions until playback settles. The loopback and same-origin checks apply to every synthesis request.

## Files Changed

- `dockside/static/` presents the voice controls and manages playback.
- `dockside/server.py` and `dockside/speech.py` validate preset selection and render the WAV.
- `tests/test_server.py` checks default and explicit presets, invalid and duplicate voice values, and speech failures.
- `README.md` explains how to select and preview a voice.

## Tradeoffs

Preview requires stopping manual recording or pausing hands-free mode first. The first preview in a server session may include model initialization.

## Future Work

Verify physical microphone capture and permission behavior during push-to-talk testing.
