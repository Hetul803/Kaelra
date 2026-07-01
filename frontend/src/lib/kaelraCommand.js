// Kaelra's Entity command router.
//
// Kaelra is one continuous presence: the user just talks and she navigates,
// opens cards, and asks what's next. This router resolves the common
// "operate the app" intents ENTIRELY on the client (no LLM, no premium voice
// spend). Anything that needs real reasoning returns null so the caller can
// hand it to the LLM (/talk).

// Verbs that signal the user wants Kaelra to show / open / go somewhere.
const SHOW_VERBS =
  /\b(show|open|pull\s?up|go to|take me to|bring up|see|view|display|let me see|navigate to|switch to|head to|jump to|check)\b/;

// Targets Kaelra can resolve locally. `cardKind` items can be opened as a card
// on the Home feed; otherwise Kaelra navigates to the page.
const TARGETS = [
  { keys: ["email", "inbox", "mail", "message", "gmail", "outlook"], cardKind: "email", path: "/dashboard", label: "your email" },
  { keys: ["calendar", "schedule", "agenda", "event", "meeting", "appointment"], cardKind: "event", path: "/dashboard", label: "your calendar" },
  { keys: ["news", "headline"], cardKind: "news", path: "/dashboard", label: "the news" },
  { keys: ["file", "document", "doc ", "attachment", "drive"], path: "/files", label: "your files" },
  { keys: ["timeline", "where i", "my places", "location history", "places i"], path: "/timeline", label: "your timeline" },
  { keys: ["job", "career", "recruiter", "internship"], path: "/jobs", label: "jobs and career" },
  { keys: ["memory", "remember", "what you know", "learned", "memories"], path: "/memory", label: "your memory" },
  { keys: ["queue", "approval", "pending", "to approve"], path: "/queue", label: "your action queue" },
  { keys: ["routine"], path: "/routines", label: "your routines" },
  { keys: ["connected account", "connect google", "connect microsoft", "integration", "accounts"], path: "/accounts", label: "connected accounts" },
  { keys: ["device"], path: "/devices", label: "your devices" },
  { keys: ["setting", "privacy"], path: "/settings", label: "settings and privacy" },
  { keys: ["dashboard", "control panel", "overview"], path: "/dashboard", label: "your dashboard" },
  { keys: ["class", "school", "assignment", "course", "study"], path: "/class", label: "class and school" },
  { keys: ["smart home", "home device", "lights", "thermostat"], path: "/home", label: "smart home" },
];

const DONE = /\b(done|that'?s all|that is all|finished|i'?m done|im done|all set|dismiss|close it|close this|go back)\b/;
const NEXT = /\b(what'?s next|what next|what else|anything else|now what)\b/;
const THANKS = /^(thanks|thank you|cheers|nice|great|perfect|awesome)\b/;
const STOP = /\b(stop talking|be quiet|quiet|mute|shush|hush|silence|stop speaking)\b/;
const HOME = /\b(go home|home screen|take me home|main screen)\b/;

const NEXT_PROMPTS = [
  "What would you like to see next?",
  "What should I pull up next?",
  "Anything else you'd like me to show you?",
  "What's next?",
];
let _promptIdx = 0;
function nextPrompt() {
  const p = NEXT_PROMPTS[_promptIdx % NEXT_PROMPTS.length];
  _promptIdx += 1;
  return p;
}

/**
 * Interpret a raw utterance into a local command, or null if it needs the LLM.
 * @returns {null | {kind:'stop'|'prompt'|'navigate'|'card', path?:string, cardKind?:string, say?:string}}
 */
export function interpretCommand(raw) {
  const t = (raw || "").toLowerCase().trim();
  if (!t) return null;

  if (STOP.test(t)) return { kind: "stop" };
  if (HOME.test(t)) return { kind: "navigate", path: "/", say: "Here's your home." };
  if (NEXT.test(t) || DONE.test(t) || THANKS.test(t)) {
    return { kind: "prompt", say: nextPrompt() };
  }

  if (SHOW_VERBS.test(t)) {
    for (const tg of TARGETS) {
      if (tg.keys.some((k) => t.includes(k))) {
        return {
          kind: tg.cardKind ? "card" : "navigate",
          path: tg.path,
          cardKind: tg.cardKind,
          say: `Here's ${tg.label}.`,
        };
      }
    }
  }
  return null; // needs real reasoning -> hand to the LLM
}

/**
 * Execute a local command. Returns true if handled locally (no LLM needed).
 * @param {object} opts
 * @param {object} opts.cmd       result of interpretCommand
 * @param {function} opts.navigate react-router navigate
 * @param {function} [opts.speak]  short spoken confirmation (use free browser TTS)
 * @param {function} [opts.openCard] (cardKind) => bool; open a card on Home
 * @param {function} [opts.closeCard]
 * @param {function} [opts.stopSpeaking]
 */
export function executeCommand({ cmd, navigate, speak, openCard, closeCard, stopSpeaking }) {
  if (!cmd) return false;
  switch (cmd.kind) {
    case "stop":
      stopSpeaking && stopSpeaking();
      return true;
    case "prompt":
      closeCard && closeCard();
      speak && speak(cmd.say);
      return true;
    case "navigate":
      navigate(cmd.path);
      speak && speak(cmd.say);
      return true;
    case "card": {
      if (openCard && openCard(cmd.cardKind)) {
        speak && speak(cmd.say);
        return true;
      }
      navigate(cmd.path);
      speak && speak(cmd.say);
      return true;
    }
    default:
      return false;
  }
}
