<div align="center">

# Open Interview

**开源面试题库 + 模拟面试官 + 免费语音面试**

从 4,000+ 道有出处的真题里按 **公司 / 岗位 / 轮次 / 知识点** 抽题，让你本机的 AI agent
（Claude Code、Codex、Antigravity、Cursor、OpenCode）当面试官：一题一题地问、追问，最后打分。
题目会被读出来，你直接开口回答。

**中文** · [English](README.en.md)

[网页面试](#方式一网页面试推荐) · [在 agent 里用](#方式二在-agent-里用) · [allclose · 手撕](#allclose--手撕大模型手撕题本地评测) · [记忆卡](#记忆卡agent-面试卡组--间隔重复) · [在线刷题](https://bigerbigernerd.github.io/open-interview/) · [题库](#题库) · [贡献题目和面经](CONTRIBUTING.md)

</div>

---

## 为什么做这个

- 面经散落在几十个仓库和帖子里，格式各不相同，agent 没法直接用。
- 现有的「模拟面试 prompt」大多让模型自己编题，题目不真实，也没有公司和轮次的信息。
- 这里把开源题目统一成一种 **带标签、带出处** 的格式，谁都可以提 PR 补充新题和新面经。
  面试官用的是你电脑上已经登录的 agent，不需要 API key，也不额外花钱。

## 五种用法

| | 适合谁 | 怎么开始 |
|---|---|---|
| **网页面试**（推荐） | 想打开网页就开始面试 | `python3 skills/mock-interviewer/scripts/studio.py` |
| **在 agent 里用** | 平时就在 Claude Code / Codex 里干活 | 装上 skill，说「语音面试我」 |
| **在线刷题** | 不想装任何东西，只想刷题 | 打开 [GitHub Pages](https://bigerbigernerd.github.io/open-interview/) |
| **allclose · 手撕** | 准备大模型 / 算法岗的手撕代码 | 网页里的「手撕」，或 `skills/allclose/scripts/allclose.py` |
| **记忆卡** | 要把八股背熟、准备 Agent 岗面试 | 网页里的「记忆卡」，左右划卡复习 |

## 方式一：网页面试（推荐）

![网页面试：选择面试官后端、公司、岗位和轮次](docs/studio.png)

```bash
git clone https://github.com/bigerbigernerd/open-interview
python3 open-interview/skills/mock-interviewer/scripts/studio.py
```

浏览器会自动打开。选一个面试官后端，再选公司、岗位、职级、轮次、语言和题数，点「开始面试」。
之后全程在网页里：题目读出来，你说话回答（也可以打字），可以要提示、跳过、随时结束，最后出报告。

页面会自动检测本机装了哪些 agent CLI，每一轮调用一次（无头模式、没有工具权限、在空目录里运行）：

| 面试官后端 | 命令 | 本机实测每轮耗时 |
|---|---|---|
| Codex | `codex exec`（只读沙箱，推理强度 low） | 约 10-15 秒 |
| Antigravity | `agy -p` | 约 15 秒 |
| Cursor Agent | `cursor-agent -p --mode ask` | 约 15-20 秒 |
| OpenCode | `opencode run --agent plan` | 约 10 秒 |
| Claude Code | `claude -p --tools ""` | 已适配，作者机器上暂未实测 |

用之前先在终端里把对应的 CLI 登录好。想换模型就在「模型」里填，比如 `gpt-5`、`sonnet`、`opencode/big-pickle`。
CLI 装在非标准位置时，可以用环境变量指定路径，例如 `OPEN_INTERVIEW_CODEX_BIN=/path/to/codex`。

检查哪些后端可用：

```bash
python3 skills/mock-interviewer/scripts/backends.py list
python3 skills/mock-interviewer/scripts/backends.py ping codex
```

## 方式二：在 agent 里用

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
这个 skill 只依赖 Python 3 标准库。然后对 agent 说：

```text
模拟面试我：字节跳动 后端 校招一面，45 分钟
用语音面试我，Google SWE phone screen，英文
来 5 道大模型 RAG 方向的题，难度 3 以上，最后给我打分
```

要语音面试时，agent 会启动一个本地语音桥并给你一个链接：

![语音面试界面：面试官光环、题目、屏幕内容和回答区](docs/voice-interview.png)

```text
┌──────────────┐  voice.py ask "…"   ┌───────────────┐   long-poll   ┌────────────────────┐
│   你的 agent  │ ──────────────────▶ │ 本地语音桥     │ ◀───────────▶ │ 浏览器标签          │
│  （面试官大脑）│ ◀────────────────── │ 127.0.0.1:8765│               │ 朗读题目 + 听写回答  │
└──────────────┘     你的回答文本      └───────────────┘               └────────────────────┘
```

`voice.py ask` 最多等 50 秒，候选人还没说完就退出码 3，agent 再循环调用 `voice.py wait`，
所以不会撞上各家 agent 的命令超时。Codex 的默认沙箱会拦本地网络，第一次运行时允许它联网即可。

## 语音说明

- 朗读用浏览器自带的 `speechSynthesis`，免费。Edge 的 *Microsoft … Online (Natural)* 和 Chrome 的 *Google 普通话* 最自然，可以在页面右上角 ⚙ 里换声音和语速。
- 听写用 Web Speech API 的 `SpeechRecognition`，支持 Chrome、Edge、Safari。Firefox 不支持，可以直接打字。
- 隐私：服务只监听本机地址；但 Chrome / Edge 的语音识别会把音频发到 Google / Microsoft 的云端服务。介意的话就打字回答。
- 面试记录保存在 `~/.mock-interviewer/sessions/`，页面上也可以导出 Markdown。

## 自助刷题

同一个页面的「自助刷题」不需要 agent：按岗位、公司、题型、语言筛题，朗读题目，语音或打字作答，
看参考要点和出处。练习记录可以导出成 Markdown，贴给任何 AI 让它打分。

![自助刷题界面](docs/practice.png)

- 本地：`studio.py` 或 `voice.py start` 打开的页面里点「自助刷题」
- 线上：仓库开启 GitHub Pages（Source 选 GitHub Actions）后自动部署到 `https://bigerbigernerd.github.io/open-interview/`

## allclose · 手撕：大模型手撕题，本地评测

![allclose · 手撕：写代码、本地评测、面试官追问](docs/allclose.png)

像力扣一样刷大模型 / 机器学习的手撕题：在网页编辑器里用 numpy 写 Attention、RoPE、KV Cache、
top-p、BPE、DPO、GRPO……点「提交」，代码在**你自己电脑上**的独立 Python 进程里跑，和参考答案逐个用例比对，
误差在 `rtol 1e-5 / atol 1e-6` 内（也就是 `np.allclose`）才算过。代码不上传，没有线上评测机。

- **测试专门抓常见错误**：大数值溢出、mask 加错位置、拆头少了 transpose、RoPE 配对方式、top-p 的边界 token、
  BatchNorm 的有偏 / 无偏方差、AUC 的并列分数…… 每道题都附了几份「典型错误写法」，CI 会确认测试能把它们全部抓出来。
- **答错时直接告诉你哪里错**：哪个用例、哪个位置、期望值、你的输出、最大误差，以及你 `print` 的内容。
- **通过之后面试官追问**：真实的手撕面试里写完代码只是开始。用你本机的 Claude Code / Codex / agy / Cursor / OpenCode
  当面试官，贴着你的代码问 3 个问题（为什么除以 √d？-inf 换成 -1e9 会怎样？），最后打分。卡住时也可以让它看一眼代码给个提示。
- **网页和命令行共用同一份文件**：代码存在 `~/allclose/<题目>.py`，在 VS Code 里改、在网页里提交都行。

| 方向 | 题数 | 题目 |
|---|---|---|
| 大模型 | 18 | 缩放点积注意力（带 mask） · 多头注意力 MHA · 旋转位置编码 RoPE · temperature + top-k + top-p 采样 · 分组查询注意力 GQA · 带 KV Cache 的单步解码 · SwiGLU · LoRA · Beam Search · 字节级 BPE 训练 · MoE 路由 + 负载均衡损失 · DPO · PPO 截断目标 · GRPO · 合并分块注意力结果（FlashAttention 的核心） · CLIP 对比损失 · int8 量化 · 投机解码的验收步骤 |
| 深度学习 | 8 | 数值稳定的 Softmax · 交叉熵（带 label smoothing） · LayerNorm · RMSNorm · BatchNorm（含 running stats） · AdamW · 手推 MLP 反向传播 · 二维卷积 |
| 机器学习基础 | 4 | 手写 AUC · 逻辑回归 · K-Means · IoU + NMS |

简单 10 道、中等 14 道、困难 6 道，题面中英双语。

```bash
# 网页：和模拟面试同一个服务，打开后点「手撕」
python3 open-interview/skills/mock-interviewer/scripts/studio.py

# 命令行
cd open-interview/skills/allclose
python3 scripts/allclose.py list              # 题单，✓ 表示已通过
python3 scripts/allclose.py pull attention    # 生成 ~/allclose/attention.py，用任何编辑器写
python3 scripts/allclose.py test attention    # 全部用例；--run 只跑样例
python3 scripts/allclose.py hint attention    # 下一条提示
```

评测需要 numpy：当前 Python 有 numpy 就直接用；没有的话如果装了 [uv](https://docs.astral.sh/uv/)，会自动用
`uv run --with numpy`；都没有就 `pip install numpy`。在线页面（GitHub Pages）只能看题和写草稿，评测和追问都要在本地跑。

在 Claude Code / Codex 里也能用：装上 `allclose` skill 后说「出一道大模型手撕题给我」，agent 会出题、
在本地评测你的文件、通过后追问。新增题目的格式见 [skills/allclose/SKILL.md](skills/allclose/SKILL.md)。

## 记忆卡：Agent 面试卡组 + 间隔重复

![记忆卡：翻面看答案，往右划记得、往左划忘了](docs/cards.png)

像 Anki 一样背八股：先在心里答一遍，点卡片看答案，**往右划 = 记得，往左划 = 忘了**（键盘 `→` / `←`，
`↑` 简单、`↓` 模糊，`Z` 撤销）。下次什么时候再出现由 [FSRS](https://github.com/open-spaced-repetition/fsrs4anki)
算法决定，和 Anki 现在默认用的是同一个调度器：记得牢的卡间隔越拉越长，忘了的很快再出现。

- **Agent 面试卡组（315 张，带参考答案）**：Agent 基础与规划、工具调用与 MCP、记忆与上下文工程、多 Agent 与框架、
  评估 / 安全 / 上线、RAG、Agent 训练与大模型基础、场景设计 / 项目深挖 / 手写代码。每张卡背面是「开口 30 秒该说的答案」
  加要点清单和常见追问。新卡按「有答案 → Agent 核心主题 → 高频 → 由易到难」的顺序出现，RAG 和大模型基础作为辅助。
  也可以切到「Agent 岗全部题」（加上题库里 500 多道没有答案的真题）或整个题库。
- **复盘**：此刻平均记得的概率、近 30 天真实记忆率、你的遗忘曲线（FSRS 预测和实际记得的比例放在一张图里）、
  每天复习量和记忆率、未来 14 天到期量、按标签 / 主题排出的薄弱点，以及最常忘的题，一键加练。
- **标签**：每张卡可以打「重点 / 易错 / 不会 / 项目相关」或自己的标签，按标签筛选复习、按标签看记忆率。
- **导出给 AI 复盘**：把薄弱主题和最常忘的题连同参考答案导出成 Markdown，贴给任意 AI 让它出追问。
- **记录存在哪**：用 `studio.py` 打开时存在本机 `~/.mock-interviewer/cards/reviews.jsonl`（每次复习一行，状态都从这个
  日志重算，换端口、换浏览器都不丢）；在线页面存在浏览器里，可以导出 / 导入 JSON 搬到本地。
- **本地扩展卡组**：在 `skills/mock-interviewer/data/` 放一个 `cards-extra.json`（已加入 `.gitignore`，不进仓库），
  记忆卡会把里面的题合进来，卡组下拉框多出「面经真题 / 高频 / 按领域 / 按课程」几组，课程卡组按讲次顺序出新卡。
  答案和题目里的 `$公式$` 用 KaTeX 渲染。文件格式见 `ui/cards.js` 里的 `mergeExtra`。

| 分组 | 张数 | 内容 |
|---|---|---|
| Agent 基础与规划 | 39 | Agent 的定义、Agent 和 Workflow 怎么选、ReAct / Plan-and-Execute / ReWOO / Reflexion、推理模型、失败模式、Prompt |
| 工具调用与 MCP | 37 | function calling 与约束解码、几百个工具怎么选、出错回滚、MCP（架构、传输、授权、2026-07-28 无状态版）、A2A、computer use |
| 记忆与上下文工程 | 40 | 短期 / 长期记忆、记忆的读写与遗忘、MemGPT / mem0、压缩与子 Agent 隔离、lost in the middle、prompt caching |
| 多 Agent 与框架 | 39 | 编排模式、handoff、共享状态、多 Agent 失败分类、LangGraph、OpenAI Agents SDK、Claude Agent SDK、CrewAI / AutoGen |
| 评估、安全与上线 | 42 | 轨迹评估、LLM-as-a-judge、SWE-bench / GAIA / τ-bench / BFCL、tracing、成本和延迟、prompt injection、沙箱与审批 |
| RAG（辅） | 39 | 解析与切分、混合检索、rerank、HNSW / IVF-PQ、Agentic RAG、GraphRAG、RAG 评测与坏 case 排查 |
| Agent 训练与大模型基础（辅） | 40 | 工具调用 SFT、Agentic RL / GRPO / reward hacking、DPO、注意力 / KV cache / RoPE、推理加速、MoE |
| 场景设计、项目深挖、手写代码 | 39 | 客服 / Deep Research / 编程 Agent 设计、项目怎么讲、手写 ReAct 循环 / 流式工具调用解析 / 重试与限流 |

其中 111 张标了高频；题型是八股 268、场景设计 20、手写代码 13、项目 10、行为面 4。答案由多个 agent 分领域整理，涉及论文数字、协议细节和框架 API 的大多对照过原文，拿不准的写成了不依赖具体数字的说法；发现不准的地方欢迎提 issue。

## 题库

当前 **5,481** 道题：其中 5,166 道（含 60 份面经里的 893 道）来自 18 个许可证允许再分发的开源项目，每道题都保留了原始链接；另外 315 道是上面带答案的 Agent 面试卡组。题目来源：

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
目前有 **60** 份面经（893 道题，中文 44 份、英文 16 份），都是上游作者本人的面试记录，仓库用 MIT 许可证；公司、轮次、日期、结果只取作者写明的，没写就留空：

| 来源 | 面经 | 公司 / 方向 |
|---|---:|---|
| [HurleyWong/vuepress-interview-hurley](https://github.com/HurleyWong/vuepress-interview-hurley) | 13 | 字节、微信读书、阿里飞猪、微博、海康等，Android / Java 校招（上游未分轮次） |
| [CocaineCong/Golang-Interview](https://github.com/CocaineCong/Golang-Interview) | 11 | 字节、B站、百度、滴滴、米哈游、知乎、蔚来等，Go 后端 |
| [mayukhkchanda/react-interview-experience](https://github.com/mayukhkchanda/react-interview-experience) | 10 | Cvent、MakeMyTrip、Amdocs、Capgemini 等，React 前端社招（英文） |
| [imrohit1997/interview_experiences](https://github.com/imrohit1997/interview_experiences) | 6 | Deloitte、Infosys、LTIMindtree、iAcuity，Java 后端，2026（英文） |
| [Electronic-Waste/My-Job-Hunting](https://github.com/Electronic-Waste/My-Job-Hunting) | 4 | 字节基架、Intel、RisingWave、Databend，实习，带结果 |
| [Pypy233/Interview-Collection](https://github.com/Pypy233/Interview-Collection) | 4 | 头条基础架构、蚂蚁、大摩、SAP，实习 |
| [jx888-max/Interview-experience](https://github.com/jx888-max/Interview-experience) | 3 | 字节多模态、阿里大模型、快手算法，2025-10 日常实习 |
| [kevin-jk/InterviewExp](https://github.com/kevin-jk/InterviewExp) | 3 | 华为、招银网络科技、蚂蚁，Java 后端社招，都拿到 offer |
| [tumiMsaki/Interview-experience](https://github.com/tumiMsaki/Interview-experience) | 3 | 百度搜索、腾讯云、网易游戏，前端，带每轮时长 |
| [GGboya/interview](https://github.com/GGboya/interview) | 3 | 字节抖音支付 / 国际商业化、百度，后端，2024-2025 |

你自己的面经最有价值（模板：[`bank/experiences/_template.yml`](bank/experiences/_template.yml)）。

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
  questions/                题目；imported/ 由脚本从上游生成，不要手改；agent/ 是带答案的 Agent 面试卡组
  experiences/              面经，一次面试一个文件；imported/ 由脚本从上游生成
skills/allclose/            allclose · 手撕（可单独安装的 skill）
  problems/<id>/            每题一个文件夹：题面、模板、参考答案、测试、典型错误写法
  scripts/allclose.py       命令行 + 评测（只用标准库）
  scripts/runner.py         在独立进程里跑你的代码（需要 numpy）
  data/problems.json        由 tools/build.py 生成
skills/mock-interviewer/    可单独安装的 skill
  SKILL.md                  面试官流程
  scripts/bank.py           查题（只用标准库）
  scripts/voice.py          agent 驱动模式的语音桥（只用标准库）
  scripts/studio.py         网页面试服务（只用标准库）
  scripts/backends.py       调用本机 agent CLI 的适配层
  scripts/cards.py          记忆卡的复习记录存取
  ui/                       面试、自助刷题、手撕、记忆卡页面（无依赖、无构建；fsrs.js 是调度算法）
  data/index.json           由 tools/build.py 生成的题库索引
tools/build.py              校验 bank/ 和手撕题，生成索引
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
- [ ] 在线刷题页面支持填 OpenAI 兼容的 API key（DeepSeek、通义、Ollama），不装 agent 也能面试
- [ ] 跨来源去重、难度校准
- [ ] 更多岗位：数据、测试、运维、产品
- [ ] 手撕：PyTorch 题目（autograd、自定义 Function）、更多大模型推理和训练题
- [ ] 手撕：在线页面用 Pyodide 在浏览器里评测（仍然是本地运行）
- [ ] 手撕：从面经里给题目补「哪家公司考过」的标签

## License

代码和 allclose 手撕题 MIT（[LICENSE](LICENSE)）；题库 CC BY-SA 4.0，第三方来源和许可证见 [LICENSE-DATA.md](LICENSE-DATA.md)。
