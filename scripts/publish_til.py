#!/usr/bin/env python3
# Parse today's Obsidian TIL note, extract title/summary/topics,
# and publish a trimmed markdown into this repo with a git commit + push.

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Override with JANDI_VAULT_TIL_DIR; otherwise fall back to the per-OS vault location.
if sys.platform == "win32":
    DEFAULT_VAULT_TIL_DIR = Path.home() / "Documents" / "TIL" / "TIL"
else:
    DEFAULT_VAULT_TIL_DIR = Path("/Users/zephyr/dev/내거/TIL")
VAULT_TIL_DIR = Path(os.environ.get("JANDI_VAULT_TIL_DIR") or DEFAULT_VAULT_TIL_DIR)
REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLISH_ROOT = REPO_ROOT / "TIL"

SUMMARY_HEADING = "## 📌 오늘의 주제"
TOPICS_HEADING = "### 개념"

# Strings that indicate the user hasn't filled in the placeholder.
PLACEHOLDER_MARKERS = ("한 줄 요약", "한 문장으로 압축", "YOUR", "TODO")

# Notes carrying any of these tags are company material: nothing from them
# (not even the title) may reach this public repo.
PRIVATE_TAGS = {"업무", "회사", "비공개"}


def find_tils(today):
    # Notes are named either "2026-10-06 (화).md" or "TIL — 2026-10-06 (화).md".
    date_str = today.strftime("%Y-%m-%d")
    return sorted(VAULT_TIL_DIR.glob(f"*{date_str}*.md"))


def extract_tags(content):
    # Frontmatter `tags:` in block ("  - a") or inline ("[a, b]") form, plus
    # inline `#tag` in the body.
    tags = set()
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if m:
        in_tags = False
        for line in m.group(1).splitlines():
            if re.match(r"^tags\s*:", line):
                in_tags = True
                tags.update(re.split(r"[,\s]+", line.partition(":")[2].strip(" []")))
            elif in_tags and line.lstrip().startswith("-"):
                tags.add(line.lstrip()[1:].strip())
            else:
                in_tags = False
    tags.update(re.findall(r"(?<!\S)#([^\s#]+)", content))
    return {t.strip("\"'#") for t in tags if t}


def is_private(content):
    return bool(extract_tags(content) & PRIVATE_TAGS)


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
    # Windows redirects stdout with the ANSI code page; force UTF-8 for the log files.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")

    # An optional YYYY-MM-DD argument backfills a missed day; the commit is
    # dated 16:30 of that day so it lands on the right square of the graph.
    backfill = len(sys.argv) > 1
    today = datetime.strptime(sys.argv[1], "%Y-%m-%d") if backfill else datetime.now()
    date_str = today.strftime("%Y-%m-%d")

    dst = PUBLISH_ROOT / today.strftime("%Y") / today.strftime("%m") / f"{date_str}.md"
    if dst.exists():
        print(f"[{date_str}] 이미 게시됨 — skip: {dst}")
        return 0

    notes = [p.read_text(encoding="utf-8") for p in find_tils(today)]
    public = [n for n in notes if not is_private(n)]
    if not public:
        title = date_str
        summary = ""
        topics = []
        if notes:
            note = "오늘 학습한 내용은 비공개 자료라 게시하지 않습니다."
        else:
            note = "오늘은 TIL을 남기지 못했습니다."
    else:
        fm, body = parse_frontmatter(public[0])
        title = fm.get("title") or date_str
        summary = extract_summary(body)
        topics = extract_topics(body)
        note = None
        if is_placeholder(summary) and not topics:
            note = "오늘은 기록할 내용이 아직 정리되지 않았습니다."

    dst.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" keeps LF on Windows, matching the files published from macOS.
    with dst.open("w", encoding="utf-8", newline="\n") as f:
        f.write(render(title, summary, topics, note))

    rel = dst.relative_to(REPO_ROOT)
    run_git("add", str(rel))
    if backfill:
        stamp = today.strftime("%Y-%m-%dT16:30:00")
        os.environ["GIT_AUTHOR_DATE"] = os.environ["GIT_COMMITTER_DATE"] = stamp
    run_git("commit", "-m", f"TIL: {date_str}")
    run_git("push")
    print(f"[{date_str}] 게시 완료 → {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
