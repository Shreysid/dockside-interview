import { createTurnDetector } from "./turn-detection.mjs";

const chooser = document.querySelector("#problem");
const code = document.querySelector("#code");
const response = document.querySelector("#response");
const messages = document.querySelector("#messages");
const status = document.querySelector("#status");
const send = document.querySelector("#send");
const check = document.querySelector("#check");
const finish = document.querySelector("#finish");
const retry = document.querySelector("#retry");
const handsFree = document.querySelector("#hands-free");
const record = document.querySelector("#record");
const spokenReplies = document.querySelector("#spoken-replies");
const voice = document.querySelector("#voice");
const previewVoice = document.querySelector("#preview-voice");
const problemTitle = document.querySelector("#problem-title");
const sessions = new Map();
const encoder = new TextEncoder();
const decoder = new TextDecoder();
const historyTextBytes = 400;
const historyMessageLimit = 6;
const recordingTypes = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"];
const recordingType = recordingTypes.find((type) => window.MediaRecorder?.isTypeSupported(type));
const canRecord = recordingType && navigator.mediaDevices?.getUserMedia;

let problem;
let session;
let pending = false;
let previewing = false;
let capture = null;
let listening = false;
let playbackContext;

async function request(path, options) {
  const result = await fetch(path, options);
  const data = await result.json().catch(() => null);
  if (!result.ok || !data) {
    throw new Error(data?.error ?? "The local server could not complete the request.");
  }
  return data;
}

function updateControls() {
  const busy = pending || previewing;
  chooser.disabled = busy || Boolean(capture) || !problem;
  code.disabled = !problem;
  code.readOnly = pending || Boolean(session?.finished);
  response.disabled = !problem;
  response.readOnly = code.readOnly;
  spokenReplies.disabled = voice.disabled = busy || !window.AudioContext;
  previewVoice.disabled = voice.disabled || listening || Boolean(capture);
  check.disabled = finish.disabled = !problem || code.readOnly || previewing || Boolean(capture);
  send.disabled = check.disabled || !response.value.trim();
  handsFree.disabled = !listening && (!canRecord || !window.AudioContext || !problem || code.readOnly || previewing || Boolean(capture));
  handsFree.textContent = listening ? "Pause mic" : "Hands-free";
  handsFree.setAttribute("aria-pressed", String(listening));
  record.disabled = !canRecord || !problem || code.readOnly || previewing || Boolean(capture && !capture.stop);
  record.textContent = capture?.stop
    ? (capture.automatic ? "Send recording" : "Stop recording")
    : "Record response";
}

async function enablePlayback() {
  playbackContext ??= new AudioContext();
  await playbackContext.resume();
}

async function playSpeech(text, preview = false) {
  const context = playbackContext;
  if (context?.state !== "running") throw new Error("Audio is unavailable.");
  status.textContent = preview ? "Preparing voice preview…" : "Preparing spoken reply…";
  const result = await fetch("/api/speech", {
    method: "POST",
    headers: { "Content-Type": "text/plain;charset=UTF-8", "X-Dockside-Voice": voice.value },
    body: text,
    signal: AbortSignal.timeout(30000),
  });
  if (!result.ok) throw new Error("Speech synthesis failed.");
  const audio = await context.decodeAudioData(await result.arrayBuffer());
  const source = context.createBufferSource();
  source.buffer = audio;
  source.connect(context.destination);
  status.textContent = preview ? "Playing voice preview…" : "Interviewer is speaking…";
  try {
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        source.stop();
        reject(new Error("Playback timed out."));
      }, (audio.duration + 5) * 1000);
      source.onended = () => {
        clearTimeout(timer);
        resolve();
      };
      try {
        source.start();
      } catch (error) {
        clearTimeout(timer);
        reject(error);
      }
    });
  } finally {
    source.disconnect();
  }
}

function pauseMic() {
  listening = false;
  if (capture?.automatic) capture.abort.abort();
  if (!pending) status.textContent = "Microphone paused.";
  updateControls();
}

