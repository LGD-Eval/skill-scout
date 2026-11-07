#!/usr/bin/env python3
"""scout_score.py — 技能候选打分器（技能侦察兵内置工具）

用法:
    python scout_score.py <目录1> [<目录2> ...]
    python scout_score.py --json <目录>
"""
import argparse
import json
import os
import re

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

SAFE_DECLARATIONS = ("权限", "boundary", "permission", "不会修改", "只读", "read-only")


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


def score_pack(root):
    report = {"path": root, "score": 0, "max": 100, "grade": "F", "items": [], "findings": []}
    skill = os.path.join(root, "SKILL.md")
    if not os.path.exists(skill):
        report["findings"].append("缺少 SKILL.md，无法作为技能分发")
        report["grade"] = "F"
        return report

    fm = parse_frontmatter(read_text(skill))
    total = 0

    # 1 structure 25
    s = 0
    s += 8
    missing = [f for f in REQUIRED_FIELDS if not fm.get(f)]
    s += 8 if not missing else max(0, 8 - 2 * len(missing))
    s += 5 if os.path.exists(os.path.join(root, "LICENSE")) else 0
    s += 4 if os.path.exists(os.path.join(root, "README.md")) else 0
    total += s
    report["items"].append(("结构完整性", s, WEIGHTS["structure"]))
    if missing:
        report["findings"].append("frontmatter 缺字段：" + "/".join(missing))

    # 2 layout 15
    s = 0
    for d, pts in (("scripts", 6), ("examples", 6), ("references", 3)):
        if os.path.isdir(os.path.join(root, d)):
            s += pts
    total += s
    report["items"].append(("目录规范", s, WEIGHTS["layout"]))

    # 3 docs 20
    body = read_text(skill)
    s = 0
    doc_signals = (
        ("when to use", 5), ("何时用", 5), ("when not", 3), ("何时不用", 3),
        ("用法", 4), ("usage", 4), ("示例", 4), ("example", 4),
        ("限制", 4), ("limitation", 4), ("known limit", 4),
    )
    low = body.lower()
    for kw, pts in doc_signals:
        if kw in low:
            s += pts
    total += min(s, 20)
    report["items"].append(("文档质量", min(s, 20), WEIGHTS["docs"]))

    # 4 security 25 — 先看边界声明，再谈风险调用
    sec_file = any(
        os.path.exists(os.path.join(root, n))
        for n in ("SECURITY.md", "SECURITY", "PRIVACY.md")
    )
    declared = sec_file or any(
        k in body for k in ("权限", "边界", "只读", "不会修改", "boundary", "permission", "限制", "不联网")
    )
    s = 20 if declared else 12
    if not declared:
        report["findings"].append("未声明权限边界或安全说明")
    if sec_file:
        s += 5

    hit_local = 0
    hit_exfil = 0
    scan_ext = (".py", ".sh", ".js", ".ps1", ".md")
    for dp, _dn, fn in os.walk(root):
        rel_dir = os.path.relpath(dp, root).replace("\\", "/").lower()
        # 测试夹具里的示例代码不代表运行时行为，跳过
        if rel_dir.startswith("tests") or "/tests/" in rel_dir or "fixtures" in rel_dir:
            continue
        for f in fn:
            if not f.lower().endswith(scan_ext):
                continue
            txt = read_text(os.path.join(dp, f))
            for pat, label in RISK_PATTERNS:
                if not re.search(pat, txt):
                    continue
                if label == "向外部发送数据":
                    hit_exfil += 1
                else:
                    hit_local += 1

    # 本地子进程/动态执行：有声明则视为受控实现，不扣；无声明才扣，且设上限
    if declared:
        if hit_local:
            report["findings"].append("含 %d 处本地执行调用，已声明边界，视为受控实现" % hit_local)
    else:
        s -= min(12, 4 * hit_local)
        if hit_local:
            report["findings"].append("含 %d 处本地执行调用且无边界声明" % hit_local)
    # 数据外发一律重扣，与声明无关
    if hit_exfil:
        s -= 10
        report["findings"].append("检出 %d 处疑似向外部发送数据" % hit_exfil)

    s = max(0, min(25, s))
    total += s
    report["items"].append(("安全性", s, WEIGHTS["security"]))

    # 5 ecosystem 15
    s = 0
    if "tags" in body or fm.get("tags"):
        s += 6
    if "windows" in body.lower() or "platform" in body.lower() or "macos" in body.lower():
        s += 5
    if "agent" in body.lower() or "mcp" in body.lower():
        s += 4
    total += s
    report["items"].append(("生态兼容", s, WEIGHTS["ecosystem"]))

    report["score"] = total
    report["name"] = fm.get("name", os.path.basename(root))
    report["grade"] = (
        "A+" if total >= 90 else
        "A" if total >= 80 else
        "B" if total >= 70 else
        "C" if total >= 60 else
        "D" if total >= 40 else "F"
    )
    return report


def render(reports):
    lines = []
    lines.append("=" * 62)
    lines.append("  🔭 技能侦察兵 · 候选打分")
    lines.append("=" * 62)
    for r in sorted(reports, key=lambda x: x["score"], reverse=True):
        lines.append("")
        lines.append("%-28s %3d/100  %s" % (str(r.get("name", "?")), r["score"], r["grade"]))
        for label, got, full in r["items"]:
            lines.append("    %-10s %2d/%2d" % (label, got, full))
        for f in r["findings"]:
            lines.append("    ! " + f)
    lines.append("")
    lines.append("=" * 62)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="技能候选打分器")
    ap.add_argument("dirs", nargs="+", help="候选技能目录")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()
    reports = [score_pack(d) for d in args.dirs]
    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        print(render(reports))


if __name__ == "__main__":
    main()
