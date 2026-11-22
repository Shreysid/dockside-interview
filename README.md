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

The browser currently supports typed turns. Microphone capture and spoken replies are separate from the workspace at this stage.

## Verify

```sh
uv run --locked python -m unittest discover -v
node --check dockside/static/workspace.js
```

With the server and Ollama running, choose a problem and edit its starter code. Switch away and back to check that the draft survives. Type an approach and select **Send response**. Confirm the interviewer replies, then select **Check code** and confirm another reply arrives. Select **Finish interview** and confirm feedback appears and the controls close the session. At narrow window widths, the panels stack and long examples wrap.
