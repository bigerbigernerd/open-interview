# 贡献指南

谢谢你愿意帮忙！这个题库给 agent 用，所以**格式统一、标签准确、出处清楚**比数量更重要。

## 能贡献什么

| 想做的事 | 改哪里 |
|---|---|
| 分享一次真实面试（面经） | 新建 `bank/experiences/<公司>/<YYYY-MM>-<岗位>-<短名>.yml` |
| 补充题目 | 新建或修改 `bank/questions/<topic>/<文件名>.yml` |
| 给已有题目补要点、追问、纠正标签 | 在 `bank/questions/` 下新建一个文件，写同样的题加上 `key_points`；imported 文件是生成的，别直接改 |
| 新增公司 / 岗位 | `bank/tags.yml` |
| 接入新的开源题库 | `tools/import_upstream.py`（只接受许可证允许再分发的仓库） |

不会 git？用 Issue 里的「提交面经」表单，维护者或 agent 会帮你转成文件。

## 三条硬规则

1. **有出处、有权利。** 自己的面试经历直接写。转载别人的面经，要么得到作者同意，要么用自己的话重新整理，并在 `source.url` 附上原帖链接。不要整段复制别人受版权保护的答案。
2. **不泄密、不暴露隐私。** 删掉姓名、联系方式、面试官名字、内部项目代号；签过保密协议（NDA）不能外传的题不要提交。
3. **公司标签要真实。** 只有确实在这家公司被问过才写 `companies`。「我觉得字节会问」不算。

提交即表示你同意以 CC BY-SA 4.0 授权你贡献的内容（见 [LICENSE-DATA.md](LICENSE-DATA.md)）。

## 写一份面经

复制 [`bank/experiences/_template.yml`](bank/experiences/_template.yml)，最少只需要这些：

```yaml
company: meituan
role: backend
level: campus
date: 2026-09
result: unknown
source: { name: 自己的面试, license: CC-BY-SA-4.0 }
rounds:
  - name: 一面
    questions:
      - 介绍一下你的项目，难点是什么
      - q: 手撕：反转链表
        type: coding
  - name: 二面
    type: system-design
    questions:
      - 设计一个短链系统
```

题目可以直接写一句话，也可以写成带 `type` / `topics` / `followups` 的对象。每一轮的 `type` 是这一轮题目的默认题型。

## 写题目

复制 [`bank/questions/_template.yml`](bank/questions/_template.yml)。`defaults` 里的字段会套用到文件里每一道题：

```yaml
source: { name: open-interview contributors, license: CC-BY-SA-4.0 }
defaults: { lang: zh, type: technical, roles: [backend], topics: [mysql] }
questions:
  - MySQL 的 MVCC 是怎么实现的？
  - q: 为什么 InnoDB 用 B+ 树而不是 B 树或哈希？
    difficulty: 2
    followups: [联合索引的最左前缀是怎么回事？]
    key_points: [磁盘 IO 次数, 范围查询, 叶子节点链表]
```

字段说明（完整定义在 [`schema/`](schema/)，用 VS Code 的 YAML 插件可以自动补全）：

| 字段 | 必填 | 说明 |
|---|---|---|
| `q` | ✓ | 题目，按面试官的口吻写，600 字以内 |
| `lang` | ✓ | `zh` / `en`（一般写在 defaults 里） |
| `type` | | `technical`（默认）/ `coding` / `system-design` / `behavioral` / `project` / `hr` |
| `roles` | | `bank/tags.yml` 里的岗位；不写表示所有岗位通用 |
| `companies` | | `bank/tags.yml` 里的公司；只写确实问过的 |
| `topics` | | 小写连字符，例如 `redis`、`react`、`rag` |
| `levels` | | `intern` `campus` `junior` `mid` `senior` `staff` |
| `difficulty` | | 1-5 |
| `followups` | | 常见追问 |
| `key_points` | | 好回答应该覆盖的要点，agent 打分时会参考 |
| `hot` / `weight` | | 高频标记 / 抽样权重（默认 1） |
| `url` | | 出处链接 |

