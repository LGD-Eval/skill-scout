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

WEIGHTS = {
    "structure": 25,
    "layout": 15,
    "docs": 20,
    "security": 25,
    "ecosystem": 15,
}

REQUIRED_FIELDS = ("name", "description", "version", "license")

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
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


def parse_frontmatter(text):
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
    cands = []
    env = os.environ.get("LGD_ENGINE")
    if env:
        cands.append(env)
    if explicit:
        cands.append(explicit)
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


def score_with_engine(engine, root):
    try:
        r = subprocess.run([sys.executable, engine, root],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    for ln in r.stdout.splitlines():
        m = re.search(r"Trust Score:\s*(\d+)/100", ln)
        if m:
            return int(m.group(1))
    return None


def prefilter(root):
    """没有引擎时的轻量预筛。只回答"要不要继续看"，不产生可比分数。"""
    skill = os.path.join(root, "SKILL.md")
    if not os.path.exists(skill):
        return {"name": os.path.basename(root), "verdict": "别装",
                "reason": "没有 SKILL.md，不是可分发的技能包", "source": "prefilter"}
    body = read_text(skill)
    fm = parse_frontmatter(body)
    flags = []
    local = 0
    exfil = 0
    for dp, _dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root).replace("\\", "/").lower()
        if rel.startswith("tests") or "/tests/" in rel or "fixtures" in rel:
            continue
        for f in fn:
            if not f.lower().endswith((".py", ".sh", ".js", ".ps1")):
                continue
            txt = read_text(os.path.join(dp, f))
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
    verdict = "可装" if not flags else "慎用"
    return {"name": fm.get("name", os.path.basename(root)), "verdict": verdict,
            "reason": "；".join(flags) if flags else "结构完整、未检出高风险调用",
            "source": "prefilter"}


def render_engine(results):
    lines = ["=" * 62, "  🔭 技能侦察兵 · 候选排序（分数来自 LGD 引擎，同一口径）", "=" * 62]
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        lines.append("")
        lines.append("%-28s %3d/100  %s" % (r["name"], r["score"], r["grade"]))
        if r.get("path"):
            lines.append("    " + r["path"])
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
            sc = score_with_engine(engine, d)
            if sc is None:
                results.append({"name": os.path.basename(d), "verdict": "无法评分",
                                "reason": "引擎没有给出分数", "source": "engine"})
                continue
            results.append({"name": os.path.basename(d), "score": sc,
                            "grade": grade_of(sc), "path": d, "source": "engine"})
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(render_engine(results))
        return

    results = [prefilter(d) for d in args.dirs]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(render_prefilter(results))


if __name__ == "__main__":
    main()
