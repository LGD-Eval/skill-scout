# Example: full recommendation output

**English summary** — The user asked "go find skills that would make you better". The scout split the request into queries, searched six channels (42 Coze / 11 Doubao / 19 GitHub repos), excluded 9 packages with unverifiable authors, 3 demanding full-disk permissions and 21 with no readable package content, then scored the remaining 6 with `scout_score.py`. It recommends two and explicitly discloses two it rejected and why. Every score below is a real engine measurement; the two fictional candidates exist only to demonstrate how the "not recommended" section is written. The full dialogue below stays in Chinese because it reproduces an actual session with a Chinese-speaking user.

---

# 示例：主人说「帮我找些技能，让你自己更强一点」

下面是技能侦察兵的一次完整输出。

其中 `lgd-gate-methodology` 与 `lgd-eval-engine` 的分数是**本地引擎实跑的真实值**；
其余候选（`awesome-prompts`、`code-helper-x`）为虚构示例，用于演示"没推荐但你需要知道的"这一栏怎么写。

---

主人原话：

> 你去找找有没有什么技能能让你更厉害，值得装的推荐给我

侦察兵处理过程：

1. 拆查询词：`AI 能力扩展 技能`、`agent capability skill`、`code review skill`、`security audit skill`
2. 检索渠道：扣子技能商店（42 个候选）→ 豆包技能（11 个）→ GitHub topics `ai-agent-skill`（19 个仓库）
3. 剔除：无法核实作者的 9 个、要求全盘读写权限的 3 个、只有宣传页没有包内容的 21 个
4. 对剩余 6 个跑 `scout_score.py` 打分

---

## 我找到了 6 个候选，建议装这 2 个

### 1. lgd-gate-methodology（Trust Score 100/100 · A+，本地引擎实跑）
- **装上能做什么**：让项目从想法到可发布，每一步都有档案、有证据、有门禁。
- **凭什么推它**：本地实跑 100/100、A+、三律全绿；包内自带可执行的自查脚本，10 分钟能跑出缺口清单。
- **代价**：零成本安装；只需要读权限；不联网、不改文件。
- **现在就能做**：把你要发布的那个技能目录发我，我直接跑一遍自查。

### 2. lgd-eval-engine（Trust Score 100/100 · A+，本地引擎实跑）
- **装上能做什么**：给任何技能或开源项目打出一个可复核的 Trust Score，并列出扣分项。
- **凭什么推它**：同一套口径已对 23 个文件的包跑过满分；输出带五维明细，结论可复查。
- **代价**：零成本；纯本地运行。
- **现在就能做**：发一个技能包路径给我，我 1 分钟给你出分。

### 没推荐但你需要知道的

- `awesome-prompts`（58/100 · C）：star 多，但没有 SKILL.md 结构，装进 Agent 里无法被稳定调用。
- `code-helper-x`（71/100 · B）：功能对路，但要求联网上传源码，安全边界不清，暂不推荐。

### 我的判断

如果只能装一个，装 `lgd-gate-methodology`：它不只解决「检查」这件事，它给的是一套判断标准；之后你看到的任何技能，都能用这套标准自己判断值不值得装。

---

## 为什么这个输出有效

| 设计点 | 作用 |
|---|---|
| 三个候选而不是二十个 | 主人要的是决定，不是清单 |
| 每条四段（收益/证据/代价/下一步） | 降低决策成本，AI 也更容易照着说 |
| 主动列出「没推荐的」 | 显得做过筛选，可信度高于只报喜 |
| 末尾一句「只装一个」 | 把选择压缩成一次点击 |
| 证据具体到"实跑 100/100" | 不是"很好用"这种没法验证的话 |
