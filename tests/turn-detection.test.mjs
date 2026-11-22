import assert from "node:assert/strict";
import test from "node:test";
import { createTurnDetector } from "../dockside/static/turn-detection.mjs";

test("idle windows and short noise do not trigger an upload", () => {
  const turn = createTurnDetector(0);
  assert.equal(turn.sample(100, 0.1), "listening");
  assert.equal(turn.sample(200, 0), "listening");
  assert.equal(turn.sample(2000, 0), "listening");
  assert.equal(turn.sample(25000, 0), "discard");
});

test("sustained speech triggers a turn after 1.8 seconds of quiet", () => {
  const turn = createTurnDetector(0);
  assert.equal(turn.sample(100, 0.1), "listening");
  assert.equal(turn.sample(340, 0.1), "speaking");
  assert.equal(turn.sample(2139, 0), "speaking");
  assert.equal(turn.sample(2140, 0), "send");
});

test("typing and resumed speech postpone the quiet deadline", () => {
  const turn = createTurnDetector(0);
  turn.sample(100, 0.1);
  turn.sample(340, 0.1);
  turn.typing(2000);
  assert.equal(turn.sample(2140, 0), "speaking");
  turn.sample(3700, 0.1);
  assert.equal(turn.sample(5499, 0), "speaking");
  assert.equal(turn.sample(5500, 0), "send");
});

test("typing cannot extend a turn past the capture cap", () => {
  const turn = createTurnDetector(0);
  turn.sample(24400, 0.1);
  turn.sample(24640, 0.1);
  turn.typing(24995);
  assert.equal(turn.sample(25000, 0.1), "send");
});
