# Local Kokoro speech

## Summary

Spoken interviewer turns and finish feedback use Kokoro-82M INT8.

## Motivation

A local, open-source model makes Chrome playback independent of the operating system's speech service.

## Design

The serial HTTP server loads one Kokoro instance on the first speech request and reuses it for subsequent requests. The model and voice files are local. The endpoint returns mono 16-bit PCM WAV at 24 kHz and retains the existing response size limit. A model or inference error returns HTTP 503 so the browser can show the transcript.

## Implementation

Kokoro ONNX 0.6.1 and its runtime dependencies are locked with uv. The project selects Python 3.12. Synthesis uses the English `af_heart` voice.

## Files Changed

- `dockside/speech.py` implements Kokoro synthesis and WAV encoding.
- `pyproject.toml`, `uv.lock`, and `.python-version` define the runtime environment.
- `README.md` documents the model files and playback smoke test.

## Tradeoffs

The first spoken reply includes model initialization time. Keeping a single INT8 session resident lets later turns reuse the loaded model.

## Future Work

Verify physical microphone capture and permission behavior on the host.
