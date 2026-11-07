# LGD Three Laws — Quick Reference

Skill Scout uses these three laws to decide whether a skill or project is worth installing.

## Registered — the record is traceable

- Has a CHANGELOG; every version shows what changed
- Declares authorship and license (frontmatter `author` / `license`)
- Decisions and changes are recorded, not made on impulse

**Ask**: Who made this? What changed in the last version? Who do I talk to when it breaks?

## Evidenced — conclusions carry evidence

- Has tests or measured output, not just marketing copy
- Has a score, case, or report someone else can re-check
- Claims match the code: the advertised feature actually exists

**Ask**: It says it works — where is the evidence? Can I verify it myself?

## Gated — checkpoints exist

- A pre-release checklist exists
- The permission boundary is written down (what it reads, what it writes, whether it uses the network)
- Dangerous operations are blocked or confirmed

**Ask**: What can it touch of mine? Is there a gate before something goes wrong?

## Three hard rules (Skill Scout's operating criteria)

1. Evidence over popularity
2. Unverifiable author / unclear security boundary / excessive permissions → veto
3. Tie-break by verifiability: re-checkable evidence within 10 minutes wins

## Score mapping

The table below explains which law each engine dimension belongs to, so you can explain why a point was deducted.
**Weights and algorithm live in `lgd-eval-engine`'s `evaluate.py`; this file defines no weights of its own** —
one object has exactly one score, so do not compute a second one from this table.

| LGD law | Scoring dimension | Weight |
|---|---|---|
| Registered | Structure + Layout | 25 + 15 |
| Evidenced | Documentation | 20 |
| Gated | Security | 25 |
| Ecosystem | Ecosystem compatibility | 15 |

> Theoretical basis: LGD Three Laws · AI governance standards work (W3C / ITU-T FG-TIDA)

---

# LGD 三律 · 速查

技能侦察兵用这套标准判断一个技能/项目值不值得装。

## 有籍（Registered）— 档案可追溯

- 有 CHANGELOG，每个版本能查到改了什么
- 有作者与许可声明（frontmatter 的 author / license）
- 决策与变更留下记录，不是"凭感觉改的"

**判断问句**：这个技能是谁做的？上一版改了什么？出了问题找谁？

## 有证（Evidenced）— 结论有证据

- 有测试或实测输出，不是只有宣传语
- 有可复核的评分、案例或报告
- 说法与代码能对上（宣传的功能确实存在）

**判断问句**：它说自己好用，证据在哪？我能自己复核一遍吗？

## 有门禁（Gated）— 关键节点有检查

- 发布前有检查清单
- 权限边界写清楚（读什么、写什么、联不联网）
- 危险操作有拦截或确认

**判断问句**：它会碰我的什么东西？出事之前有没有一道闸？

## 三条硬规则（侦察兵执行口径）

1. 证据优先于热度
2. 作者不可确认 / 安全边界不清 / 权限过宽 → 一票否决
3. 同分时比"可验证性"：10 分钟内能跑出结果、能给出可复核证据的优先

## 评分对应关系

下表说明引擎的五个维度分别对应哪条律，用来解释"为什么扣这一分"。
**权重与算法定义在 `lgd-eval-engine` 的 `evaluate.py`，本文件不另定权重**——
同一对象只有一套分数，不要据本表自己算分。

| LGD 三律 | 打分维度 | 权重 |
|---|---|---|
| 有籍 | 结构完整性 + 目录规范 | 25 + 15 |
| 有证 | 文档质量 | 20 |
| 有门禁 | 安全性 | 25 |
| 生态 | 生态兼容 | 15 |

> 理论依据：LGD 三律 · AI 治理标准参与研究（W3C / ITU-T FG-TIDA）
