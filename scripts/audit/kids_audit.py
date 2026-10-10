#!/usr/bin/env python3
"""lhg-kids-code 确定性教案审计：14 条规则，零第三方依赖。

扫描目标目录的 Markdown 教案（约定见下），输出 JSON 与人类可读报告；
有 blocker 时以 exit code 2 退出（供 hooks 与 CI 使用）。

用法：
    python3 kids_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

教案 Markdown 约定（审计脚本识别的结构）：
  - 顶部信息行注明年龄段，如 `> 年龄段：8-10岁 | 工具：Scratch | 课时：45分钟`
  - `## 故事引入`：≤3 句话的故事 + 提问钩子
  - `##` PRIMM 五步（预测/运行/探究/改写/创造）或积木/代码示例节
  - `## 课堂互动小游戏`：规则 + 时长 + 安全注意
  - `## 课后练习`：必做 + 挑战
  - `## 成人审核声明`：文末必备（blocker，一票否决）
  - Python 示例用 ```python 代码块；Scratch 积木用文字描述（含"积木"字样）

规则文案均为本项目原创（思路受 PRIMM / Use-Modify-Create 等公开教学
方法论启发，未复制任何第三方原文）。
"""

import argparse
import ast
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-kids-code/kids-audit"

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", "dist", "build", "vendor",
}
SCAN_EXTS = {".md", ".markdown"}


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def collect_files(target):
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            _, ext = os.path.splitext(f)
            if ext in SCAN_EXTS:
                out.append(os.path.join(root, f))
    return sorted(out)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def first_hit_line(lines, pattern, flags=0):
    rx = re.compile(pattern, flags)
    for i, ln in enumerate(lines):
        if rx.search(ln):
            return i + 1, ln.strip()[:160]
    return 1, ""


def code_blocks(text):
    """返回 [(语言标注或None, 代码, 起始行号)]。"""
    out = []
    cur_lang, cur_lines, cur_start = None, None, 0
    for i, ln in enumerate(text.split("\n")):
        m = re.match(r"^```(\w*)\s*$", ln)
        if m and cur_lines is None:
            cur_lang = m.group(1) or None
            cur_lines = []
            cur_start = i + 1
        elif ln.strip() == "```" and cur_lines is not None:
            out.append((cur_lang, "\n".join(cur_lines), cur_start))
            cur_lang, cur_lines = None, None
        elif cur_lines is not None:
            cur_lines.append(ln)
    return out


# ---------------------------------------------------------------- 规则定义

RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity, "category": category,
             "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


def _mk(rule_id, path, line, snippet):
    r = _RULE_BY_ID[rule_id]
    return Finding(r["id"], r["severity"], r["category"], r["title"],
                   path, line, snippet, r["detail"])


def _missing_section(rule_id, lines, text, path, keywords):
    if not any(k in text for k in keywords):
        line, snip = first_hit_line(lines, r"^#")
        return [_mk(rule_id, path, line, snip or os.path.basename(path))]
    return []


# ---------------- 教案结构 ----------------

@rule("KC-LSN-001", "blocker", "教案结构", "成人审核声明缺失",
      "教案文末缺少成人审核声明。本插件是备课助手，内容须经成年人审核后才能用于儿童——无声明一票否决。")
def r_lsn_001(lines, text, path, ctx):
    return _missing_section("KC-LSN-001", lines, text, path, ["成人审核"])


@rule("KC-LSN-002", "warning", "教案结构", "故事引入缺失",
      "缺少故事引入节。少儿编程课靠故事钩子开场，无引入直接讲概念，孩子坐不住。")
def r_lsn_002(lines, text, path, ctx):
    return _missing_section("KC-LSN-002", lines, text, path, ["故事引入"])


@rule("KC-LSN-003", "blocker", "教案结构", "积木/代码示例缺失",
      "既无代码块也无积木描述。编程课没有可运行的示例等于没备课。")
def r_lsn_003(lines, text, path, ctx):
    if "```" not in text and "积木" not in text:
        line, snip = first_hit_line(lines, r"^#")
        return [_mk("KC-LSN-003", path, line, snip or os.path.basename(path))]
    return []


@rule("KC-LSN-004", "warning", "教案结构", "课堂互动小游戏缺失",
      "缺少课堂互动小游戏设计。少儿课堂需要动手环节纯讲，纪律会先崩。")
def r_lsn_004(lines, text, path, ctx):
    return _missing_section("KC-LSN-004", lines, text, path, ["小游戏", "互动游戏"])


@rule("KC-LSN-005", "warning", "教案结构", "课后练习缺失",
      "缺少课后练习（必做 1 + 挑战 1）。无练习，家长不知道课后陪孩子做什么。")
def r_lsn_005(lines, text, path, ctx):
    return _missing_section("KC-LSN-005", lines, text, path, ["课后练习"])


@rule("KC-LSN-006", "warning", "教案结构", "年龄段声明缺失",
      "顶部信息行缺少年龄段声明。5 岁和 12 岁的课是两种课，不声明等于没法定讲法。")
def r_lsn_006(lines, text, path, ctx):
    return _missing_section("KC-LSN-006", lines, text, path, ["年龄段", "学段"])


# ---------------- 示例代码 ----------------

@rule("KC-CODE-001", "blocker", "示例代码", "Python 示例语法错误",
      "Python 代码块无法通过语法解析。课堂上跑不通就是教学事故，先修再上课。")
def r_code_001(lines, text, path, ctx):
    out = []
    for lang, code, start in code_blocks(text):
        if (lang or "").lower() != "python" or not code.strip():
            continue
        try:
            ast.parse(code)
        except SyntaxError as e:
            out.append(_mk("KC-CODE-001", path, start + (e.lineno or 1) - 1,
                          "SyntaxError: %s" % (e.msg or "语法错误")))
    return out


