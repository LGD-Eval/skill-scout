# STRUCTURE — 分层与改动代价

## 三层

| 层 | 文件 | 内容 |
|---|---|---|
| L1 规则 | `references/lgd-three-laws.md` | 有籍 / 有证 / 有门禁三律的判据来源 |
| L2 逻辑 | `scripts/scout_score.py` | 技能检索、过滤、打分、推荐理由生成 |
| L3 检验与分发 | `tests/selftest.py`、`.github/workflows/ci.yml`、`SKILL.md`、`examples/sample-recommendation.md` | 自检、CI、技能声明与样例输出 |

## 改动代价

| 你想做 | 改哪里 | 必须重跑 | 必须同步 |
|---|---|---|---|
| 改三律判据 | `references/lgd-three-laws.md` | `tests/selftest.py` | `SKILL.md` 的判据段 |
| 改打分权重 | `scout_score.py` | 自检 + 一份前后样例对比 | `examples/sample-recommendation.md` |
| 加检索源 | `scout_score.py` | CI | README 的"检索范围" |

## 边界

本仓只回答**推荐哪个、凭什么推荐**；技能本身的安全与质量归 `skillgate`，
变更是否越界归 `lcas`。它不生产技能，也不替代评测。