### 给记忆卡组加题（`bank/questions/agent/`）

记忆卡的「Agent 面试卡组」就是这个目录里 id 以 `agent-` 开头的题。除了上面的字段，这里的题还要求：

- **必须写 `id`**（`agent-<领域>-<短名>`），以后改题面也不改 id，因为大家的复习记录是按 id 存的。
- **必须有 `answer_brief` 和 `key_points`**：`answer_brief` 是开口 30 秒该说的答案（2-4 句），`key_points` 是 3-6 条具体的机制、取舍或数字，卡片背面就显示这两样。
- 涉及论文数字、协议细节、框架 API 的，写之前先查原文；查不到就写成不依赖具体数字的说法。

## 本地校验

```bash
pip install pyyaml
python3 tools/build.py --check   # 只校验
python3 tools/build.py           # 校验并重新生成 skills/mock-interviewer/data/index.json
```

PR 不需要提交重新生成的 `index.json`，合并到 main 后 CI 会自动生成。CI 失败时，日志会指出哪个文件、第几道题、什么问题。

## 新增公司或岗位

在 `bank/tags.yml` 里按格式加一行，`aliases` 写上常见叫法（中文名、英文名、旧名、子品牌），这样用户搜「字节」「抖音」「tiktok」都能找到。岗位可以设 `parent`，比如 `android` 的 parent 是 `mobile`。

## 接入新的开源题库

1. 确认对方的许可证允许再分发（MIT / Apache-2.0 / BSD / CC BY / CC BY-SA / CC0）。没有许可证的仓库不能导入。
2. 在 `tools/import_upstream.py` 的 `SOURCES` 里登记，写一个 `imp_xxx` 函数，只导入题目文本和简短元数据。
3. 运行 `python3 tools/import_upstream.py xxx`，抽查生成的文件，然后在 `LICENSE-DATA.md` 的表格里加上署名。

面经来源还要多一条：必须是仓库作者（或 PR 贡献者）本人的面试，转载牛客 / 小红书 / 知乎帖子的合集不行。
导入的面经生成到 `bank/experiences/imported/<来源>/`，公司、岗位、轮次、日期、结果只写上游写明的，没写就不填。

## 出一道手撕题（allclose）

`skills/allclose/problems/<id>/` 一题一个文件夹，照着已有的题抄一份改最快：

| 文件 | 内容 |
|---|---|
| `problem.yml` | `num`（编号，不能写成 `no`，YAML 会把它当成 false）、中英标题、`difficulty`、`track`（ml / dl / llm）、`topics`、`entry`（函数名）、中英题面、提示、通过后的追问 |
| `starter.py` | 函数签名 + 一行说明 + `raise NotImplementedError` |
| `solution.py` | 参考答案。只用 numpy 和标准库 |
| `tests.py` | `cases()` 返回用例列表：`dict(name=..., kwargs=..., sample=True)`；`sample` 的用例「运行」时会跑。可选 `limit`（秒）、`rtol`、`atol` |
| `wrong.py` | 至少一个典型错误写法（漏了数值稳定、轴弄错、约定写反……），函数签名和题目一样 |

题面要把约定写死（形状、哪一维、平局怎么处理、eps 加在哪），否则不同的正确写法会被判错。
测试除了随机用例，至少要有：样例、边界（长度 1、全相等、全被 mask）、数值稳定（上千的 logits）。

```bash
pip install pyyaml numpy
python3 tools/build.py                                   # 校验并生成 skills/allclose/data/problems.json
python3 skills/allclose/scripts/allclose.py check <id>   # 参考答案必须通过；模板和 wrong.py 里每个写法都必须被抓出来
```

题目要求原创，或者来自许可证允许再分发的项目（在 `problem.yml` 的 `source` 里写明出处）。
「哪家公司考过」只在有面经出处时才加：`companies: [{company: bytedance, source: <面经链接>}]`。
