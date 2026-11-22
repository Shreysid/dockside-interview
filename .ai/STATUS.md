# Project status

Dockside serves a responsive typed interview workspace at the loopback origin. It loads a three-problem catalog, holds a separate draft and transcript for each problem while the page is open, submits the current code with each typed, check, and finish action, and displays final feedback.

The locked uv environment and HTTP tests cover typed turns, the catalog, static assets, and the loopback access policy. Chrome can record and transcribe short microphone clips into an editable response draft. Opt-in hands-free capture sends a turn after sustained speech and 1.8 seconds of quiet, or on manual send. Typed, recorded, check, and finish turns use bounded conversation context from the active problem. Chrome can speak interviewer replies and finish feedback using the local speech endpoint. Hands-free capture stays closed through synthesis and playback. Kokoro synthesis is pending. Physical microphone QA is pending.
