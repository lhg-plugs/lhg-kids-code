#!/usr/bin/env python3
"""lhg-kids-code 硬门②（警告级，不拦截）：教案 Markdown 缺成人审核声明时提醒。

触发：PostToolUse / Write|Edit。只做提醒，永远 exit 0、不拦截写入。
本插件是备课助手，教案须经成年人审核后才能用于儿童——写完教案没带
声明，大概率是忘了贴，而不是故意不贴，所以只提醒不拦截。

逃生方式：LHG_KC_HOOKS_OFF=1（环境变量）可关闭本提醒；
或 /plugin disable lhg-kids-code 停用整个插件。
零第三方依赖。
"""

import json
import os
import sys

MD_EXTS = {".md", ".markdown"}


def main() -> int:
    if os.environ.get("LHG_KC_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0

    _, ext = os.path.splitext(file_path)
    if ext.lower() not in MD_EXTS:
        return 0
    if not os.path.isfile(file_path):
        return 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return 0

    # 非教案文件（不含教案关键词）不打扰
    if "教案" not in text and "课后练习" not in text:
        return 0
    if "成人审核" in text:
        return 0  # 已有声明，不提醒

    msg = (
        "备课提醒（lhg-kids-code）：%s 疑似教案，但未找到「成人审核声明」。\n"
        "本插件是备课助手，教案须经成年人审核后才能用于儿童——"
        "请在文末补上声明（模板见 lhg-kc-audit 第 7 节），或跑 /lhg-kids-code:audit。\n"
        "关闭本提醒：export LHG_KC_HOOKS_OFF=1（当前会话有效）。"
    ) % file_path
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
