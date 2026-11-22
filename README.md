# Dockside Interview

Dockside is a local coding interview practice workspace. Choose a problem, write Python in the editor, and discuss your approach with a local Ollama interviewer. **Check code** requests a review of your current draft. **Finish interview** requests final feedback and closes that problem's session. Dockside sends your code as text for review and never executes it.

## Run locally

Install uv and Ollama. Start Ollama locally with the `qwen3:4b` model available.

```sh
ollama pull qwen3:4b
uv sync --locked
uv run --locked python -m dockside.server
```

Open `http://127.0.0.1:8765` in Chrome. Drafts and replies are held in the current page. Switching problems preserves each session until you reload.

To dictate a response, install ffmpeg and whisper-cli and place the Whisper base.en model at `models/ggml-base.en.bin`. Select **Record response** and grant Chrome microphone access. Select **Stop recording** when done. Recording stops automatically after 25 seconds. Dockside appends the transcript to your response draft, where you can edit it before sending.

## Verify

```sh
uv run --locked python -m unittest discover -v
node --check dockside/static/workspace.js
```

With the server and Ollama running, choose a problem and edit its starter code. Switch away and back to check that the draft survives. Type an approach and select **Send response**. Confirm the interviewer replies, then select **Check code** and confirm another reply arrives. Select **Finish interview** and confirm feedback appears and the controls close the session. At narrow window widths, the panels stack and long examples wrap.

For a microphone smoke test, start with a typed draft, select **Record response**, and say a short sentence. Stop the recording and verify that Chrome releases the microphone and the transcript follows the typed draft. Edit the code and send the response. Confirm that the candidate message includes the transcript and that the interviewer replies. Deny microphone permission and verify that typed responses still work.
