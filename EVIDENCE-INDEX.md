# EVIDENCE-INDEX — skill-scout

## 现状

| 级 | 结果 | 证据位置 | 说明 |
|---|---|---|---|
| L1 自我复现 | **有** | `tests/selftest.py`、`.github/workflows/ci.yml`、`scripts/scout_score.py` | 自检脚本可跑，CI 每次 push 执行 |
| L2 异体审查 | **0** | — | 无外部审查记录 |
| L3 第二实现 | **0** | — | 无独立实现 |
| L3.5 外部语料 | **0** | `examples/sample-recommendation.md` 是示例，不是实跑记录 | |
| L4 外部节点 | **0** | — | 无第三方使用证据 |

## 已知不硬的地方

1. **徽章是自评。** README 顶部 `LGD Certified A+ · self-assessed` 指向 `LGD-Eval/evaluation-evidence` 的 badge 图，虽然写了 `self-assessed`，但图形形态与"认证"极像，**引用时不得省略 self-assessed 字样**。
2. **评分逻辑只有一份实现。** `scout_score.py` 的权重没有第二套实现或人工标注对照，权重是否合理无法被外部检验。
3. **"推荐"这件事没有对照实验。** 没有"用它 vs 不用它"的推荐质量对比记录，因此不能声称推荐更准。

## 维护约定

- 调整打分权重 → 附一份前后对比样例 → 更新本表 L1 行。
- 任何"推荐效果"表述必须附对照条件，否则删除。
- 等级只降不升。
