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
const problemTitle = document.querySelector("#problem-title");
const sessions = new Map();
const encoder = new TextEncoder();

let problem;
let session;
let pending = false;

async function request(path, options) {
  const result = await fetch(path, options);
  const data = await result.json().catch(() => null);
  if (!result.ok || !data) {
    throw new Error(data?.error ?? "The local server could not complete the request.");
  }
  return data;
}

function updateControls() {
  chooser.disabled = pending || !problem;
  code.disabled = !problem;
  code.readOnly = pending || Boolean(session?.finished);
  response.disabled = !problem;
  response.readOnly = code.readOnly;
  check.disabled = finish.disabled = !problem || code.readOnly;
  send.disabled = check.disabled || !response.value.trim();
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
  if (!session || pending || session.finished) return;

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
loadProblems();
