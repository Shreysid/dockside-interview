# Dockside Interview

Dockside is a local coding interview practice workspace. Choose a problem, write Python in the editor, and discuss your approach with a local Ollama interviewer. **Check code** requests a review of your current draft. **Finish interview** requests final feedback and closes that problem's session. Dockside sends your code as text for review and never executes it.

## Run locally

On macOS with Homebrew and Chrome installed, install the command-line dependencies.

```sh
brew install uv ollama ffmpeg whisper.cpp
```

Start Ollama in a separate Terminal window and leave it running. If Ollama is already serving locally, use that instance.

```sh
ollama serve
```

From the Dockside repository root, download the models and set up the locked Python environment. The project selects Python 3.12 for the ONNX runtime.

```sh
ollama pull qwen3:4b
mkdir -p models
curl -fL --retry 3 -o models/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
curl -fL --retry 3 -o models/kokoro-v1.0.int8.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.int8.onnx
curl -fL --retry 3 -o models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin
uv sync --locked
uv run --locked python -m dockside.server
```

After setup, you can start Dockside offline with Ollama still running locally and all model files in place.

```sh
uv run --locked --offline python -m dockside.server
```

Open `http://127.0.0.1:8765` in Chrome. Drafts and replies are held in the current page. Switching problems preserves each session until you reload. Each turn sends the current code and up to six recent messages from the selected problem to Ollama. The interviewer can offer a hint, and gives one when asked.

To dictate a response, select **Record response** and grant Chrome microphone access. Select **Stop recording** when done. Dockside appends the English transcript to your response draft, where you can edit it before sending. Each browser recording is capped at 25 seconds. The transcription endpoint accepts WebM, MP4, or Ogg audio with a 2 MiB upload limit and a 30-second decoded duration limit.

Hold **Push to talk (hold)** with a pointer, Space, or Enter. Release to transcribe and send the response with the current code snapshot. Drag off the button or press Escape to cancel. Once the microphone opens, hold for at least a quarter second. If Chrome asks for permission, grant access and hold again. Capture stops after 25 seconds and sends when you release. Pause **Hands-free** before using push-to-talk. You can keep editing code while the interviewer is thinking or speaking.

Select **Hands-free** to send spoken responses automatically. The microphone listens for sustained speech followed by 1.8 seconds of quiet. Typing in either editor postpones the quiet deadline. Select **Send recording** to end the recording manually. Select **Pause mic** to discard the current recording and use typed send, check, or finish. Hands-free listening resumes after the interviewer replies.

Enable **Speak interviewer replies** to hear replies and final feedback through Chrome. Choose **Heart** (default), **Bella**, or **Michael** from the **Voice** menu. Dockside uses local Kokoro-82M at 0.96× speed. Select **Preview voice** to hear a sample with spoken replies on or off. Stop manual recording or pause hands-free mode before previewing. With spoken replies enabled, hands-free capture stays closed through synthesis and playback. Replies and feedback also appear in the conversation, including when audio is unavailable.

On one Apple M1 run with the locked environment already installed, the HTTP server started in 0.04 s and Whisper transcribed a short synthetic clip in 0.47 s. The first Ollama reply took 14.05 s with the model initially unloaded, and the first Kokoro request took 2.30 s including initialization. The following finish request took 2.04 s in Ollama and 0.60 s in Kokoro. These were local HTTP timings. Playback added 5.21 s for the reply and 3.35 s for the feedback, and hands-free mode also waits for its 1.8-second quiet interval before submitting.

## Verify

```sh
uv run --locked python -m unittest discover -v
node --input-type=module --check < dockside/static/workspace.js
node --test tests/turn-detection.test.mjs
```

With the server and Ollama running, choose a problem and edit its starter code. Switch away and back to check that the draft survives. Type an approach and select **Send response**. Confirm the interviewer replies. Refer back to a detail from your first response in a follow-up, then select **Check code** and confirm another reply arrives. Select **Finish interview** and confirm feedback appears and the controls close the session. At narrow window widths, the panels stack and long examples wrap.

For a microphone smoke test, start with a typed draft, select **Record response**, and say a short sentence. Stop the recording and verify that Chrome releases the microphone and the transcript follows the typed draft. Edit the code and send the response. Confirm that the candidate message includes the transcript and that the interviewer replies. Deny microphone permission and verify that typed responses still work.

For a push-to-talk smoke test, hold with the pointer, speak, and release. Verify that the microphone closes and the response sends automatically. Repeat with Space or Enter. Try a quick tap, dragging off the button, and releasing while Chrome is still asking for permission. None of those attempts should send a response. Edit the code while a reply is pending and verify that your edit remains in the editor.

For a hands-free smoke test, enable **Hands-free** and stay quiet for 25 seconds. The conversation should remain unchanged. Speak a response, type in the code editor, and stop typing. After the quiet interval, confirm that Chrome releases the microphone, the transcript appears as a sent response, and listening resumes after the interviewer replies. Enable **Speak interviewer replies** and repeat a spoken turn. Confirm that Chrome keeps the microphone closed while the interviewer is speaking and resumes listening when playback ends. Select **Pause mic** and confirm that Chrome releases the microphone again.

For a speech smoke test, enable **Speak interviewer replies**, send a response, and verify that the interviewer is audible. Finish the interview and verify that the feedback appears and plays. The first request also initializes the model.
