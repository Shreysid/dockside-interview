"use strict";

const chooser = document.querySelector("#problem");
const code = document.querySelector("#code");
const response = document.querySelector("#response");
const messages = document.querySelector("#messages");
const status = document.querySelector("#status");
const send = document.querySelector("#send");
const check = document.querySelector("#check");
const finish = document.querySelector("#finish");
const retry = document.querySelector("#retry");
const record = document.querySelector("#record");
const problemTitle = document.querySelector("#problem-title");
const sessions = new Map();
const encoder = new TextEncoder();
const recordingTypes = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"];
const recordingType = recordingTypes.find((type) => window.MediaRecorder?.isTypeSupported(type));
const canRecord = recordingType && navigator.mediaDevices?.getUserMedia;

let problem;
let session;
let pending = false;
let capture = null;

async function request(path, options) {
  const result = await fetch(path, options);
  const data = await result.json().catch(() => null);
  if (!result.ok || !data) {
    throw new Error(data?.error ?? "The local server could not complete the request.");
  }
  return data;
}

function updateControls() {
  chooser.disabled = pending || Boolean(capture) || !problem;
  code.disabled = !problem;
  code.readOnly = pending || Boolean(session?.finished);
  response.disabled = !problem;
  response.readOnly = code.readOnly;
  check.disabled = finish.disabled = !problem || code.readOnly || Boolean(capture);
  send.disabled = check.disabled || !response.value.trim();
  record.disabled = !canRecord || !problem || code.readOnly || Boolean(capture && !capture.stop);
  record.textContent = capture?.stop ? "Stop recording" : "Record response";
}

async function recordResponse() {
  if (capture?.stop) {
    capture.stop();
    return;
  }
  if (!canRecord || !session || pending || session.finished || capture) return;

  const current = { stop: null, abort: new AbortController() };
  capture = current;
  let stream;
  let timer;
  const closeMic = () => {
    clearTimeout(timer);
    stream?.getTracks().forEach((track) => track.stop());
  };
  const { signal } = current.abort;
  signal.addEventListener("abort", closeMic, { once: true });
  status.textContent = "Waiting for microphone permission…";
  updateControls();
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (signal.aborted) return;
    const recorder = new MediaRecorder(stream, { mimeType: recordingType, audioBitsPerSecond: 48000 });
    const chunks = [];
    const recording = new Promise((resolve, reject) => {
      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size) chunks.push(event.data);
      });
      recorder.addEventListener("stop", () => resolve(new Blob(chunks, { type: recorder.mimeType })), { once: true });
      recorder.addEventListener("error", () => reject(new Error("Microphone recording failed.")), { once: true });
      recorder.start();
    });
    current.stop = () => {
      current.stop = null;
      if (recorder.state !== "inactive") recorder.stop();
      closeMic();
      status.textContent = "Transcribing recording…";
      updateControls();
    };
    timer = setTimeout(current.stop, 25000);
    status.textContent = "Recording…";
    updateControls();

    const blob = await recording;
    closeMic();
    current.stop = null;
    if (signal.aborted) return;
    if (!blob.size) {
      status.textContent = "No audio was captured.";
      return;
    }
    status.textContent = "Transcribing recording…";
    updateControls();
    const { transcript } = await request("/api/transcribe", { method: "POST", body: blob, signal });
    if (transcript?.trim()) {
      session.response = response.value = [response.value.trimEnd(), transcript.trim()].filter(Boolean).join("\n");
      status.textContent = "Review the transcript, then send your response.";
    } else {
      status.textContent = "No speech was detected.";
    }
  } catch (error) {
    if (!signal.aborted) {
      status.textContent = error.name === "NotAllowedError"
        ? "Microphone permission was denied. You can still type a response."
        : error.message;
    }
  } finally {
    closeMic();
    capture = null;
    updateControls();
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
  if (!session || pending || session.finished || capture) return;

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
    const { reply } = await request("/api/interview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_id: problem.id, intent, code: snapshot, text }),
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
    status.textContent = session.finished ? "Interview complete." : "";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    pending = false;
    updateControls();
  }
}

code.addEventListener("input", () => { session.code = code.value; });
response.addEventListener("input", () => {
  session.response = response.value;
  updateControls();
});
document.querySelector("#composer").addEventListener("submit", (event) => {
  event.preventDefault();
  submit("reply");
});
check.addEventListener("click", () => submit("check"));
finish.addEventListener("click", () => submit("finish"));
retry.addEventListener("click", loadProblems);
record.addEventListener("click", recordResponse);
window.addEventListener("pagehide", () => capture?.abort.abort());
loadProblems();
