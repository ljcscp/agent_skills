#!/usr/bin/env python3
"""
Architecture constraint validator for situation-goal-solver skill.

Validates:
1. SKILL.md exists and has required frontmatter
2. All referenced files exist
3. L1-core has required sections
4. L2 strategies follow correct format
5. L3 rules are well-formed
6. No cross-layer contamination (L1 in L2 files, etc.)
"""

import os
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "SKILL.md",
    "references/l1-core.md",
    "references/l2-strategies.md",
    "references/l3-onetime.md",
    "references/exploration-mode.md",
    "references/error-recovery.md",
]

L1_REQUIRED_SECTIONS = [
    "触发规则",
    "执行流程",
    "方向确认驱动循环",
    "方向确认节点",
    "追问策略选择",
    "输出结构",
]

L2_REQUIRED_SECTIONS = [
    "策略的挂载与摘除",
]

L3_REQUIRED_SECTIONS = [
    "冲突解决",
    "生命周期",
]

EXPLORATION_REQUIRED = [
    "触发条件",
    "核心规则",
    "输出格式",
]

ERROR_RECOVERY_REQUIRED = [
    "错误恢复表",
    "自我检查清单",
    "常见陷阱",
]

PASSED = 0
FAILED = 0
WARNINGS = 0


def ok(msg: str):
    global PASSED
    PASSED += 1
    print(f"  ✅ {msg}")


def fail(msg: str):
    global FAILED
    FAILED += 1
    print(f"  ❌ {msg}")


def warn(msg: str):
    global WARNINGS
    WARNINGS += 1
    print(f"  ⚠️  {msg}")


def check_file_exists(rel_path: str) -> bool:
    path = SKILL_DIR / rel_path
    if path.exists():
        ok(f"{rel_path} exists")
        return True
    else:
        fail(f"{rel_path} MISSING")
        return False


def read_file(rel_path: str) -> str:
    path = SKILL_DIR / rel_path
    return path.read_text(encoding="utf-8")


def validate_frontmatter():
    """Validate SKILL.md frontmatter."""
    print("\n--- SKILL.md Frontmatter ---")
    content = read_file("SKILL.md")

    if not content.startswith("---"):
        fail("SKILL.md does not start with frontmatter (---)")
        return

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        fail("Cannot parse frontmatter")
        return

    fm = match.group(1)
    ok("Frontmatter block found")

    # version check
    ver_match = re.search(r"version:\s*(\S+)", fm)
    if ver_match:
        ver = ver_match.group(1)
        ok(f"version: {ver}")
        if not ver.startswith("4."):
            warn(f"Version {ver} — expected 4.x")
    else:
        fail("No version field in frontmatter")

    # name check
    if "name: situation-goal-solver" in fm:
        ok("name: situation-goal-solver")
    else:
        fail("Missing or wrong 'name' field")


def validate_l1():
    """Validate L1 core skeleton."""
    print("\n--- L1 Core ---")
    content = read_file("references/l1-core.md")

    for section in L1_REQUIRED_SECTIONS:
        if section in content:
            ok(f"Section: {section}")
        else:
            fail(f"Missing section: {section}")

    # Check direction confirmation node format
    if "方向对吗？有什么需要纠正的" in content:
        ok("方向确认节点 format found")
    else:
        fail("Missing 方向确认节点 format template")

    # Check skip condition
    if "跳过条件" in content or "跳过本轮方向确认" in content:
        ok("跳过条件 present")
    else:
        fail("Missing 跳过条件 for direction check")

    # Check three validation types
    counts = {
        "可验证（搜索/数据）": content.count("可验证（搜索/数据）"),
        "可验证（逻辑推演）": content.count("可验证（逻辑推演）"),
        "未经搜索验证": content.count("未经搜索验证"),
    }
    for vtype, count in counts.items():
        if count > 0:
            ok(f"Validation type: {vtype}")
        else:
            fail(f"Missing validation type: {vtype}")

    # Check option comparison vs hypothesis test distinction
    if "选项对比" in content and "假设测试" in content:
        ok("Both 选项对比 and 假设测试 present")
    else:
        fail("Missing 选项对比 or 假设测试 template")

    # Must NOT contain confidence % self-rating (as active rule)
    # Allow mentions in changelog lines (prefixed with ❌ "不再使用")
    for line in content.split("\n"):
        stripped = line.strip()
        if "自评信心" in stripped or "信心：__%" in stripped:
            # Skip if it's a changelog line saying "no longer used"
            if "不再使用" in stripped or stripped.startswith("❌") or stripped.startswith("- ❌"):
                continue
            fail(f"v4.0 confidence self-rating leaked into L1: {stripped[:60]}")
            break
    else:
        ok("No v4.0 confidence self-rating contamination")

    # Check strategy confirmation rule
    if "策略确认" in content:
        ok("策略确认 rule present")
    else:
        fail("Missing 策略确认 (strategy misdetection fallback)")


