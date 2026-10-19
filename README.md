<div align="center">

# Open Interview

**开源面试题库 + 模拟面试官 Skill + 免费语音面试**

让你的 AI agent 变成面试官：从 4,000+ 道有出处的真题里按 **公司 / 岗位 / 轮次 / 知识点** 抽题，
一题一题地问、追问、最后打分。想练口语面试，就开一个浏览器标签：题目用语音读出来，你用嘴回答。

[在线刷题](https://bigerbigernerd.github.io/open-interview/) · [快速开始](#快速开始) · [语音面试](#语音面试) · [自助刷题](#自助刷题) · [题库](#题库) · [贡献题目和面经](CONTRIBUTING.md) · [English](#english)

</div>

---

## 为什么做这个

- 面经散落在几十个仓库和帖子里，格式各不相同，agent 没法直接用。
- 现有的「模拟面试 prompt」大多让模型自己编题，题目不真实，也没有公司和轮次的信息。
- 这里把开源题目统一成一种 **带标签、带出处** 的格式，谁都可以提 PR 补充新题和新面经，
  任何支持 Skills 的 agent 都能直接拿来当面试官用。

## 快速开始

**Claude Code**

```bash
/plugin marketplace add bigerbigernerd/open-interview
/plugin install open-interview@open-interview
```

**Codex / Cursor / Gemini CLI / OpenCode 等支持 Agent Skills 的工具**

```bash
npx skills add bigerbigernerd/open-interview
```

或者直接把 `skills/mock-interviewer/` 整个文件夹复制到你的 agent 的 skills 目录（例如 `~/.claude/skills/`）。
这个 skill 只依赖 Python 3 标准库。

然后对 agent 说：

```text
模拟面试我：字节跳动 后端 校招一面，45 分钟
用语音面试我，Google SWE phone screen，英文
来 5 道大模型 RAG 方向的题，难度 3 以上，最后给我打分
```

## 语音面试

![语音面试界面：面试官光环、题目、屏幕内容和回答区](docs/voice-interview.png)

```text
┌──────────────┐  voice.py ask "…"   ┌───────────────┐   long-poll   ┌────────────────────┐
│   你的 agent  │ ──────────────────▶ │ 本地语音桥     │ ◀───────────▶ │ 浏览器标签          │
│  （面试官大脑）│ ◀────────────────── │ 127.0.0.1:8765│               │ 朗读题目 + 听写回答  │
└──────────────┘     你的回答文本      └───────────────┘               └────────────────────┘
```

- agent 负责出题、追问、打分；浏览器只负责「说」和「听」。不需要任何 API key，也不花钱。
- 朗读用浏览器自带的 `speechSynthesis`；Edge 的 *Microsoft … Online (Natural)* 和 Chrome 的 *Google 普通话* 最自然。
- 听写用 Web Speech API 的 `SpeechRecognition`，支持 Chrome、Edge、Safari。Firefox 不支持，可以直接打字。
- 隐私：语音桥只监听本机地址；但 Chrome / Edge 的语音识别会把音频发到 Google / Microsoft 的云端服务。介意的话就打字回答。
- 「要提示 / 跳过 / 结束面试」按钮会把信号传给 agent；面试记录保存在 `~/.mock-interviewer/sessions/`。

手动试一下（不经过 agent）：

```bash
python3 skills/mock-interviewer/scripts/voice.py start
python3 skills/mock-interviewer/scripts/voice.py ask "请做一个简单的自我介绍"
```

## 自助刷题

同一个页面的「自助刷题」不需要 agent：按岗位、公司、题型、语言筛题，朗读题目，语音或打字作答，
看参考要点和出处。练习记录可以导出成 Markdown，贴给任何 AI 让它打分。

![自助刷题界面](docs/practice.png)

- 本地：`voice.py start` 后打开 `http://127.0.0.1:8765/#practice`
- 线上：仓库开启 GitHub Pages（Source 选 GitHub Actions）后自动部署到 `https://bigerbigernerd.github.io/open-interview/`

## 题库

当前 **4,273** 道题，来自 8 个许可证允许再分发的开源项目，每道题都保留了原始链接：

| 来源 | 题数 | 方向 | 许可证 |
|---|---:|---|---|
| [haizlin/fe-interview](https://github.com/haizlin/fe-interview) | 2,789 | 前端（中文，抽样权重调低） | MIT |
| [Snailclimb/JavaGuide](https://github.com/Snailclimb/JavaGuide) | 721 | Java 后端、计算机基础、AI 应用 | Apache-2.0 |
| [SuperGODOG/ai-agent-interview-240](https://github.com/SuperGODOG/ai-agent-interview-240) | 235 | AI Agent 开发、大模型、八股 | MIT |
| [h5bp/Front-end-Developer-Interview-Questions](https://github.com/h5bp/Front-end-Developer-Interview-Questions) | 145 | 前端（英文） | MIT |
| [kdn251/interviews](https://github.com/kdn251/interviews) | 129 | 算法题，按公司标注 | MIT |
| [yangshun/tech-interview-handbook](https://github.com/yangshun/tech-interview-handbook) | 117 | 行为面，按公司标注 | MIT |
| [MisterBooo/llm-interview-questions](https://github.com/MisterBooo/llm-interview-questions) | 100 | 大模型 / RAG / Agent | CC BY-SA 4.0 |
| [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) | 37 | 系统设计 | CC BY 4.0 |

每道题的标签：

| 字段 | 例子 | 说明 |
|---|---|---|
| `companies` | `bytedance`, `google` | 只有确实在这家公司被问过才标；别名可查（字节、tiktok 都能命中） |
| `roles` | `backend`, `frontend`, `ai-agent`, `llm-algorithm` | 有层级：查 `backend` 也会带上通用 `swe` 题 |
| `type` | `technical` `coding` `system-design` `behavioral` `project` `hr` | 八股 / 手撕 / 系统设计 / 行为面 / 项目 / HR |
| `topics` | `redis`, `rag`, `react` | 开放集合 |
| `levels` / `difficulty` / `hot` | `campus`, `3`, `true` | 校招社招、难度 1-5、高频 |

面经（一次真实面试的多轮记录）放在 `bank/experiences/`，agent 会优先按面经里的轮次结构来面。
**目前还没有面经，第一份等你来贡献**（模板：[`bank/experiences/_template.yml`](bank/experiences/_template.yml)）。

命令行查询：

```bash
cd skills/mock-interviewer
python3 scripts/bank.py stats
python3 scripts/bank.py sample --company 字节 --role backend --mix technical=3,coding=1,behavioral=1
python3 scripts/bank.py search --role ai-agent --topic rag --difficulty 3-5
python3 scripts/bank.py show <id> -v
```

## 仓库结构

```text
bank/
  tags.yml                  受控标签表：公司（含别名）、岗位（含层级）、题型、职级、常用 topic
  questions/                题目；imported/ 由脚本从上游生成，不要手改
  experiences/              面经，一次面试一个文件
skills/mock-interviewer/    可单独安装的 skill
  SKILL.md                  面试官流程
  scripts/bank.py           查题（只用标准库）
  scripts/voice.py          语音桥（只用标准库）
  ui/                       语音面试 + 自助刷题页面（无依赖、无构建）
  data/index.json           由 tools/build.py 生成的题库索引
tools/build.py              校验 bank/ 并生成索引
tools/import_upstream.py    重新导入上游题库
schema/                     给编辑器用的 JSON Schema（YAML 自动补全）
```

## 贡献

最有价值的贡献：**真实面经**、给已有题目补 `key_points`（好回答的要点）、纠正公司标签、新的开源题源。
详见 [CONTRIBUTING.md](CONTRIBUTING.md)。不会 git 也可以用 Issue 表单提交面经。

## Roadmap

- [ ] 第一批真实面经（字节 / 阿里 / 腾讯 / 美团 / 大模型岗）
- [ ] 高频题补全 `key_points`，让打分更稳定
- [ ] 完全离线的语音：本地 Whisper 听写、Kokoro / Piper 朗读
- [ ] 跨来源去重、难度校准
- [ ] 更多岗位：数据、测试、运维、产品

## License

代码 MIT（[LICENSE](LICENSE)）；题库 CC BY-SA 4.0，第三方来源和许可证见 [LICENSE-DATA.md](LICENSE-DATA.md)。

---

## English

**Open Interview** is an open, community-maintained interview question bank packaged as an Agent Skill.
Your agent becomes the interviewer: it samples real, sourced questions by company, role, round type and topic,
asks one at a time with follow-ups, and ends with a scored report. For spoken practice it opens a local
browser tab that reads questions aloud (free Web Speech API) and transcribes your answers.

- Install in Claude Code: `/plugin marketplace add bigerbigernerd/open-interview`, then `/plugin install open-interview@open-interview`.
- Other agents: `npx skills add bigerbigernerd/open-interview`, or copy `skills/mock-interviewer/` into your skills folder.
- Then ask: *"Mock interview me for a Google SWE phone screen, by voice."*
- Contribute questions and interview reports via pull request: see [CONTRIBUTING.md](CONTRIBUTING.md).