async function recordResponse(automatic = false) {
  if (!canRecord || !session || pending || previewing || session.finished || capture) return;

  const current = { automatic, stop: null, abort: new AbortController(), detector: null };
  capture = current;
  let stream;
  let audioContext;
  let timer;
  let recorder;
  let discard = false;
  let autoSend = false;
  const closeMic = () => {
    clearTimeout(timer);
    clearInterval(timer);
    stream?.getTracks().forEach((track) => track.stop());
    if (audioContext && audioContext.state !== "closed") {
      void audioContext.close();
    }
  };
  const { signal } = current.abort;
  signal.addEventListener("abort", () => {
    if (recorder && recorder.state !== "inactive") recorder.stop();
    closeMic();
  }, { once: true });
  status.textContent = "Opening microphone…";
  updateControls();
  try {
    if (automatic) audioContext = new AudioContext();
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (signal.aborted) return;
    let analyser;
    let samples;
    if (automatic) {
      await audioContext.resume();
      if (signal.aborted) return;
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 1024;
      audioContext.createMediaStreamSource(stream).connect(analyser);
      samples = new Float32Array(analyser.fftSize);
    }

    recorder = new MediaRecorder(stream, { mimeType: recordingType, audioBitsPerSecond: 48000 });
    const chunks = [];
    const recording = new Promise((resolve, reject) => {
      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size) chunks.push(event.data);
      });
      recorder.addEventListener("stop", () => resolve(new Blob(chunks, { type: recorder.mimeType })), { once: true });
      recorder.addEventListener("error", () => reject(new Error("Microphone recording failed.")), { once: true });
      recorder.start();
    });
    current.stop = (shouldDiscard = false) => {
      discard = shouldDiscard;
      current.stop = null;
      if (recorder.state !== "inactive") recorder.stop();
      closeMic();
      if (!discard) status.textContent = "Transcribing recording…";
      updateControls();
    };
    if (automatic) {
      current.detector = createTurnDetector(performance.now());
      timer = setInterval(() => {
        analyser.getFloatTimeDomainData(samples);
        let energy = 0;
        for (const sample of samples) energy += sample * sample;
        const decision = current.detector.sample(performance.now(), Math.sqrt(energy / samples.length));
        if (decision === "send" || decision === "discard") current.stop(decision === "discard");
        if (decision === "speaking") status.textContent = "Speech detected…";
      }, 40);
    } else {
      timer = setTimeout(current.stop, 25000);
    }
    status.textContent = automatic ? "Listening…" : "Recording…";
    updateControls();

    const blob = await recording;
    closeMic();
    current.stop = null;
    if (signal.aborted || discard) return;
    if (!blob.size) {
      status.textContent = "No audio was captured.";
      return;
    }
    status.textContent = "Transcribing recording…";
    updateControls();
    const { transcript } = await request("/api/transcribe", { method: "POST", body: blob, signal });
    if (signal.aborted) return;
    if (transcript?.trim()) {
      session.response = response.value = [response.value.trimEnd(), transcript.trim()].filter(Boolean).join("\n");
      autoSend = automatic;
      status.textContent = "Review the transcript, then send your response.";
    } else {
      status.textContent = "No speech was detected.";
    }
  } catch (error) {
    if (!signal.aborted) {
      if (automatic) listening = false;
      status.textContent = error.name === "NotAllowedError"
        ? "Microphone permission was denied. You can still type a response."
        : error.message;
    }
  } finally {
    closeMic();
    capture = null;
    if (autoSend && listening && !await submit("reply")) listening = false;
    updateControls();
    if (automatic && listening) void recordResponse(true);
  }
}

function addMessage(entry) {
  const item = document.createElement("article");
  item.className = "message " + entry.role;
  const label = document.createElement("strong");
  label.textContent = entry.label;
  const content = document.createElement("p");
  content.textContent = entry.text;
  item.append(label, content);
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
}

function openProblem(selected) {
  problem = selected;
  if (!sessions.has(problem.id)) {
    sessions.set(problem.id, {
      code: problem.starter_code,
      response: "",
      finished: false,
      messages: [{
        role: "interviewer",
        label: "Interviewer",
        text: "How would you approach this problem?",
      }],
    });
  }
  session = sessions.get(problem.id);
  problemTitle.textContent = problem.title;
  for (const field of ["prompt", "constraints", "example"]) {
    document.getElementById(field).textContent = problem[field];
  }
  code.value = session.code;
  response.value = session.response;
  messages.replaceChildren();
  session.messages.forEach(addMessage);
  status.textContent = session.finished ? "Interview complete." : "";
  updateControls();
}