@rule("KC-CODE-002", "warning", "示例代码", "代码块缺语言标注",
      "``` 后未标注语言（如 python）。标注语言才能做语法检查，也方便老师复制。")
def r_code_002(lines, text, path, ctx):
    out = []
    for lang, code, start in code_blocks(text):
        if lang is None and code.strip():
            out.append(_mk("KC-CODE-002", path, start, "``` 未标注语言"))
    return out


@rule("KC-CODE-003", "warning", "示例代码", "Python 示例过长",
      "单个 Python 示例超过 40 行。少儿课堂示例宜 ≤30 行，超长请拆成基础版 + 加料版。")
def r_code_003(lines, text, path, ctx):
    out = []
    for lang, code, start in code_blocks(text):
        if (lang or "").lower() == "python" and len(code.split("\n")) > 40:
            out.append(_mk("KC-CODE-003", path, start,
                           "该 python 代码块 %d 行" % len(code.split("\n"))))
    return out


# ---------------- 安全红线 ----------------

@rule("KC-SAFE-001", "warning", "安全红线", "疑似不当用词",
      "教案出现暴力/恐怖/施压类用词。儿童内容须改写：失败说'我们再试一次'，不说教施压。")
def r_safe_001(lines, text, path, ctx):
    out = []
    for i, ln in enumerate(lines):
        if re.search(r"杀死|血腥|死掉|鬼故事|恐怖|打死|笨死了|跟不上就|别人都会", ln):
            out.append(_mk("KC-SAFE-001", path, i + 1, ln.strip()[:160]))
    return out


@rule("KC-SAFE-002", "warning", "安全红线", "超纲概念未标注",
      "出现递归/指针/面向对象/多线程/正则/算法复杂度等超纲概念。请按 lhg-kc-audit 超纲分级表确认年龄段适配，或删改。")
def r_safe_002(lines, text, path, ctx):
    out = []
    for i, ln in enumerate(lines):
        if re.search(r"递归|指针|面向对象|多线程|正则表达式|算法复杂度|时间复杂度", ln):
            out.append(_mk("KC-SAFE-002", path, i + 1, ln.strip()[:160]))
    return out


@rule("KC-SAFE-003", "warning", "安全红线", "疑似索取儿童个人信息",
      "教案要求儿童填写/提供姓名、电话、住址、照片等个人信息。本插件不收集儿童信息，此类要求请删掉，改由成年人线下处理。")
def r_safe_003(lines, text, path, ctx):
    out = []
    for i, ln in enumerate(lines):
        if re.search(r"让(孩子|学生|小朋友).{0,12}(填|输入|提供|写下|告诉).{0,12}(姓名|电话|住址|照片|身份证|学校)", ln):
            out.append(_mk("KC-SAFE-003", path, i + 1, ln.strip()[:160]))
    return out


# ---------------- 卫生 ----------------

@rule("KC-HYG-001", "blocker", "卫生", "TODO/占位残留",
      "教案里还有 TODO/FIXME/XXX。备课稿有占位 = 没备完，不许交付。")
def r_hyg_001(lines, text, path, ctx):
    out = []
    for i, ln in enumerate(lines):
        if re.search(r"\b(TODO|FIXME|XXX)\b", ln):
            out.append(_mk("KC-HYG-001", path, i + 1, ln.strip()[:160]))
    return out


@rule("KC-HYG-002", "warning", "卫生", "'待补充'占位残留",
      "出现'待补充/待定'类占位。请补完内容或删掉该节，不要带着占位上课。")
def r_hyg_002(lines, text, path, ctx):
    out = []
    for i, ln in enumerate(lines):
        if re.search(r"待补充|待定|TBD", ln):
            out.append(_mk("KC-HYG-002", path, i + 1, ln.strip()[:160]))
    return out


# ---------------------------------------------------------------- 运行器

def run(target):
    files = collect_files(target)
    findings = []
    for path in files:
        text = read_text(path)
        lines = text.split("\n")
        rel = os.path.relpath(path, target)
        for r in RULES:
            try:
                for f in r["check"](lines, text, path, {}) or []:
                    f.file = rel
                    findings.append(f)
            except Exception:
                continue  # 单条规则异常不影响整体
    return files, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="lhg-kids-code 确定性教案审计")
    ap.add_argument("--target", default=".", help="扫描目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"], default="blocker")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print("target 不是目录：%s" % args.target, file=sys.stderr)
        return 1

    files, findings = run(target)
    sev_rank = {"blocker": 3, "warning": 2, "nit": 1}
    counts = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    result = {
        "tool": TOOL,
        "version": VERSION,
        "target": args.target,
        "summary": {
            "files_scanned": len(files),
            "rules_run": len(RULES),
            "blocker": counts["blocker"],
            "warning": counts["warning"],
            "nit": counts["nit"],
        },
        "findings": [f.to_dict() for f in sorted(
            findings, key=lambda x: (-sev_rank.get(x.severity, 0), x.file, x.line))],
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print("教案审计：扫描 %d 文件，运行 %d 条规则" % (s["files_scanned"], s["rules_run"]))
        print("blocker=%d warning=%d nit=%d" % (s["blocker"], s["warning"], s["nit"]))
        for f in result["findings"]:
            print("[%s][%s] %s:%d %s" % (
                f["severity"].upper(), f["rule_id"], f["file"], f["line"], f["title"]))
            print("    %s" % f["detail"])
            if f["snippet"]:
                print("    → %s" % f["snippet"])

    level = sev_rank[args.fail_on]
    bad = any(sev_rank.get(f.severity, 0) >= level for f in findings)
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
