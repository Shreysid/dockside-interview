# Local speech transcription

## Summary

A local transcription function converts short browser recordings into English text using ffmpeg and Whisper base.en.

## Motivation

Push-to-talk and hands-free mode need to feed candidate speech into the same interviewer that handles typed responses.

## Design

Accept WebM, Ogg, and MP4 audio and select the demuxer from the declared media type. Decode from standard input with ffmpeg's protocol allowlist restricted to pipes. Whisper reads the normalized WAV from a private temporary directory that is removed when transcription ends.

## Implementation

Recordings are limited to 2 MiB and 30 seconds of decoded mono audio. Conversion has a 10-second deadline and transcription has a 45-second deadline. Digital silence and standalone non-speech markers produce an empty transcript. Install ffmpeg and whisper-cli on the local machine and place the Whisper base.en model at `models/ggml-base.en.bin`.

## Files Changed

`dockside/transcription.py` implements the local pipeline. `tests/test_transcription.py` exercises input limits, timeouts, silence handling, and temporary file cleanup.

## Tradeoffs

The server rejects recordings that exceed the duration limit. Browser recording controls should stop before that limit to leave room for container padding. Whisper can still misinterpret ambient noise as speech.

## Future Work

Expose transcription through a bounded, same-origin upload endpoint. Add browser voice activity detection and use the transcript with the current canvas snapshot.