async function loadProblems() {
  retry.hidden = true;
  problemTitle.textContent = "Loading problems…";
  status.textContent = "";
  try {
    const { problems } = await request("/api/problems");
    if (!Array.isArray(problems) || !problems.length) {
      throw new Error("No problems are available.");
    }
    chooser.replaceChildren(...problems.map((entry) => new Option(entry.title, entry.id)));
    chooser.onchange = () => openProblem(problems.find((entry) => entry.id === chooser.value));
    openProblem(problems[0]);
  } catch (error) {
    problemTitle.textContent = "Could not load problems";
    status.textContent = error.message;
    retry.hidden = false;
  }
}

async function submit(intent) {
  if (!session || pending || previewing || session.finished || capture) return;

  const text = response.value.trim();
  if (intent === "reply" && !text) return;
  const snapshot = code.value;
  if (encoder.encode(snapshot).length > 6000 || encoder.encode(text).length > 1500) {
    status.textContent = "Use up to 6,000 UTF-8 bytes of code and 1,500 bytes of response.";
    return;
  }

  pending = true;
  status.textContent = intent === "finish" ? "Preparing feedback…" : "Interviewer is thinking…";
  updateControls();
  try {
    const buffer = new Uint8Array(historyTextBytes);
    const history = session.messages.slice(-historyMessageLimit).map(({ role, text }) => {
      const { written } = encoder.encodeInto(text, buffer);
      return { role, text: decoder.decode(buffer.subarray(0, written)) };
    });
    const { reply } = await request("/api/interview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_id: problem.id, intent, code: snapshot, text, history }),
    });
    const candidate = {
      role: "candidate",
      label: "You",
      text: text || (intent === "check" ? "Check my code." : "Finish the interview."),
    };
    const interviewer = {
      role: "interviewer",
      label: intent === "finish" ? "Feedback" : "Interviewer",
      text: reply,
    };
    session.messages.push(candidate, interviewer);
    addMessage(candidate);
    addMessage(interviewer);
    session.response = response.value = "";
    session.finished = intent === "finish";
    const completion = session.finished ? "Interview complete." : "";
    status.textContent = completion;
    if (spokenReplies.checked) {
      try {
        await playSpeech(reply);
        status.textContent = completion;
      } catch {
        status.textContent = [completion, "Audio unavailable. The reply is in the conversation."].filter(Boolean).join(" ");
      }
    }
    return true;
  } catch (error) {
    status.textContent = error.message;
  } finally {
    pending = false;
    updateControls();
  }
}

function noteTyping() {
  capture?.detector?.typing(performance.now());
}

code.addEventListener("input", () => {
  session.code = code.value;
  noteTyping();
});
response.addEventListener("input", () => {
  session.response = response.value;
  noteTyping();
  updateControls();
});
document.querySelector("#composer").addEventListener("submit", (event) => {
  event.preventDefault();
  submit("reply");
});
check.addEventListener("click", () => submit("check"));
finish.addEventListener("click", () => submit("finish"));
retry.addEventListener("click", loadProblems);
spokenReplies.addEventListener("change", async () => {
  if (!spokenReplies.checked) return;
  try {
    await enablePlayback();
  } catch {
    spokenReplies.checked = false;
    status.textContent = "Audio unavailable. You can continue with text.";
  }
});
previewVoice.addEventListener("click", async () => {
  if (pending || previewing || listening || capture) return;
  previewing = true;
  updateControls();
  try {
    await enablePlayback();
    await playSpeech("Let's walk through your approach. What would you try first?", true);
    status.textContent = session?.finished ? "Interview complete." : "";
  } catch {
    status.textContent = "Voice preview unavailable.";
  } finally {
    previewing = false;
    updateControls();
  }
});
record.addEventListener("click", () => {
  if (capture?.stop) capture.stop();
  else void recordResponse();
});
handsFree.addEventListener("click", () => {
  if (previewing) return;
  if (listening) {
    pauseMic();
    return;
  }
  listening = true;
  void recordResponse(true);
});
window.addEventListener("pagehide", () => {
  listening = false;
  capture?.abort.abort();
  if (playbackContext) {
    void playbackContext.close();
    playbackContext = undefined;
    spokenReplies.checked = false;
  }
});
loadProblems();
