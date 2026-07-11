#!/usr/bin/env python3
"""
L2 Strategy Matcher for situation-goal-solver skill.

Input: a user query string
Output: which L2 strategy should activate, confidence, and reasoning.

Usage:
    python match-strategy.py "帮我写个 Python 脚本读取 CSV"
    python match-strategy.py "我在纠结去大厂还是创业公司"
    python match-strategy.py --json "docker 容器启动报错了"

When --json flag is used, outputs machine-readable JSON for AI consumption.
When omitted, outputs human-readable format.
"""

import json
import re
import sys

# Strategy definitions with trigger patterns and weights
STRATEGIES = {
    0: {
        "name": "探索模式",
        "explicit_triggers": ["我不确定", "我不知道", "你帮我看看", "帮我探索", "探索模式"],
        "pattern_triggers": [
            (r"选(哪个|什么)方向", 5),
            (r"不知道.*怎么", 4),
            (r"帮我.*看看.*方向", 4),
            (r"有点迷", 3),
        ],
        "description": "用户自身信息不足或问题开放探索型",
    },
    1: {
        "name": "写代码 / 技术实现",
        "explicit_triggers": [],
        "pattern_triggers": [
            (r"(写|帮我写|编码|实现).*(代码|脚本|函数|程序|类)", 5),
            (r"(Python|Java|C\+\+|Rust|Go|JS|TypeScript).*(函数|脚本|代码)", 4),
            (r"(开发|搭建).*(项目|应用|功能)", 3),
            (r"(算法|数据结构|设计模式)", 3),
            (r"(优化|重构).*(代码|函数)", 3),
        ],
        "description": "代码编写、开发实现、算法设计",
    },
    2: {
        "name": "做决策 / 选方向",
        "explicit_triggers": [],
        "pattern_triggers": [
            (r"(选|纠结|犹豫).*(哪个|哪个好|方向|offer|工作|公司)", 5),
            (r"(求职|找工作|职业规划|跳槽)", 5),
            (r"(技术选型|选型)", 4),
            (r"(怎么选|如何选择|怎么抉择)", 4),
            (r"(大厂|创业|考研|考公)", 3),
            (r"(先.*再|路线|路径).*(规划|选择)", 3),
        ],
        "description": "决策、选方向、职业规划、技术选型",
    },
    3: {
        "name": "部署 / 配置 / 调试",
        "explicit_triggers": [],
        "pattern_triggers": [
            (r"(报错|出错|error|exception|traceback|崩溃|挂了)", 5),
            (r"(部署|deploy|上线|发布)", 5),
            (r"(配置|config|环境).*(问题|不对|失败)", 4),
            (r"(docker|k8s|nginx|服务器).*(报错|配置|启动)", 4),
            (r"(调试|debug|排查|定位)", 4),
            (r"(装不上|安装失败|跑不起来)", 3),
        ],
        "description": "部署、配置、调试、排错",
    },
    4: {
        "name": "学习新东西 / 技能提升",
        "explicit_triggers": [],
        "pattern_triggers": [
            (r"(学|学习|入门|新手).*(怎么|如何|推荐)", 5),
            (r"(教程|课程|资源|路径)", 4),
            (r"(零基础|小白|完全不懂)", 4),
            (r"(提升|进阶).*(技能|能力)", 3),
            (r"(学什么|先学什么|怎么学)", 5),
        ],
        "description": "学习路径、技能提升、资源推荐",
    },
}


def score_query(query: str, strategy: dict) -> float:
    """Score how well a query matches a strategy."""
    total = 0.0

    # Check explicit triggers (instant match)
    for trigger in strategy["explicit_triggers"]:
        if trigger in query:
            return 10.0  # Instant high confidence

    # Check pattern triggers
    for pattern, weight in strategy["pattern_triggers"]:
        if re.search(pattern, query):
            total += weight

    return total


def match_strategy(query: str) -> dict:
    """Find the best matching strategy for a query."""
    scores = {}
    for sid, strategy in STRATEGIES.items():
        scores[sid] = score_query(query, strategy)

    best_sid = max(scores, key=scores.get)
    best_score = scores[best_sid]

    # If no strategy matches strongly, return None (use pure L1)
    if best_score < 2.0:
        return {
            "strategy_id": None,
            "strategy_name": "纯 L1 规则（未匹配）",
            "confidence": 0.0,
            "reason": "No strategy matched strongly — use pure L1 rules",
            "all_scores": scores,
        }

    # Calculate confidence (0.0-1.0)
    # At score 10, confidence = 1.0; at score 2, confidence = 0.3
    confidence = min(1.0, max(0.3, best_score / 10.0))

    # Check if another strategy is close (boundary case)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    boundary = False
    runner_up = None
    if len(sorted_scores) > 1 and sorted_scores[1][1] >= best_score * 0.7:
        boundary = True
        runner_up = STRATEGIES[sorted_scores[1][0]]["name"]

    result = {
        "strategy_id": best_sid,
        "strategy_name": STRATEGIES[best_sid]["name"],
        "confidence": round(confidence, 3),
        "reason": STRATEGIES[best_sid]["description"],
        "boundary_case": boundary,
        "runner_up": runner_up,
        "all_scores": {str(sid): score for sid, score in scores.items()},
    }

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python match-strategy.py [--json] '<user query>'", file=sys.stderr)
        print("       echo 'user query' | python match-strategy.py [--json]", file=sys.stderr)
        sys.exit(1)

    json_mode = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--json"]

    # Read query from args or stdin
    if args:
        query = " ".join(args)
    else:
        query = sys.stdin.read().strip()

    if not query:
        print("Error: empty query", file=sys.stderr)
        sys.exit(1)

    result = match_strategy(query)

    if json_mode:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Query: {query}")
        print(f"Strategy: {result['strategy_name']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Reason: {result['reason']}")
        if result.get("boundary_case"):
            print(f"⚠️  Boundary case — runner-up: {result['runner_up']}")
            print("   Consider 策略确认 before proceeding.")

    return 0


if __name__ == "__main__":
    main()
