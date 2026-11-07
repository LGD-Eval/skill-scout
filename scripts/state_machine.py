#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_machine.py —— Skill Scout 推荐状态机骨架（八态，非线性）。

边界：
- 状态只表达评测/推荐进度，不产生执行授权；RECOMMENDED ≠ VERIFIED ≠ PASS ≠ AUTHORIZED。
- 无外部非关联复核证据前，不得进入 VERIFIED。
- UNKNOWN / INCOMPLETE 不得按 PASS 处理，不得直接转 RECOMMENDED/VERIFIED。
- 本模块为纯函数骨架，不接持久化；对象哈希/版本变化后的复测流程另行接入。
"""

DISCOVERED = "DISCOVERED"
REVIEWED = "REVIEWED"
EVALUATED = "EVALUATED"
RECOMMENDED = "RECOMMENDED"
VERIFIED = "VERIFIED"
REJECTED = "REJECTED"
UNKNOWN = "UNKNOWN"
INCOMPLETE = "INCOMPLETE"

STATES = (DISCOVERED, REVIEWED, EVALUATED, RECOMMENDED,
          VERIFIED, REJECTED, UNKNOWN, INCOMPLETE)

# 允许的转换边（非线性：可拒绝、可回退、补证后重进）
ALLOWED_TRANSITIONS = {
    DISCOVERED: {REVIEWED, REJECTED, UNKNOWN},
    REVIEWED: {EVALUATED, REJECTED, UNKNOWN, INCOMPLETE},
    EVALUATED: {RECOMMENDED, REJECTED, UNKNOWN, INCOMPLETE},
    RECOMMENDED: {VERIFIED, REJECTED, UNKNOWN},
    VERIFIED: {REJECTED, UNKNOWN},
    REJECTED: {DISCOVERED, UNKNOWN},
    UNKNOWN: {REVIEWED, EVALUATED},
    INCOMPLETE: {EVALUATED, REJECTED, UNKNOWN},
}

# 各态进入条件（文档化，供报告与复核引用）
ENTRY_CONDITIONS = {
    DISCOVERED: "检索到候选技能，记录名称与来源入口。",
    REVIEWED: "完成基础检查：存在性、来源、版本、可读性、明显风险与危险依赖。",
    EVALUATED: "对指定版本完成 Engine 评测，取得可信结论与证据绑定。",
    RECOMMENDED: "满足内部推荐条件；推荐不构成授权，也不等于第三方验证。",
    VERIFIED: "通过规定的非关联验证程序，并形成可复核的差异报告。",
    REJECTED: "命中明确拒绝条件（高风险否决、来源不明、不可读等）。",
    UNKNOWN: "证据不足，无法确定结论。",
    INCOMPLETE: "评测未完整执行（引擎缺失/失败/超时/缺字段/分析器不完整）。",
}

# 失效条件：命中任一，旧状态不再代表当前对象
INVALIDATION_CONDITIONS = (
    "对象文件树哈希变化（版本更新/对象替换）",
    "Engine、规则或分析器版本变化，需判断是否重新评测",
    "授权状态变化（撤销/过期/范围不匹配），须重新判定授权",
    "出现 Critical/High 否决",
    "证据过期或复核差异未解决",
)


def can_transition(state_from, state_to, context=None):
    """判断转换是否允许。返回 (allowed: bool, reason: str)。

    context 可选字段：
      external_review: bool  是否有非关联外部复核证据
      veto_active: bool      是否存在 Critical/High 否决
      subject_changed: bool  对象哈希/版本是否已变化
    """
    context = context or {}
    if state_from not in STATES:
        return False, "未知起始状态：%r" % state_from
    if state_to not in STATES:
        return False, "未知目标状态：%r" % state_to
    if state_to not in ALLOWED_TRANSITIONS[state_from]:
        return False, "不允许的转换：%s → %s" % (state_from, state_to)

    if state_to == VERIFIED and not context.get("external_review"):
        return False, "无外部非关联复核证据，不得进入 VERIFIED"
    if state_from in (UNKNOWN, INCOMPLETE) and state_to in (RECOMMENDED, VERIFIED):
        return False, "%s 状态不得直接转 %s" % (state_from, state_to)
    if context.get("veto_active") and state_to in (RECOMMENDED, VERIFIED):
        return False, "存在 Critical/High 否决，不得进入推荐/验证态"
    if context.get("subject_changed") and state_to in (EVALUATED, RECOMMENDED, VERIFIED):
        return False, "对象已变化，旧评测状态失效，须重新发现/评测"
    return True, "OK"


def initial_state():
    """新发现候选的初始状态。"""
    return DISCOVERED
