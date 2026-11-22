# Local setup and verification

## Summary

The README gives the full macOS setup sequence and an offline launch command.

## Motivation

Voice features depend on local command-line tools and model files that the Python lockfile cannot install.

## Design

Ollama serves the interviewer model in a separate Terminal. The Python app uses the locked environment, and the speech models live at the paths expected by the transcription and playback endpoints.

## Implementation

Verified that the three public model URLs resolved successfully and that the existing environment synced and launched with uv offline. A fresh local HTTP smoke test submitted a synthetic WebM clip to Whisper, passed its transcript to Ollama, and validated 24 kHz WAV output from Kokoro for both the reply and final feedback.

## Files Changed

- `README.md` lists installation and launch commands, capture limits, and M1 timings.
- `.ai/STATUS.md` and `.ai/HANDOFF.md` record the verified setup and pipeline.

## Tradeoffs

The offline launch depends on a completed online setup. First-turn latency includes loading Ollama and Kokoro models, and the measured times vary with hardware and response length.

## Future Work

Repeat the browser smoke steps with a physical microphone and the native Chrome permission dialog.