def validate_l2():
    """Validate L2 strategies."""
    print("\n--- L2 Strategies ---")
    content = read_file("references/l2-strategies.md")

    for section in L2_REQUIRED_SECTIONS:
        if section in content:
            ok(f"Section: {section}")
        else:
            fail(f"Missing section: {section}")

    # Check all 5 strategies present
    strategies = [f"策略 {i}" for i in range(5)]
    for s in strategies:
        if s in content:
            ok(f"{s} present")
        else:
            fail(f"Missing {s}")

    # Check memory reading notification rule
    if "记忆读取" in content or "通知用户" in content:
        ok("记忆读取通知 rule present")
    else:
        fail("Missing 记忆读取 notification rule")

    # Check strategy 3 bug recording template
    if "踩坑记录" in content:
        ok("踩坑记录 template (Strategy 3) present")
    else:
        warn("No 踩坑记录 template in Strategy 3")

    # Check "换策略" shortcut
    if "换策略" in content:
        ok("换策略 fallback present")
    else:
        fail("Missing '换策略' immediate fallback rule")


def validate_l3():
    """Validate L3 disposable rules."""
    print("\n--- L3 Disposable Rules ---")
    content = read_file("references/l3-onetime.md")

    for section in L3_REQUIRED_SECTIONS:
        if section in content:
            ok(f"Section: {section}")
        else:
            fail(f"Missing section: {section}")

    # Check conflict resolution mentions user choice
    if "冲突" in content:
        ok("冲突解决 rule present")
    else:
        fail("Missing 冲突解决 rule")

    # Check task end definition
    if "新任务" in content and "任务结束" in content:
        ok("任务结束边界 defined")
    else:
        fail("Missing 任务结束 boundary definition")

    # Check L3 can override L2
    if "L2 恢复原样" in content or "临时覆盖" in content:
        ok("L3→L2 override rule present")
    else:
        fail("Missing L3 can temporarily override L2 rule")


def validate_exploration():
    """Validate exploration mode."""
    print("\n--- Exploration Mode ---")
    content = read_file("references/exploration-mode.md")

    for section in EXPLORATION_REQUIRED:
        if section in content:
            ok(f"Section: {section}")
        else:
            fail(f"Missing section: {section}")

    # Light vs full version
    if "简单探索版" in content or "轻量" in content:
        ok("Light exploration version present")
    else:
        warn("No light exploration version — may over-engineer simple questions")


def validate_error_recovery():
    """Validate error recovery & appendix."""
    print("\n--- Error Recovery ---")
    content = read_file("references/error-recovery.md")

    for section in ERROR_RECOVERY_REQUIRED:
        if section in content:
            ok(f"Section: {section}")
        else:
            fail(f"Missing section: {section}")

    # Check both 假设测试 AND 选项对比 in traps
    if "假设测试" in content and "选项对比" in content:
        ok("假设测试/选项对比 distinction in traps")
    else:
        warn("Traps don't distinguish 假设测试 vs 选项对比")


def validate_cross_layer():
    """Check no cross-layer contamination."""
    print("\n--- Cross-Layer Contamination ---")

    l1 = read_file("references/l1-core.md")
    l2 = read_file("references/l2-strategies.md")
    l3 = read_file("references/l3-onetime.md")

    # L2 should not define core rules that belong in L1
    l1_terms = ["方向确认节点", "方向确认驱动循环", "输出结构"]
    for term in l1_terms:
        if term in l2:
            warn(f"'{term}' appears in L2 (belongs in L1)")
        else:
            ok(f"'{term}' not leaked into L2")

    if term in l3:
        warn(f"'{term}' appears in L3 (belongs in L1)")
    else:
        ok(f"'{term}' not leaked into L3")


def main():
    global PASSED, FAILED, WARNINGS

    print("=" * 60)
    print("  situation-goal-solver v4.1 — Architecture Validator")
    print("=" * 60)

    # 1. File existence
    print("\n--- File Existence ---")
    for f in REQUIRED_FILES:
        check_file_exists(f)

    # 2. Layer validations
    validate_frontmatter()
    validate_l1()
    validate_l2()
    validate_l3()
    validate_exploration()
    validate_error_recovery()
    validate_cross_layer()

    # Summary
    print("\n" + "=" * 60)
    total = PASSED + FAILED + WARNINGS
    print(f"  Results: {PASSED} passed, {FAILED} failed, {WARNINGS} warnings ({total} checks)")
    print("=" * 60)

    if FAILED > 0:
        print("\n❌ VALIDATION FAILED — fix errors above before using skill.")
        sys.exit(1)
    elif WARNINGS > 0:
        print("\n⚠️  PASSED WITH WARNINGS — review warnings above, skill is usable.")
    else:
        print("\n✅ ALL CHECKS PASSED — skill is valid.")

    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    main()
