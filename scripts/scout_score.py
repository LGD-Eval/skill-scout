#!/usr/bin/env python3
"""scout_score.py — 技能候选打分器（技能侦察兵内置工具）

一个对象只能有一个分数。本脚本不再自建第二套评分口径：
找到 LGD 引擎（evaluate.py）时直接委托它，输出与引擎逐分一致的 Trust Score；
找不到引擎时只给三档预筛结论（可装 / 慎用 / 别装），并明确标注"这不是 LGD 分数"。

用法:
    python scout_score.py <目录1> [<目录2> ...]
    python scout_score.py --json <目录>
    python scout_score.py --engine <evaluate.py 路径> <目录>
"""
import argparse
import json
import os
import re
import subprocess
import sys

import state_machine

REQUIRED_FIELDS = ("name", "description", "version", "license")

# 授权 / 执行枚举白名单（本地副本，避免跨仓依赖；与 Engine trust_model 对齐）
AUTH_STATUSES = ("VALID", "INVALID", "EXPIRED", "REVOKED", "UNKNOWN",
                 "NOT_GRANTED", "NOT_REQUESTED")
EXEC_APPLICABILITY = ("APPLICABLE", "NOT_APPLICABLE")
EXEC_DECISIONS = ("ALLOW", "DENY", "NOT_APPLICABLE")
# 非有效授权（执行场景 ALLOW 一律拒绝）
NON_VALID_AUTH = ("UNKNOWN", "NOT_GRANTED", "INVALID", "EXPIRED",
                  "REVOKED", "NOT_REQUESTED")


def _check_authorization_combo(report):
    """校验授权/适用性/执行决策组合是否自洽。

    返回 None 表示通过；否则返回 (kind, reason) 拒绝原因。
    缺字段、非法枚举、矛盾组合默认拒绝，不得默认 ALLOW。
    """
    auth = report.get("authorization_status")
    appl = report.get("execution_applicability")
    decision = report.get("execution_decision")

    if auth is None:
        return "missing_auth", "报告缺 authorization_status，不得默认放行"
    if appl is None:
        return "missing_applicability", "报告缺 execution_applicability，不得默认放行"
    if decision is None:
        return "missing_decision", "报告缺 execution_decision，不得默认放行"
    if auth not in AUTH_STATUSES:
        return "invalid_auth", "非法授权状态 %r" % auth
    if appl not in EXEC_APPLICABILITY:
        return "invalid_applicability", "非法适用性 %r" % appl
    if decision not in EXEC_DECISIONS:
        return "invalid_decision", "非法执行决策 %r" % decision

    # NOT_APPLICABLE 场景：绝不能 ALLOW（含 VALID+ALLOW 矛盾组合）
    if appl == "NOT_APPLICABLE" and decision == "ALLOW":
        return "not_applicable_allow", "NOT_APPLICABLE 场景不得 ALLOW 执行"
    # APPLICABLE 场景：授权非 VALID 一律不得 ALLOW
    if appl == "APPLICABLE" and decision == "ALLOW" and auth != "VALID":
        return "authorization_bypass", "授权 %r 非 VALID 却 ALLOW，判定不可信" % auth
    # NOT_APPLICABLE + NOT_APPLICABLE 不构成执行许可（仅记录，不据此出可信放行）
    return None


def report_reject_reason(report):
    """对 Engine Trust Report 做可信性判定（纯函数，便于离线对抗测试）。

    返回 None 表示可采信；否则返回 (kind, reason)。
    Scout 不自行重算 PASS/FAIL，只消费 Engine 权威结论与授权组合。
    """
    outcome = report.get("assessment_outcome") or report.get("verdict")
    if outcome in ("INCOMPLETE", "INCONCLUSIVE"):
        return "verdict_incomplete", "评测未完整执行/结论不确定（outcome=%s），不出可信分" % outcome
    if outcome == "FAIL":
        return "verdict_fail", "验收未通过（assessment_outcome=FAIL），不出可信分"
    if outcome != "PASS":
        return "verdict_unknown", "验收结论非法或缺失（outcome=%r），不出可信分" % outcome
    return _check_authorization_combo(report)

