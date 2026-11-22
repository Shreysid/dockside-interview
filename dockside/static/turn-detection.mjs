const SPEECH_LEVEL = 0.025;
const SPEECH_MS = 240;
const QUIET_MS = 1800;
const MAX_MS = 25000;

export function createTurnDetector(startedAt) {
  let speechStart = null;
  let heardSpeech = false;
  let lastActivity = startedAt;

  return {
    typing(now) {
      lastActivity = now;
    },

    sample(now, level) {
      if (level >= SPEECH_LEVEL) {
        speechStart ??= now;
        heardSpeech ||= now - speechStart >= SPEECH_MS;
        lastActivity = now;
      } else {
        speechStart = null;
      }

      if (now - startedAt >= MAX_MS) return heardSpeech ? "send" : "discard";
      if (heardSpeech && now - lastActivity >= QUIET_MS) return "send";
      return heardSpeech ? "speaking" : "listening";
    },
  };
}
