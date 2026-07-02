# SpeakEasy — Plan of Action
**Deadline: July 12** (10 days from today, July 2)

---

## 1. Track & Positioning

**Track: Slack Agent for Good**
**Technology:** Real-Time Search API (primary) + Slack AI capabilities (summarization)

**Impact area: Public health / safety** — distracted driving. Also touch on **accessibility** — hands-free, voice-first Slack access helps anyone who can't safely or physically look at a screen (drivers, people with visual impairments, motor impairments, or anyone multitasking in a way that makes reading unsafe).

**Elevator pitch (draft):**
"Distracted driving kills over 3,000 people a year in the US, and checking Slack is part of the problem. SpeakEasy turns Slack into a hands-free voice assistant — reading important messages aloud, summarizing what's happening in a channel, and answering questions by voice — so people never have to look at their phone to stay in the loop. It's built for anyone who can't safely look at a screen: drivers, people with visual or motor impairments, or anyone who needs Slack to just talk back."

**Impact statement (for submission — expand this):**
- **Problem:** Constant Slack notifications pull people's eyes to their phones in unsafe moments — most visibly while driving, but also for anyone with visual/motor impairments who can't easily read a stream of messages.
- **Solution:** SpeakEasy makes Slack fully voice-accessible — spoken summaries, spoken alerts, and voice Q&A — so staying connected to work doesn't require looking at or touching a screen.
- **Who it helps:** commuters/drivers, people with visual impairments, people with limited hand mobility, and anyone in a hands-busy job (warehouse, healthcare, field work) who needs Slack updates without stopping to read.
- **Why it matters:** this is accessibility and public-safety infrastructure that could be built directly into Slack's own platform, not a novelty feature.

---

## 2. MVP — Must Have by July 12

This is the minimum that needs to work live for the 3-min demo. Don't scope beyond this until it's solid.

1. **Slack app in dev sandbox** — Bolt SDK (Node or Python), Events API + Web API scopes configured
2. **"Speak Alerts" toggle** — slash command like `/speak-alerts on #channel` or for a DM/person, stored in a simple DB (even in-memory/JSON for hackathon is fine)
3. **Message capture + summarization** — when a new message lands in a "speak alerts" channel, pull it (and recent thread context) and summarize into a short, spoken-friendly sentence using an LLM (Claude API is easiest since you already know it)
4. **Text-to-speech playback** — simplest path: a small companion web page/app that polls or receives the summary and reads it aloud via the Web Speech API (no native mobile/watch app needed for MVP — simulate "smartwatch" as a phone-sized web view, say so in the demo)
5. **Voice query** — user asks (typed or spoken into the same demo web app) "what's going on in #eng-team" → agent fetches recent messages, summarizes, speaks the answer back
6. **Architecture diagram** — see below
7. **Demo video (~3 min)** — see script below
8. **Text description + elevator pitch** written up
9. **Sandbox access granted** to `slackhack@salesforce.com` and `testing@devpost.com` — do this now, takes 2 minutes, easy to forget under deadline pressure

---

## 3. Nice-to-Have (only after MVP is demo-ready)

Ranked by impact-per-effort:

1. **Priority filtering** — use the Real-Time Search API to check if a message references you, a deadline, or a keyword like "urgent"/boss's name, and only trigger a spoken alert for high-priority items (this is a great way to justify the Real-Time Search API track more directly — worth prioritizing if MVP goes smoothly)
2. **Voice reply / suggested responses** — agent suggests 2-3 short reply options, user picks one by voice ("send the first one"), agent posts to Slack
3. **Speech-to-text replies** — full voice dictation back into Slack instead of picking from suggestions
4. **Driving-mode auto-detect** — simulate via a toggle ("driving mode: on") rather than real GPS/motion detection — still demos well
5. **Real smartwatch integration** (WearOS/watchOS companion) — high effort, low necessity for judging; only attempt if you have major time left
6. **Per-person voice/summary personalization** (e.g., different summary style for boss vs. friends)
7. **Multi-language TTS** — nice touch, low priority

Don't start on any of these until the MVP list is fully working end-to-end.

---

## 4. Architecture Diagram (draft outline)

**Frontend**
- Demo companion web app (simulates phone/watch) — plays TTS, shows voice query input
- Slack slash commands (`/speak-alerts`) as the in-Slack control surface

**Backend**
- Node.js/Python server running Slack Bolt (event listener + command handler)
- Lightweight store (JSON/SQLite) for per-channel/per-user "speak alerts" preferences
- Summarization service — calls Claude API with message/thread context
- TTS service — Web Speech API (free, fast) or Amazon Polly/ElevenLabs if you want higher quality voice for the demo

**APIs**
- Slack Events API (message.channels, message.im)
- Slack Web API (conversations.history, chat.postMessage)
- Real-Time Search API (priority detection / context lookup)
- Claude API (summarization + query answering)
- Web Speech API or Polly (TTS)

I can build this out as an actual visual diagram (SVG) once you confirm the pieces above — just say the word.

---

## 5. Demo Video — Script Skeleton (~3 min)

1. **(0:00–0:20) Hook** — "You're driving, Slack's blowing up, and picking up your phone could get someone hurt. SpeakEasy fixes that."
2. **(0:20–0:50) Problem + concept** — quick explanation of distracted driving + Slack overload
3. **(0:50–1:40) Live demo part 1** — show `/speak-alerts on` in a channel, someone sends a message, companion app speaks the summary aloud
4. **(1:40–2:20) Live demo part 2** — voice query: "what's going on in #eng-team" → spoken summary answer
5. **(2:20–2:50) Impact + stretch vision** — driving safety angle, mention roadmap (priority filtering, smartwatch)
6. **(2:50–3:00) Close** — team name, project name, thank you

---

## 6. Timeline (July 2 → July 12)

| Dates | Focus |
|---|---|
| **Jul 2–3** | Sandbox setup, Bolt app scaffold, get all API keys (Slack, Claude, TTS), grant sandbox access to the two required emails now, assign roles across team, rough out architecture diagram |
| **Jul 4–6** | Build core pipeline: event listener → message capture → summarization → TTS playback. Get `/speak-alerts` toggle working |
| **Jul 7–8** | Build voice query feature. Start priority filtering (Real-Time Search API) if time allows. Begin integration testing |
| **Jul 9** | Full end-to-end test of MVP flow. Fix bugs. Start demo video storyboard/script |
| **Jul 10** | Record and edit demo video. Draft text description, elevator pitch, finalize architecture diagram |
| **Jul 11** | Buffer day — bug fixes, polish, dry-run submission, double check sandbox access is granted |
| **Jul 12** | Final review, submit early in the day (don't wait for the deadline hour) |

---

## 6.5 Submission Checklist (Slack Agent for Good)

- [ ] Project Track: **Slack Agent for Good**
- [ ] Text description (features + functionality)
- [ ] Impact write-up — explicitly explain the social good angle (safety/accessibility), don't leave it implicit
- [ ] ~3-min demo video with real footage of the working product
- [ ] Architecture diagram
- [ ] Slack developer sandbox URL, with access granted to `slackhack@salesforce.com` and `testing@devpost.com`

## 7. Immediate next steps (today)
- [ ] Create Slack app in developer sandbox, add bot scopes
- [ ] Grant access to `slackhack@salesforce.com` and `testing@devpost.com`
- [ ] Decide: Node or Python for Bolt app
- [ ] Get Claude API key + confirm TTS approach (Web Speech API is fastest to ship)
- [ ] Assign owners: Slack event handling / summarization+LLM / TTS+frontend demo app / video+writeup
