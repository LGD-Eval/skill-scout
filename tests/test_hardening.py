#!/usr/bin/env python3
"""硬ening 负对照：验证 Scout 委托引擎时的失败分类与健壮性。

不依赖真实 LGD 引擎，用临时假 engine 脚本模拟各种返回；可在 CI 本地跑：

    python tests/test_hardening.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE = os.path.join(HERE, "..", "scripts", "scout_score.py")
SCRIPTS = os.path.join(HERE, "..", "scripts")
PY = sys.executable

GOOD_SKILL = """---
name: demo-good
description: 演示
version: 1.0.0
license: MIT
---
# demo
"""

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  " + name)
    else:
        print("  FAIL  " + name + "  " + detail)
        failures.append(name)


def write(path, text, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if binary else "w"
    if binary:
        with open(path, mode) as f:
            f.write(text)
    else:
        with open(path, mode, encoding="utf-8") as f:
            f.write(text)


def _good_report(score=88, grade="B", verdict="PASS", with_tree=True):
    rep = {"score": score, "grade": grade, "verdict": verdict,
           "assessment_outcome": verdict,
           "evidence_grade": "E2", "authorization_status": "NOT_GRANTED",
           "execution_applicability": "NOT_APPLICABLE",
           "execution_decision": "NOT_APPLICABLE", "subject": {},
           "inputs": {"tree_sha256": "sha256:abcdef"}}
    if not with_tree:
        rep["inputs"] = {}
    return rep


def report_engine(path, report=None, code=0, emit=True, bad_json=False):
    """生成一个会按 --report-json 写 Trust Report 的假引擎脚本。"""
    report = report if report is not None else _good_report()
    if bad_json:
        write_code = "open(rp,'w',encoding='utf-8').write('this is { not json')"
    else:
        write_code = "json.dump(%s, open(rp,'w',encoding='utf-8'))" % json.dumps(report)
    body = (
        "import sys, json, os\n"
        "argv = sys.argv[1:]\n"
        "rp = argv[argv.index('--report-json')+1]\n"
        + ("%s\n" % write_code if emit else "")
        + "sys.exit(%d)\n" % code
    )
    write(path, body)


def run_scout(args):
    r = subprocess.run([PY, SCORE] + args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def main():
    with tempfile.TemporaryDirectory() as tmp:
        good = os.path.join(tmp, "good")
        write(os.path.join(good, "SKILL.md"), GOOD_SKILL)

        eng_good = os.path.join(tmp, "eng_good.py")
        report_engine(eng_good)
        eng_exit = os.path.join(tmp, "eng_exit.py")
        report_engine(eng_exit, code=3, emit=False)
        eng_noreport = os.path.join(tmp, "eng_noreport.py")
        report_engine(eng_noreport, emit=False)
        eng_oob = os.path.join(tmp, "eng_oob.py")
        report_engine(eng_oob, report=_good_report(score=150))
        eng_missing = os.path.join(tmp, "eng_missing.py")
        report_engine(eng_missing, report={"grade": "B"})
        eng_notree = os.path.join(tmp, "eng_notree.py")
        report_engine(eng_notree, report=_good_report(with_tree=False))
        eng_badjson = os.path.join(tmp, "eng_badjson.py")
        report_engine(eng_badjson, bad_json=True)
        eng_incomplete = os.path.join(tmp, "eng_incomplete.py")
        report_engine(eng_incomplete, report=_good_report(verdict="INCOMPLETE"))

        print("[非零退出不得出成功分]")
        rc, out, err = run_scout(["--json", "--engine", eng_exit, good])
        try:
            data = json.loads(out)
            r0 = data[0]
            check("退出码 3 判 INCOMPLETE", r0.get("status") == "INCOMPLETE", out[:120])
            check("error_kind=nonzero_exit", r0.get("error_kind") == "nonzero_exit", out[:120])
            check("失败项不含成功 score", "score" not in r0, out[:120])
            check("reason 透传退出码", "3" in r0.get("reason", ""), out[:120])
        except Exception as e:  # noqa: BLE001
            check("JSON 可解析", False, repr(e) + " " + out[:120])

        print("[退出 0 但无报告文件]")
        rc, out, _ = run_scout(["--json", "--engine", eng_noreport, good])
        data = json.loads(out)
        check("error_kind=no_report_json", data[0].get("error_kind") == "no_report_json", out[:120])

        print("[分数越界拒绝]")
        rc, out, _ = run_scout(["--json", "--engine", eng_oob, good])
        data = json.loads(out)
        check("error_kind=score_out_of_range",
              data[0].get("error_kind") == "score_out_of_range", out[:120])

        print("[报告缺必需字段拒绝]")
        rc, out, _ = run_scout(["--json", "--engine", eng_missing, good])
        data = json.loads(out)
        check("error_kind=missing_fields", data[0].get("error_kind") == "missing_fields", out[:120])

        print("[对象未绑定（缺树哈希）拒绝]")
        rc, out, _ = run_scout(["--json", "--engine", eng_notree, good])
        data = json.loads(out)
        check("error_kind=binding_missing", data[0].get("error_kind") == "binding_missing", out[:120])

        print("[报告 JSON 非法拒绝]")
        rc, out, _ = run_scout(["--json", "--engine", eng_badjson, good])
        data = json.loads(out)
        check("error_kind=report_invalid_json",
              data[0].get("error_kind") == "report_invalid_json", out[:120])

        print("[verdict=INCOMPLETE 不出可信分]")
        rc, out, _ = run_scout(["--json", "--engine", eng_incomplete, good])
        data = json.loads(out)
        check("error_kind=verdict_incomplete",
              data[0].get("error_kind") == "verdict_incomplete", out[:120])
        check("INCOMPLETE 项不含成功 score", "score" not in data[0], out[:120])

        print("[混合成功+失败不崩溃、不 KeyError]")
        sys.path.insert(0, SCRIPTS)
        import scout_score  # noqa: E402
        mixed = [
            {"name": "a-good", "status": "EVALUATED", "score": 88, "grade": "B", "path": good},
            {"name": "b-bad", "status": "INCOMPLETE", "verdict": "无法评分",
             "reason": "退出码 3", "error_kind": "nonzero_exit", "source": "engine"},
        ]
        try:
            txt = scout_score.render_engine(mixed)
            check("渲染不抛 KeyError", True, "")
            check("成功项出 88/100", "88/100" in txt, txt[:160])
            check("失败项进 INCOMPLETE 区块", "INCOMPLETE" in txt, txt[:160])
        except Exception as e:  # noqa: BLE001
            check("渲染不抛 KeyError", False, repr(e))
        rc, out, err = run_scout(["--json", "--engine", eng_good, good])
        data = json.loads(out)
        check("CLI 成功项 EVALUATED 出分",
              rc == 0 and len(data) == 1 and data[0]["status"] == "EVALUATED"
              and data[0]["score"] == 88, out[:120])

        print("[引擎路径优先级：explicit > 环境变量]")
        sys.path.insert(0, SCRIPTS)
        import scout_score  # noqa: E402
        env_p = os.path.join(tmp, "env_engine.py")
        exp_p = os.path.join(tmp, "exp_engine.py")
        write(env_p, "# env")
        write(exp_p, "# explicit")
        os.environ["LGD_ENGINE"] = env_p
        got = scout_score.find_engine(explicit=exp_p)
        check("explicit 优先于 LGD_ENGINE", os.path.abspath(got) == os.path.abspath(exp_p), str(got))
        del os.environ["LGD_ENGINE"]

        print("[不可解码文件不崩溃并标记不可读]")
        bad = os.path.join(tmp, "undecodable")
        write(os.path.join(bad, "SKILL.md"), GOOD_SKILL)
        write(os.path.join(bad, "bin.py"), b"\xff\xfe\x00\x01\x02", binary=True)
        rc, out, _ = run_scout(["--json", "--no-engine", bad])
        try:
            data = json.loads(out)
            check("prefilter 返回结论", data[0].get("verdict") in ("可装", "慎用", "别装"), out[:120])
            check("标记存在不可读文件", "不可读" in data[0].get("reason", ""), out[:120])
        except Exception as e:  # noqa: BLE001
            check("JSON 可解析", False, repr(e) + " " + out[:120])

    print()
    if failures:
        print("负对照未通过：" + "、".join(failures))
        return 1
    print("硬ening 负对照全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
