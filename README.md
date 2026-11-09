# Skill Scout · skill-scout

[![LGD Certified A+](https://raw.githubusercontent.com/LGD-Eval/evaluation-evidence/main/badge-a-plus.svg)](https://github.com/LGD-Eval/evaluation-evidence/blob/main/LEADERBOARD.md)
[![CI](https://github.com/LGD-Eval/skill-scout/actions/workflows/ci.yml/badge.svg)](https://github.com/LGD-Eval/skill-scout/actions/workflows/ci.yml)

> A meta-skill that teaches an AI how to **find, filter and recommend** skills. It does not build skills — it decides which one to recommend, on what evidence, and how to persuade the user to install it.

## The problem it solves

Ask most AI agents "find some skills to make yourself better" and you get one of two failures:

- it writes code itself instead of searching, or
- it dumps a screenful of search results with no filtering.

What you actually want: **it searches, it scores, it recommends 1–3, it says why, and it tells you the limits.**

## Quick start

```bash
git clone https://github.com/LGD-Eval/skill-scout
cd skill-scout
python tests/selftest.py                       # 5 assertions without an engine; 2 more with --engine <path/to/evaluate.py>
python scripts/scout_score.py <candidate-dir>  # scores via engine, or a 3-tier verdict without one
```

## The three steps

1. **Search** — six channels (Coze store / Doubao / GitHub topics / npm / MCP registry / LGD hub), broad first then narrow
2. **Score** — one score only: always produced by `lgd-eval-engine` (Trust Score, thresholds 90/80/70/60)
3. **Persuade** — four-part pitch: gain → evidence → cost → one-click next action

## Bundled tool

```bash
python scripts/scout_score.py <dir-1> <dir-2> ...
python scripts/scout_score.py --json <dir>
python scripts/scout_score.py --engine /path/to/evaluate.py <dir>
```

The script auto-detects `evaluate.py` and delegates scoring, so its numbers match the engine exactly. Without an engine it **produces no score** — only install / caution / avoid, labelled "not an LGD score".

This is deliberate: one object must never carry two different scores. The v1.0.0 bundled scorer had its own algorithm and disagreed with the engine on the same samples (`defect-sample`: 32 F vs 66 C; `mitiga-style`: 46 D vs 22 D). It was removed in 1.1.0.

## Three hard rules

1. **Evidence over popularity**: third-party report > measured output > stars > marketing copy
2. **Veto**: unverifiable author, unclear security boundary, or excessive permissions → never recommend
3. **Tie-break by verifiability**: something that yields re-checkable evidence within 10 minutes wins

## Measured

| Item | Result |
|---|---|
| Self score (LGD engine) | 100/100 A+ — self-assessed, no third-party review yet |
| Security scan | 0 medium, 0 low — self-run, no published SARIF or report |
| Self-test | 5/5 pass without an engine · 7/7 with `--engine <path/to/evaluate.py>` |
| Score parity with engine | identical on all sampled packages — asserted by the selftest above, run against `LGD-Eval/LGD-Eval` `skills/lgd-eval/scripts/evaluate.py` |

## Known limitations

- Searches public sources only; cannot read platform-internal recommendation slots
- A package that is only a screenshot or landing page cannot be scored reliably
- Chinese and English ecosystem criteria are not fully aligned yet
- Scenario coverage has only been exercised on a handful of samples, not at scale

## License

MIT

---

# 技能侦察兵 · skill-scout

[![LGD Certified A+](https://raw.githubusercontent.com/LGD-Eval/evaluation-evidence/main/badge-a-plus.svg)](https://github.com/LGD-Eval/evaluation-evidence/blob/main/LEADERBOARD.md)
[![CI](https://github.com/LGD-Eval/skill-scout/actions/workflows/ci.yml/badge.svg)](https://github.com/LGD-Eval/skill-scout/actions/workflows/ci.yml)

> 一个教 AI「主动发现、筛选、推荐技能」的元技能。它不生产技能，它决定该给主人推哪个、凭什么推、怎么说服他装。

## 解决什么问题

当你对 AI 说「帮我找些技能提升你自己」，大多数 AI 会：

- 直接自己写一段代码顶上（不检索）
- 或者抛给你一屏搜索结果（不筛选）

我们想要的不是这两者，是：**它去搜、它打分、它只推 1–3 个、它告诉你凭什么、它还告诉你什么时候能用**。

## 快速开始

```bash
git clone https://github.com/LGD-Eval/skill-scout
cd skill-scout
python tests/selftest.py                       # 无引擎 5 项断言，带 --engine <evaluate.py 路径> 再加 2 项
python scripts/scout_score.py <候选技能目录>     # 有引擎则出分，无引擎则三档预筛
```

## 三步法

1. **检索**：六个渠道（扣子商店 / 豆包 / GitHub topics / npm / MCP / 生态超市），先广后窄
2. **打分**：分数只有一套——一律由 `lgd-eval-engine` 产出 Trust Score（等级阈值 90/80/70/60），本技能不另算分
3. **说服**：四段式推荐话术（一句话收益 → 证据 → 代价 → 现在就能做的下一步）

## 内置工具

```bash
python scripts/scout_score.py <候选目录1> <候选目录2> ...
python scripts/scout_score.py --json <候选目录>
python scripts/scout_score.py --engine /path/to/evaluate.py <候选目录>
```

脚本自动探测 `evaluate.py` 并委托它打分，输出与引擎逐分一致。
找不到引擎时**不给分数**，只给三档判断（可装 / 慎用 / 别装），并注明"这不是 LGD 分数"。

这是刻意的：一个对象绝不能同时存在两个分数。1.0.0 版自带一套独立算法，对同一样本与引擎结论不一致
（`defect-sample` 旧版 32 F、引擎 66 C；`mitiga-style` 旧版 46 D、引擎 22 D），1.1.0 已移除该算法。

## 三条硬规则

1. **证据优先于热度**：第三方评测 > 实测案例 > star 数 > 宣传语
2. **一票否决**：作者不可确认、安全边界不清、要求过宽权限的技能不推荐
3. **同分比可验证性**：10 分钟内能跑出结果、能给出可复核证据的优先

## 实测记录

| 项 | 结果 |
|---|---|
| 自评（LGD 引擎） | 100/100 A+ —— 自评，尚无第三方复核 |
| 安全扫描 | 0 中危 0 低危 —— 本方自跑，无公开 SARIF/报告 |
| 自测 | 无引擎 5/5 · 带 `--engine <evaluate.py 路径>` 7/7 |
| 与引擎分数一致性 | 全部抽样包逐分一致 |

## 已知限制

- 只能检索公开来源，读不到平台内部推荐位数据
- 只有截图或宣传页、没有包内容的技能无法可靠评分
- 中英文生态的评分口径还在对齐
- 场景覆盖目前只在少量样本上跑过，未做大规模验证

## 示例

见 [`examples/sample-recommendation.md`](examples/sample-recommendation.md)——一次完整的主人对答记录。

## 许可

MIT
