#!/usr/bin/env python3
"""Static checks for this repository. Development tool only; the skill does not need it.

Checks:
  * every skills/<name>/SKILL.md follows the Agent Skills spec frontmatter rules
  * SKILL.md body length and referenced files
  * no personal paths, e-mail addresses, or owner-specific strings anywhere in the repo

Owner-specific strings (names, machine names, company names) are read from an
untracked `.private-patterns` file, one case-insensitive literal per line, so the
patterns themselves never land in the public repository.

Usage: python3 scripts/check.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_BODY_LINES = 500
SKIP_DIRS = {".git", "__pycache__", "results", "node_modules"}
GENERIC_PATTERNS = [
    ("home directory path", re.compile(r"/Users/(?!<)[A-Za-z0-9._-]+")),
    ("home directory path", re.compile(r"/home/(?!<)[a-z0-9._-]+")),
    ("Windows user path", re.compile(r"[A-Za-z]:\\Users\\")),
    ("e-mail address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")


def parse_frontmatter(text):
    """Return (fields, body_start_line) for a simple YAML frontmatter block.

    Supports `key: value`, block scalars (`>`, `>-`, `|`, `|-`) and one level of
    nested mapping, which is all the spec fields need. Raises ValueError otherwise.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with a '---' frontmatter line")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("frontmatter has no closing '---' line")

    fields, key = {}, None
    for raw in lines[1:end]:
        if not raw.strip():
            if key and isinstance(fields[key], list):
                fields[key].append("")
            continue
        if raw[0] in " \t":
            if key is None:
                raise ValueError(f"indented line without a key: {raw!r}")
            if isinstance(fields[key], list):
                fields[key].append(raw.strip())
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not match:
            raise ValueError(f"cannot parse frontmatter line: {raw!r}")
        key, value = match.group(1), match.group(2).strip()
        if key in fields:
            raise ValueError(f"duplicate frontmatter key: {key}")
        if value in (">", ">-", "|", "|-", ""):
            fields[key] = [] if value else {}
            fields[key + "\0style"] = value
        else:
            fields[key] = value.strip("'\"")

    result = {}
    for k, v in fields.items():
        if k.endswith("\0style"):
            continue
        style = fields.get(k + "\0style", "")
        if isinstance(v, list):
            joined = "\n".join(v) if style.startswith("|") else " ".join(x for x in v if x)
            result[k] = joined.strip()
        else:
            result[k] = v
    return result, end + 1


def check_skill(skill_md, problems):
    rel = skill_md.relative_to(ROOT)
    text = skill_md.read_text(encoding="utf-8")
    try:
        fields, body_start = parse_frontmatter(text)
    except ValueError as error:
        problems.append(f"{rel}: {error}")
        return

    unknown = set(fields) - SPEC_KEYS
    if unknown:
        problems.append(f"{rel}: frontmatter keys outside the Agent Skills spec: {sorted(unknown)}")

    name = fields.get("name", "")
    if not name:
        problems.append(f"{rel}: missing name")
    elif len(name) > 64 or not NAME_RE.match(name):
        problems.append(f"{rel}: name {name!r} breaks the spec naming rules")
    elif name != skill_md.parent.name:
        problems.append(f"{rel}: name {name!r} differs from directory {skill_md.parent.name!r}")

    description = fields.get("description", "")
    if not isinstance(description, str) or not description:
        problems.append(f"{rel}: missing description")
    elif len(description) > 1024:
        problems.append(f"{rel}: description is {len(description)} characters (max 1024)")

    body = text.split("\n")[body_start:]
    if len(body) > MAX_BODY_LINES:
        problems.append(f"{rel}: body is {len(body)} lines (keep it under {MAX_BODY_LINES})")

    for target in sorted(set(re.findall(r"references/[A-Za-z0-9_./-]+\.md", text))):
        if not (skill_md.parent / target).is_file():
            problems.append(f"{rel}: references missing file {target}")

    print(f"ok  {rel}: name={name}, description={len(description)} chars, body={len(body)} lines")


def text_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.name == ".private-patterns":
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def private_patterns():
    source = ROOT / ".private-patterns"
    if not source.is_file():
        print("note .private-patterns not found; only generic personal-info patterns are checked")
        return []
    lines = source.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def check_personal_info(problems):
    extra = [(p, re.compile(re.escape(p), re.IGNORECASE)) for p in private_patterns()]
    count = 0
    for path, text in text_files():
        count += 1
        rel = path.relative_to(ROOT)
        for number, line in enumerate(text.split("\n"), 1):
            for label, pattern in GENERIC_PATTERNS:
                for match in pattern.finditer(line):
                    if label == "e-mail address" and match.group().lower().endswith(ALLOWED_EMAIL_DOMAINS):
                        continue
                    problems.append(f"{rel}:{number}: {label}: {match.group()}")
            for literal, pattern in extra:
                if pattern.search(line):
                    problems.append(f"{rel}:{number}: private pattern {literal!r}")
    print(f"ok  scanned {count} text files for personal information")


def run_skills_ref(problems):
    if not shutil.which("skills-ref"):
        print("skip skills-ref not installed (optional: https://github.com/agentskills/agentskills)")
        return
    for skill_dir in sorted((ROOT / "skills").glob("*/")):
        result = subprocess.run(["skills-ref", "validate", str(skill_dir)], capture_output=True, text=True)
        if result.returncode != 0:
            problems.append(f"skills-ref validate {skill_dir.name}: {(result.stdout + result.stderr).strip()}")
        else:
            print(f"ok  skills-ref validate {skill_dir.name}")


def main():
    problems = []
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skills:
        print("note no skills/*/SKILL.md found yet")
    for skill_md in skills:
        check_skill(skill_md, problems)
    run_skills_ref(problems)
    check_personal_info(problems)

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
