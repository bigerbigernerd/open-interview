<div align="center">

# Open Interview

**Open interview question bank + mock interviewer + free voice interviews**

Draws real, sourced questions from a bank of 4,000+ by **company / role / round / topic**, and lets the AI agent
already on your machine (Claude Code, Codex, Antigravity, Cursor, OpenCode) be the interviewer: one question at a
time, follow-ups, then a scored report. Questions are read aloud and you answer out loud.

[中文](README.md) · **English**

[Web interview](#option-1-web-interview-recommended) · [Inside your agent](#option-2-inside-your-agent) · [Practice online](https://bigerbigernerd.github.io/open-interview/) · [Question bank](#question-bank) · [Contribute](CONTRIBUTING.md)

</div>

---

## Why

- Interview reports (面经) are scattered across dozens of repos and posts in different formats that agents can't use.
- Most "mock interview prompts" let the model invent questions, with no real company or round context.
- This project normalises open-source questions into one **tagged, sourced** format that anyone can extend by pull
  request. The interviewer runs on the agent you are already logged in to: no API key, no extra cost.

## Three ways to use it

| | For | Start with |
|---|---|---|
| **Web interview** (recommended) | Open a page and start | `python3 skills/mock-interviewer/scripts/studio.py` |
| **Inside your agent** | You already live in Claude Code / Codex | Install the skill, say "mock interview me by voice" |
| **Practice online** | Nothing to install, just drill questions | [GitHub Pages](https://bigerbigernerd.github.io/open-interview/) |

## Option 1: web interview (recommended)

![Web interview: pick the interviewer backend, company, role and round](docs/studio.png)

```bash
git clone https://github.com/bigerbigernerd/open-interview
python3 open-interview/skills/mock-interviewer/scripts/studio.py
```

A browser tab opens. Pick an interviewer backend, then company, role, level, round, language and number of
questions, and press start. Everything happens in the page: questions are spoken, you answer by voice (or typing),
ask for a hint, skip, or end at any time, and get a report at the end.

The page detects which agent CLIs are installed and calls one per turn (headless, no tools, in an empty directory):

| Backend | Command | Measured per turn |
|---|---|---|
| Codex | `codex exec` (read-only sandbox, low reasoning effort) | ~10-15 s |
| Antigravity | `agy -p` | ~15 s |
| Cursor Agent | `cursor-agent -p --mode ask` | ~15-20 s |
| OpenCode | `opencode run --agent plan` | ~10 s |
| Claude Code | `claude -p --tools ""` | adapter written, not yet run on the author's machine |

Log in to the CLI in a terminal first. Use the model field to pick a model (e.g. `gpt-5`, `sonnet`,
`opencode/big-pickle`). If a CLI lives somewhere unusual, point to it with an environment variable such as
`OPEN_INTERVIEW_CODEX_BIN=/path/to/codex`.

Check which backends work:

```bash
python3 skills/mock-interviewer/scripts/backends.py list
python3 skills/mock-interviewer/scripts/backends.py ping codex
```

## Option 2: inside your agent

**Claude Code**

```bash
/plugin marketplace add bigerbigernerd/open-interview
/plugin install open-interview@open-interview
```

**Codex / Cursor / Gemini CLI / OpenCode and other Agent Skills tools**

```bash
npx skills add bigerbigernerd/open-interview
```

Or copy `skills/mock-interviewer/` into your agent's skills folder (e.g. `~/.claude/skills/`). The skill only needs
the Python 3 standard library. Then ask:

```text
Mock interview me for a Google SWE phone screen, by voice, in English
Give me 5 LLM / RAG questions, difficulty 3+, and score me at the end
```

For voice interviews the agent starts a local bridge and gives you a link:

![Voice interview: interviewer orb, question, on-screen content and answer box](docs/voice-interview.png)

```text
┌──────────────┐  voice.py ask "…"   ┌───────────────┐   long-poll   ┌──────────────────────┐
│  your agent  │ ──────────────────▶ │ local bridge  │ ◀───────────▶ │ browser tab          │
│ (the brains) │ ◀────────────────── │ 127.0.0.1:8765│               │ speaks + transcribes │
└──────────────┘   your answer text   └───────────────┘               └──────────────────────┘
```

`voice.py ask` waits at most 50 seconds; if you are still talking it exits with code 3 and the agent loops on
`voice.py wait`, so it never runs into an agent's command timeout. Codex's default sandbox blocks local network
access; allow it the first time it runs.

## About the voice

- Speech uses the browser's built-in `speechSynthesis`, which is free. Edge's *Microsoft … Online (Natural)* and
  Chrome's *Google* voices sound best; change voice and speed under ⚙ in the top-right corner.
- Transcription uses the Web Speech API (`SpeechRecognition`) in Chrome, Edge and Safari. Firefox lacks it; type instead.
- Privacy: the server only listens on localhost, but Chrome and Edge send audio to Google / Microsoft cloud speech
  services. If that bothers you, type your answers.
- Transcripts are saved to `~/.mock-interviewer/sessions/` and can be exported as Markdown from the page.

## Self practice

The "自助刷题" tab needs no agent: filter by role, company, type and language, hear the question, answer by voice
or typing, and reveal key points and the source. Export your practice log as Markdown and paste it into any AI
for grading.

![Self practice](docs/practice.png)

- Locally: the page opened by `studio.py` or `voice.py start`
- Online: enable GitHub Pages (Source: GitHub Actions) and it deploys to `https://bigerbigernerd.github.io/open-interview/`

## Question bank

**4,796** questions (523 of them from 35 interview reports) from 13 permissively licensed open-source projects, each with a link back to its source. Question sources:

| Source | Questions | Area | License |
|---|---:|---|---|
| [haizlin/fe-interview](https://github.com/haizlin/fe-interview) | 2,789 | Front end (Chinese, lower sampling weight) | MIT |
| [Snailclimb/JavaGuide](https://github.com/Snailclimb/JavaGuide) | 721 | Java back end, CS fundamentals, AI apps | Apache-2.0 |
| [SuperGODOG/ai-agent-interview-240](https://github.com/SuperGODOG/ai-agent-interview-240) | 235 | AI agent engineering, LLMs | MIT |
| [h5bp/Front-end-Developer-Interview-Questions](https://github.com/h5bp/Front-end-Developer-Interview-Questions) | 145 | Front end (English) | MIT |
| [kdn251/interviews](https://github.com/kdn251/interviews) | 129 | Coding, tagged by company | MIT |
| [yangshun/tech-interview-handbook](https://github.com/yangshun/tech-interview-handbook) | 117 | Behavioral, tagged by company | MIT |
| [MisterBooo/llm-interview-questions](https://github.com/MisterBooo/llm-interview-questions) | 100 | LLM / RAG / agents | CC BY-SA 4.0 |
| [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) | 37 | System design | CC BY 4.0 |

Tags on every question:

| Field | Example | Notes |
|---|---|---|
| `companies` | `bytedance`, `google` | Only where the question was actually asked; aliases work (字节, tiktok) |
| `roles` | `backend`, `frontend`, `ai-agent`, `llm-algorithm` | Hierarchical: `backend` also matches general `swe` questions |
| `type` | `technical` `coding` `system-design` `behavioral` `project` `hr` | |
| `topics` | `redis`, `rag`, `react` | Open vocabulary |
| `levels` / `difficulty` / `hot` | `campus`, `3`, `true` | Hiring track, 1-5, high frequency |

Interview reports (面经, one real interview with its rounds) live in `bank/experiences/`; the interviewer mirrors
their round structure when one exists. There are **35** so far (523 questions): the upstream authors' own interviews from 5
MIT-licensed repos, covering 30 companies including ByteDance, Alibaba, Tencent, Baidu, Kuaishou, Bilibili and
miHoYo, mostly back-end, Android and infrastructure roles. Company, rounds, date and result are only filled in
where the author stated them. Sources are listed in [LICENSE-DATA.md](LICENSE-DATA.md). Template: [`bank/experiences/_template.yml`](bank/experiences/_template.yml).

Query from the command line:

```bash
cd skills/mock-interviewer
python3 scripts/bank.py stats
python3 scripts/bank.py sample --company bytedance --role backend --mix technical=3,coding=1,behavioral=1
python3 scripts/bank.py search --role ai-agent --topic rag --difficulty 3-5
python3 scripts/bank.py show <id> -v
```

## Repository layout

```text
bank/
  tags.yml                  controlled tags: companies (with aliases), roles (with parents), types, levels, topics
  questions/                questions; imported/ is generated from upstream, do not edit by hand
  experiences/              interview reports, one file per interview
skills/mock-interviewer/    the installable skill
  SKILL.md                  interviewer workflow
  scripts/bank.py           question queries (stdlib only)
  scripts/voice.py          voice bridge for agent-driven mode (stdlib only)
  scripts/studio.py         web interview server (stdlib only)
  scripts/backends.py       adapters that run local agent CLIs
  ui/                       interview + practice page (no dependencies, no build)
  data/index.json           question index built by tools/build.py
tools/build.py              validate bank/ and build the index
tools/import_upstream.py    re-import upstream question banks
schema/                     JSON Schema for editor autocompletion of the YAML files
```

## Contributing

Most valuable: **real interview reports**, `key_points` (what a strong answer covers) for existing questions,
corrected company tags, and new permissively licensed sources. See [CONTRIBUTING.md](CONTRIBUTING.md) (in Chinese);
non-git users can submit an interview report through the issue form.

## Roadmap

- [ ] First batch of real interview reports (ByteDance / Alibaba / Tencent / Meituan / LLM roles)
- [ ] `key_points` for high-frequency questions, for steadier scoring
- [ ] Fully offline voice: local Whisper transcription, Kokoro / Piper speech
- [ ] OpenAI-compatible API key support on the online page (DeepSeek, Qwen, Ollama), so no agent is needed
- [ ] Cross-source de-duplication and difficulty calibration
- [ ] More roles: data, QA, SRE, product

## License

Code: MIT ([LICENSE](LICENSE)). Question bank: CC BY-SA 4.0; third-party sources and licenses in
[LICENSE-DATA.md](LICENSE-DATA.md).
