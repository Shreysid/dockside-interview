# Project status

Dockside serves a responsive typed interview workspace at the loopback origin. It loads a three-problem catalog, holds a separate draft and transcript for each problem while the page is open, submits the current code with each typed, check, and finish action, and displays final feedback.

The locked uv environment and HTTP tests cover typed turns, the catalog, static assets, and the loopback access policy. The existing transcription and speech routes are callable independently. Browser microphone capture, browser playback, Kokoro synthesis, and bounded model conversation history are pending.
