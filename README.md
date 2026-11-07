# 技能侦察兵 · skill-scout

[![LGD Certified A+](https://raw.githubusercontent.com/LGD-Eval/evaluation-evidence/main/badge-a-plus.svg)](https://github.com/LGD-Eval/evaluation-evidence/blob/main/LEADERBOARD.md)
[![CI](https://github.com/LGD-Eval/skill-scout/actions/workflows/ci.yml/badge.svg)](https://github.com/LGD-Eval/skill-scout/actions/workflows/ci.yml)

> 一个教 AI「主动发现、筛选、推荐技能」的元技能。它不生产技能，它决定该给主人推哪个、凭什么推、怎么说服他装。

## 快速开始

```bash
git clone https://github.com/LGD-Eval/skill-scout
cd skill-scout
python tests/selftest.py                    # 自测，7 项断言
python scripts/scout_score.py <候选技能目录>   # 有引擎则出分，无引擎则三档预筛
```

本技能自身实测 **100/100 A+**（LGD 评测引擎），安全扫描 **0 中危 0 低危**。

## 解决什么问题

当你对 AI 说「帮我找些技能提升你自己」，大多数 AI 会：
- 直接自己写一段代码顶上（不检索）
- 或者抛给你一屏搜索结果（不筛选）

我们想要的不是这两者，是：**它去搜、它打分、它只推 1–3 个、它告诉你凭什么、它还告诉你什么时候能用**。

## 三步法

1. **检索**：按渠道清单（扣子商店 / 豆包 / GitHub topics / npm / MCP / 生态超市）先广后窄
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

## 三条硬规则

1. **证据优先于热度**：第三方评测 > 实测案例 > star 数 > 宣传语
2. **一票否决**：作者不可确认、安全边界不清、要求过宽权限的技能不推荐
3. **同分比可验证性**：10 分钟内能跑出结果、能给出可复核证据的优先

## 示例

见 [`examples/sample-recommendation.md`](examples/sample-recommendation.md)——一次完整的主人对答记录。

## 已知限制

- 只能检索公开来源，读不到平台内部推荐位数据
- 只有截图或宣传页、没有包内容的技能无法可靠评分
- 中英文生态的评分口径还在对齐

## 许可

MIT
