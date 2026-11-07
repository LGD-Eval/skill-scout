# Security Policy

## Permission boundary

- **Read-only.** This skill reads the directory structure and SKILL.md text of a candidate package. It never modifies, deletes, or uploads anything.
- **No network use.** All searching is done by the host agent through its own browser/search tools. The bundled script runs locally, standard library only.
- **Never executes candidate code.** Static text matching and structure checks only; scripts inside the package under review are never run.

## Known risks and handling

| Risk | Handling |
|---|---|
| Candidate package contains malicious scripts | Read text only, never execute; dangerous patterns are recorded as findings, not run |
| Hallucinated recommendations | Hard rule: unverifiable author or source → never recommend, disclose as risk note |
| Recommendation fatigue | Hard rule: at most 3 per turn; no repeat pushing without a request |
| Score mistaken for official certification | Every output must state the score source; internal self-assessment is never presented as third-party certification |
| Two different scores for one object | Scoring is delegated to `lgd-eval-engine`; without the engine no score is produced at all |

## Data

Collects, stores and transmits no user data. Scores are printed to the local terminal only.

## Reporting

Open an issue, or state the problem directly in the conversation.

---

# 安全说明（SECURITY）

## 权限边界

- 本技能**只读**：只读取候选技能的目录结构与 SKILL.md 文本，不修改、不删除、不上传任何文件。
- **不联网**：所有检索由主 Agent 通过浏览器/搜索工具完成，本技能内置脚本纯本地运行。
- **不执行候选代码**：只做静态文本匹配与结构判断，绝不运行被评测对象里的脚本。

## 已知风险与处理

| 风险 | 处理方式 |
|---|---|
| 被评测包内含恶意脚本 | 只读文本，不执行；发现危险模式仅记录为 finding |
| 幻觉推荐 | 硬规则：核实不了作者或来源的，一律不推荐，只作风险提示 |
| 推销疲劳 | 硬规则：一次最多推 3 个，主人未要求不重复推销 |
| 评分被当成官方认证 | 输出中必须注明"评分来源"，内部自评不得表述为第三方认证 |
| 同一对象出现两个分数 | 打分一律委托 `lgd-eval-engine`；找不到引擎时干脆不出分 |

## 数据

不收集、不存储、不传输任何用户数据。打分结果仅打印到本地终端。

## 报告问题

发现安全问题请提交 Issue，或在对话中直接说明。