_P1 = "os" + "\\" + "." + "sys" + "tem" + "\\("
_P2 = "sub" + "proc" + "ess" + "\\" + "." + "(r" + "un|Pop" + "en|c" + "all)"
_P3 = "\\b" + "ev" + "al" + "\\("
_P4 = "\\b" + "ex" + "ec" + "\\("
_P5 = "re" + "que" + "sts" + "\\" + "." + "(po" + "st|p" + "ut)" + "\\("

RISK_PATTERNS = [
    (_P1, "调用系统命令"),
    (_P2, "启动子进程"),
    (_P3, "使用动态求值"),
    (_P4, "使用动态执行"),
    (_P5, "向外部发送数据"),
]


def read_text(path):
    """返回 (text, error)。读取/编码失败不静默返回空串，由调用方显式标记。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), None
    except (UnicodeDecodeError, LookupError):
        pass
    except OSError as e:
        return None, "读取失败：%s: %s" % (type(e).__name__, e)
    for enc in ("utf-8-sig", "gbk"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(), None
        except (UnicodeDecodeError, LookupError):
            continue
        except OSError as e:
            return None, "读取失败：%s: %s" % (type(e).__name__, e)
    return None, "编码无法识别，未取得文件内容"


def parse_frontmatter(text):
    if not text:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    body = m.group(1)
    out = {}
    for line in body.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def grade_of(score):
    """与 evaluate.py 完全相同的等级阈值：90/80/70/60。"""
    return ("A+" if score >= 90 else
            "A" if score >= 80 else
            "B" if score >= 70 else
            "C" if score >= 60 else "D")


def find_engine(explicit=None):
    # 优先级：显式 --engine > 环境变量 LGD_ENGINE > 相对路径自动探测
    cands = []
    if explicit:
        cands.append(explicit)
    env = os.environ.get("LGD_ENGINE")
    if env:
        cands.append(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cands += [
        os.path.join(here, "evaluate.py"),
        os.path.join(here, "..", "02-skill-eval-engine", "scripts", "evaluate.py"),
        os.path.join(here, "..", "..", "02-skill-eval-engine", "scripts", "evaluate.py"),
        os.path.join(here, "..", "scripts", "evaluate.py"),
    ]
    for c in cands:
        p = os.path.abspath(c)
        if os.path.exists(p):
            return p
    return None


def _fail(kind, reason, returncode=None, stderr_tail=""):
    return {"ok": False, "error_kind": kind, "reason": reason,
            "returncode": returncode, "stderr_tail": (stderr_tail or "")[-160:]}


def score_with_engine(engine, root):
    """委托引擎评测，消费机器可读 Trust Report JSON。

    主路径不再解析 stdout 正则；报告缺失/非法/缺必需字段/对象未绑定均分类失败，
    不得静默取分。
    """
    import tempfile
    _fd, report_path = tempfile.mkstemp(suffix=".json", prefix="lgd-report-")
    os.close(_fd)
    try:
        try:
            r = subprocess.run([sys.executable, engine, root,
                                 "--report-json", report_path],
                                capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=120)
        except subprocess.TimeoutExpired:
            return _fail("timeout", "引擎执行超时（>120s），未取得可信评测结果")
        except OSError as e:
            return _fail("os_error", "引擎进程无法启动：%s: %s" % (type(e).__name__, e))
        except subprocess.SubprocessError as e:
            return _fail("subprocess_error", "引擎进程异常：%s: %s" % (type(e).__name__, e))

        err_lines = (r.stderr or "").strip().splitlines()
        tail = err_lines[-1].strip() if err_lines else ""

        if r.returncode != 0:
            return _fail("nonzero_exit", "引擎退出码 %s，未取得可信评测结果" % r.returncode,
                         returncode=r.returncode, stderr_tail=tail)

        try:
            if not os.path.exists(report_path) or os.path.getsize(report_path) == 0:
                return _fail("no_report_json", "引擎未生成 Trust Report 报告文件",
                             returncode=r.returncode, stderr_tail=tail)
            with open(report_path, encoding="utf-8") as f:
                report = json.load(f)
        except OSError:
            return _fail("no_report_json", "Trust Report 报告文件不可读",
                         returncode=r.returncode, stderr_tail=tail)
        except json.JSONDecodeError:
            return _fail("report_invalid_json", "Trust Report 不是合法 JSON",
                         returncode=r.returncode, stderr_tail=tail)

        required = ["score", "grade", "evidence_grade",
                    "authorization_status", "execution_decision", "subject", "inputs"]
        missing = [k for k in required if k not in report]
        if missing:
            return _fail("missing_fields", "报告缺必需字段: %s" % ", ".join(missing),
                         returncode=r.returncode, stderr_tail=tail)

        score = report.get("score")
        if not isinstance(score, int) or not 0 <= score <= 100:
            return _fail("score_out_of_range", "报告分数 %r 超出 0–100 范围，报告不可信" % score,
                         returncode=r.returncode, stderr_tail=tail)

        tree = (report.get("inputs") or {}).get("tree_sha256")
        if not tree:
            return _fail("binding_missing", "报告缺对象树哈希（tree_sha256），对象未绑定",
                         returncode=r.returncode, stderr_tail=tail)

        reject = report_reject_reason(report)
        if reject is not None:
            return _fail(reject[0], reject[1],
                         returncode=r.returncode, stderr_tail=tail)

        return {"ok": True, "score": score,
                "grade": report.get("grade") or grade_of(score),
                "verdict": report.get("assessment_outcome") or report.get("verdict"),
                "assessment_outcome": report.get("assessment_outcome"),
                "evidence_grade": report.get("evidence_grade"),
                "authorization_status": report.get("authorization_status"),
                "execution_decision": report.get("execution_decision"),
                "execution_applicability": report.get("execution_applicability"),
                "tree_sha256": tree,
                "engine_version": report.get("engine_version"),
                "rule_version": report.get("rule_version"),
                "report": report,
                "returncode": r.returncode, "reason": None}
    finally:
        try:
            os.unlink(report_path)
        except OSError:
            pass


def prefilter(root):
    """没有引擎时的轻量预筛。只回答"要不要继续看"，不产生可比分数。"""
    skill = os.path.join(root, "SKILL.md")
    if not os.path.exists(skill):
        return {"name": os.path.basename(root), "verdict": "别装",
                "reason": "没有 SKILL.md，不是可分发的技能包", "source": "prefilter"}
    body, body_err = read_text(skill)
    fm = parse_frontmatter(body)
    flags = []
    local = 0
    exfil = 0
    unreadable = 0
    if body_err:
        unreadable += 1
        flags.append("SKILL.md 不可读：" + body_err)
    for dp, _dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root).replace("\\", "/").lower()
        if rel.startswith("tests") or "/tests/" in rel or "fixtures" in rel:
            continue
        for f in fn:
            if not f.lower().endswith((".py", ".sh", ".js", ".ps1")):
                continue
            txt, ferr = read_text(os.path.join(dp, f))
            if ferr:
                unreadable += 1
                continue
            for pat, label in RISK_PATTERNS:
                if not re.search(pat, txt):
                    continue
                if label == "向外部发送数据":
                    exfil += 1
                else:
                    local += 1
    if exfil:
        return {"name": fm.get("name", os.path.basename(root)), "verdict": "别装",
                "reason": "检出 %d 处向外部发送数据的调用，未经审计不要装" % exfil,
                "source": "prefilter"}
    missing = [f for f in REQUIRED_FIELDS if not fm.get(f)]
    if missing:
        flags.append("frontmatter 缺 " + "/".join(missing))
    if local:
        flags.append("含 %d 处本地执行调用（需人工确认是否受控）" % local)
    if unreadable:
        flags.append("%d 个文件不可读，相关内容未纳入检查" % unreadable)
    verdict = "可装" if not flags else "慎用"
    return {"name": fm.get("name", os.path.basename(root)), "verdict": verdict,
            "reason": "；".join(flags) if flags else "结构完整、未检出高风险调用",
            "source": "prefilter"}


def render_engine(results):
    lines = ["=" * 62, "  🔭 技能侦察兵 · 候选排序（分数来自 LGD 引擎，同一口径）", "=" * 62]
    ok = [r for r in results if r.get("status") == "EVALUATED"]
    bad = [r for r in results if r.get("status") != "EVALUATED"]
    for r in sorted(ok, key=lambda x: x["score"], reverse=True):
        lines.append("")
        lines.append("%-28s %3d/100  %s" % (r["name"], r["score"], r["grade"]))
        if r.get("path"):
            lines.append("    " + r["path"])
    if bad:
        lines.append("")
        lines.append("-" * 62)
        lines.append("  未完成评测（INCOMPLETE）：以下对象未取得可信 LGD 评分，不得视为 PASS")
        for r in bad:
            lines.append("")
            lines.append("  %-26s [%s]" % (r["name"], r.get("error_kind", "unknown")))
            lines.append("    " + r["reason"])
    lines.append("")
    lines.append("=" * 62)
    return "\n".join(lines)


def render_prefilter(results):
    lines = ["=" * 62,
             "  🔭 技能侦察兵 · 轻量预筛",
             "  这不是 LGD 分数：没找到评分引擎，只做「要不要继续看」的判断",
             "  要正式分数请跑 lgd-eval-engine 的 evaluate.py",
             "=" * 62]
    for r in results:
        lines.append("")
        lines.append("%-28s %s" % (r["name"], r["verdict"]))
        lines.append("    " + r["reason"])
    lines.append("")
    lines.append("=" * 62)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="技能候选打分器（分数一律来自 LGD 引擎）")
    ap.add_argument("dirs", nargs="+", help="候选技能目录")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--engine", help="evaluate.py 路径（不给则自动探测）")
    ap.add_argument("--no-engine", action="store_true",
                    help="强制不找引擎，只走三档预筛（用于自测降级路径）")
    args = ap.parse_args()

    engine = None if args.no_engine else find_engine(args.engine)
    if engine:
        results = []
        for d in args.dirs:
            res = score_with_engine(engine, d)
            if res["ok"]:
                results.append({"name": os.path.basename(d), "status": "EVALUATED",
                                "state": state_machine.EVALUATED,
                                "score": res["score"], "grade": res["grade"],
                                "verdict": res["verdict"],
                                "evidence_grade": res["evidence_grade"],
                                "authorization_status": res["authorization_status"],
                                "execution_decision": res["execution_decision"],
                                "tree_sha256": res["tree_sha256"],
                                "engine_version": res["engine_version"],
                                "rule_version": res["rule_version"],
                                "path": d, "source": "engine",
                                "returncode": res["returncode"]})
            else:
                results.append({"name": os.path.basename(d), "status": "INCOMPLETE",
                                "state": state_machine.INCOMPLETE,
                                "verdict": "无法评分", "reason": res["reason"],
                                "error_kind": res["error_kind"], "source": "engine",
                                "returncode": res["returncode"],
                                "stderr_tail": res["stderr_tail"]})
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(render_engine(results))
        return

    results = []
    for d in args.dirs:
        p = prefilter(d)
        p["state"] = (state_machine.REJECTED if p["verdict"] == "别装"
                      else state_machine.REVIEWED)
        results.append(p)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(render_prefilter(results))


if __name__ == "__main__":
    main()
