#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""状态机负对照：八态转换规则、进入/禁止条件（离线，不依赖引擎）。

可在 CI 本地跑：
    python tests/test_state_machine.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
sys.path.insert(0, SCRIPTS)

import state_machine as sm  # noqa: E402

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  " + name)
    else:
        print("  FAIL  " + name + "  " + detail)
        failures.append(name)


def allowed(frm, to, ctx=None):
    ok, _ = sm.can_transition(frm, to, ctx)
    return ok


def main():
    print("[允许的正常转换]")
    check("DISCOVERED -> REVIEWED", allowed(sm.DISCOVERED, sm.REVIEWED))
    check("REVIEWED -> EVALUATED", allowed(sm.REVIEWED, sm.EVALUATED))
    check("EVALUATED -> RECOMMENDED",
          allowed(sm.EVALUATED, sm.RECOMMENDED, {"veto_active": False}))
    check("UNKNOWN -> REVIEWED（补证后）", allowed(sm.UNKNOWN, sm.REVIEWED))
    check("INCOMPLETE -> EVALUATED（补齐重评）", allowed(sm.INCOMPLETE, sm.EVALUATED))

    print("[无外部复核不得 VERIFIED]")
    check("EVALUATED -> VERIFIED 无复核拒绝",
          not allowed(sm.EVALUATED, sm.VERIFIED, {"external_review": False}))
    check("RECOMMENDED -> VERIFIED 无复核拒绝",
          not allowed(sm.RECOMMENDED, sm.VERIFIED))
    check("有复核才允许 VERIFIED",
          allowed(sm.RECOMMENDED, sm.VERIFIED, {"external_review": True}))

    print("[UNKNOWN / INCOMPLETE 不得直接进推荐/验证]")
    check("UNKNOWN -> RECOMMENDED 拒绝", not allowed(sm.UNKNOWN, sm.RECOMMENDED))
    check("INCOMPLETE -> VERIFIED 拒绝", not allowed(sm.INCOMPLETE, sm.VERIFIED))

    print("[否决与对象变更阻断推荐/验证]")
    check("veto_active 时 EVALUATED -> RECOMMENDED 拒绝",
          not allowed(sm.EVALUATED, sm.RECOMMENDED, {"veto_active": True}))
    check("subject_changed 时 EVALUATED -> RECOMMENDED 拒绝",
          not allowed(sm.EVALUATED, sm.RECOMMENDED, {"subject_changed": True}))

    print("[非法状态与非法边]")
    check("未知起始状态拒绝", not allowed("NOPE", sm.REVIEWED))
    check("未知目标状态拒绝", not allowed(sm.DISCOVERED, "NOPE"))
    check("REJECTED -> VERIFIED 非法边", not allowed(sm.REJECTED, sm.VERIFIED))
    check("VERIFIED -> DISCOVERED 非法边", not allowed(sm.VERIFIED, sm.DISCOVERED))

    print("[状态集完整]")
    check("八态齐全", len(sm.STATES) == 8 and len(set(sm.STATES)) == 8)
    check("每态都有进入条件说明", all(sm.ENTRY_CONDITIONS.get(s) for s in sm.STATES))

    print()
    if failures:
        print("状态机负对照未通过：" + "、".join(failures))
        return 1
    print("状态机负对照全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
