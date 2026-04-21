#!/usr/bin/env python3
# Parse today's Obsidian TIL note, extract title/summary/topics,
# and publish a trimmed markdown into this repo with a git commit + push.

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

VAULT_TIL_DIR = Path("/Users/zephyr/Documents/내거/TIL")
REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLISH_ROOT = REPO_ROOT / "TIL"

SUMMARY_HEADING = "## 📌 오늘의 주제"
TOPICS_HEADING = "### 개념"

# Strings that indicate the user hasn't filled in the placeholder.
PLACEHOLDER_MARKERS = ("한 줄 요약", "한 문장으로 압축", "YOUR", "TODO")


def find_today_til(today):
    prefix = today.strftime("%Y-%m-%d")
    matches = sorted(VAULT_TIL_DIR.glob(f"{prefix}*.md"))
    return matches[0] if matches else None


def parse_frontmatter(content):
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}, content
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("-"):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, content[m.end():]


def extract_section(body, heading):
    # Grab everything between `heading` and the next heading of equal/higher level
    # (or a horizontal rule / end of file).
    level = len(heading) - len(heading.lstrip("#"))
    stop = r"(?=\n#{1," + str(level) + r"}\s|\n---\s*\n|\Z)"
    pattern = r"^" + re.escape(heading) + r"\s*\n(.*?)" + stop
    m = re.search(pattern, body, re.DOTALL | re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_summary(body):
    section = extract_section(body, SUMMARY_HEADING)
    lines = []
    for raw in section.splitlines():
        s = raw.strip()
        if s.startswith(">"):
            lines.append(s.lstrip(">").strip())
    return "\n".join(l for l in lines if l)


def extract_topics(body):
    # Accept only canonical indentation — top-level `- ` or exactly one tab /
    # two-space level. This filters out deeper detail and also irregular
    # indentation like "\t - ..." that would otherwise be misread as depth 1.
    section = extract_section(body, TOPICS_HEADING)
    out = []
    for raw in section.splitlines():
        m = re.match(r"^(|\t|  )- (.+)$", raw)
        if not m:
            continue
        depth = 0 if m.group(1) == "" else 1
        txt = m.group(2).strip()
        txt = re.sub(r"!\[\[.*?\]\]", "", txt)
        txt = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", txt)
        txt = re.sub(r"\*\*|__", "", txt).strip()
        if txt:
            out.append(("  " * depth) + f"- {txt}")
    return out


def is_placeholder(text):
    if not text or len(text.strip()) < 5:
        return True
    return any(mk in text for mk in PLACEHOLDER_MARKERS)


def render(title, summary, topics, note=None):
    lines = [f"# {title} — TIL", ""]
    if not is_placeholder(summary):
        lines.append("## 📌 오늘의 주제")
        for s in summary.splitlines():
            lines.append(f"> {s}")
        lines.append("")
    if topics:
        lines.append("## 🔍 학습한 것")
        lines.extend(topics)
        lines.append("")
    if note:
        lines.append(f"> {note}")
        lines.append("")
    lines.append("---")
    lines.append(f"_자동 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    return "\n".join(lines) + "\n"


def run_git(*args):
    subprocess.run(["git", *args], cwd=REPO_ROOT, check=True)


def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")

    dst = PUBLISH_ROOT / today.strftime("%Y") / today.strftime("%m") / f"{date_str}.md"
    if dst.exists():
        print(f"[{date_str}] 이미 게시됨 — skip: {dst}")
        return 0

    src = find_today_til(today)
    if src is None:
        title = date_str
        summary = ""
        topics = []
        note = "오늘은 TIL을 남기지 못했습니다."
    else:
        fm, body = parse_frontmatter(src.read_text(encoding="utf-8"))
        title = fm.get("title") or date_str
        summary = extract_summary(body)
        topics = extract_topics(body)
        note = None
        if is_placeholder(summary) and not topics:
            note = "오늘은 기록할 내용이 아직 정리되지 않았습니다."

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render(title, summary, topics, note), encoding="utf-8")

    rel = dst.relative_to(REPO_ROOT)
    run_git("add", str(rel))
    run_git("commit", "-m", f"TIL: {date_str}")
    run_git("push")
    print(f"[{date_str}] 게시 완료 → {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
