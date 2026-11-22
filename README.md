# Dockside Interview

Dockside is a local coding interview practice workspace. Choose a problem, write Python in the editor, and discuss your approach with a local Ollama interviewer. **Check code** requests a review of your current draft. **Finish interview** requests final feedback and closes that problem's session. Dockside sends your code as text for review and never executes it.

## Run locally

Install uv and Ollama. The project selects Python 3.12 for the locked ONNX runtime. Start Ollama locally with the `qwen3:4b` model available.

```sh
ollama pull qwen3:4b
uv sync --locked
uv run --locked python -m dockside.server
```

Open `http://127.0.0.1:8765` in Chrome. Drafts and replies are held in the current page. Switching problems preserves each session until you reload. Each turn sends the current code and up to six recent messages from the selected problem to Ollama. The interviewer can offer a hint, and gives one when asked.

To dictate a response, install ffmpeg and whisper-cli and place the Whisper base.en model at `models/ggml-base.en.bin`. Select **Record response** and grant Chrome microphone access. Select **Stop recording** when done. Recording stops automatically after 25 seconds. Dockside appends the transcript to your response draft, where you can edit it before sending.

Select **Hands-free** to send spoken responses automatically. The microphone listens for sustained speech followed by 1.8 seconds of quiet. Typing in either editor postpones the quiet deadline. Select **Send recording** to end the recording manually. Select **Pause mic** to discard the current recording and use typed send, check, or finish. Hands-free listening resumes after the interviewer replies.

Enable **Speak interviewer replies** to hear replies and final feedback through Chrome. Choose **Heart** (default), **Bella**, or **Michael** from the **Voice** menu. Dockside uses local Kokoro-82M at 0.96× speed. Select **Preview voice** to hear a sample with spoken replies on or off. Stop manual recording or pause hands-free mode before previewing. Place `kokoro-v1.0.int8.onnx` and `voices-v1.0.bin` in `models/`. The server loads them on the first speech request. [Official model files](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1). With spoken replies enabled, hands-free capture stays closed through synthesis and playback. Replies and feedback also appear in the conversation, including when audio is unavailable.

## Verify

```sh
uv run --locked python -m unittest discover -v
node --input-type=module --check < dockside/static/workspace.js
node --test tests/turn-detection.test.mjs
```

With the server and Ollama running, choose a problem and edit its starter code. Switch away and back to check that the draft survives. Type an approach and select **Send response**. Confirm the interviewer replies. Refer back to a detail from your first response in a follow-up, then select **Check code** and confirm another reply arrives. Select **Finish interview** and confirm feedback appears and the controls close the session. At narrow window widths, the panels stack and long examples wrap.

For a microphone smoke test, start with a typed draft, select **Record response**, and say a short sentence. Stop the recording and verify that Chrome releases the microphone and the transcript follows the typed draft. Edit the code and send the response. Confirm that the candidate message includes the transcript and that the interviewer replies. Deny microphone permission and verify that typed responses still work.

For a hands-free smoke test, enable **Hands-free** and stay quiet for 25 seconds. The conversation should remain unchanged. Speak a response, type in the code editor, and stop typing. After the quiet interval, confirm that Chrome releases the microphone, the transcript appears as a sent response, and listening resumes after the interviewer replies. Enable **Speak interviewer replies** and repeat a spoken turn. Confirm that Chrome keeps the microphone closed while the interviewer is speaking and resumes listening when playback ends. Select **Pause mic** and confirm that Chrome releases the microphone again.

For a speech smoke test, enable **Speak interviewer replies**, send a response, and verify that the interviewer is audible. Finish the interview and verify that the feedback appears and plays. The first request also initializes the model.
