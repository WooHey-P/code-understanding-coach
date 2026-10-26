#!/usr/bin/env python3
"""Render a recorded scenario transcript as an animated GIF for the README.

The GIF replays a real `transcript.md` written by tests/scenarios/run.py: the text is
the agent's actual output, only reformatted for display (markdown markers removed,
tool calls summarized as one status line). Nothing is written by hand.

Development tool only. Requires Pillow (`pip install pillow`) and a font that covers
the transcript's language; the default is Apple SD Gothic Neo (macOS).

Usage:
  python3 scripts/render_demo.py tests/scenarios/results/<run>/claude/DEMO-en/transcript.md \
      docs/assets/demo-en.gif --title "Claude Code · book-rental (synthetic)"
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

WIDTH, HEIGHT = 960, 600
PAD, LINE_GAP = 28, 7
BAR = 40
FOOTER = 34
COLORS = {
    "bg": (24, 26, 33), "bar": (36, 39, 48), "text": (222, 225, 232), "dim": (128, 134, 150),
    "you": (125, 196, 255), "coach": (190, 160, 255), "status": (110, 190, 140), "rule": (60, 64, 76),
}
DEFAULT_FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def parse(transcript):
    """Return [(role, text, tools)] from a run.py transcript."""
    entries, role, lines = [], None, []
    for raw in transcript.splitlines():
        header = re.match(r"^## (Developer|Assistant|Runner)\b", raw)
        if header:
            if role:
                entries.append((role, lines))
            role, lines = header.group(1), []
        elif role and not raw.startswith("# "):
            lines.append(raw)
    if role:
        entries.append((role, lines))

    result = []
    for role, body in entries:
        tools = []
        kept = []
        for line in body:
            match = re.match(r"^_tools: (.*)_$", line.strip())
            if match:
                tools = [t.strip() for t in match.group(1).split(",")]
            else:
                kept.append(line)
        if role == "Runner":
            continue
        result.append((role, clean("\n".join(kept)), tools))
    return result


def clean(text):
    text = re.sub(r"```[a-z]*\n?", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", text)
    text = text.replace("`", "")
    text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^> ?", "  ", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def wrap(text, font, width):
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        indent = len(paragraph) - len(paragraph.lstrip(" "))
        current = ""
        for word in re.findall(r"\S+\s*", paragraph.strip()):
            candidate = current + word
            if font.getlength(" " * indent + candidate.rstrip()) <= width or not current:
                current = candidate
            else:
                lines.append(" " * indent + current.rstrip())
                current = word
        lines.append(" " * indent + current.rstrip())
    return lines


def tool_summary(tools):
    reads = sum(1 for t in tools if t in ("Read", "Grep", "Glob", "Bash", "shell"))
    parts = []
    if "Skill" in tools:
        parts.append("loaded code-understanding-coach")
    if reads:
        parts.append(f"{reads} read/search calls")
    return " · ".join(parts)


class Renderer:
    def __init__(self, font_path, title, caption):
        self.font = ImageFont.truetype(font_path, 17)
        self.small = ImageFont.truetype(font_path, 14)
        self.title, self.caption = title, caption
        self.line_h = self.font.size + LINE_GAP
        self.rows = (HEIGHT - BAR - FOOTER - 2 * 14) // self.line_h
        self.text_w = WIDTH - 2 * PAD
        self.buffer = []  # (color, text)
        self.frames, self.durations = [], []

    def frame(self, duration, cursor=False):
        image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["bg"])
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, WIDTH, BAR], fill=COLORS["bar"])
        for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            draw.ellipse([16 + i * 22, 14, 28 + i * 22, 26], fill=color)
        draw.text((WIDTH // 2, BAR // 2), self.title, font=self.small, fill=COLORS["dim"], anchor="mm")
        visible = self.buffer[-self.rows:]
        y = BAR + 14
        for color, text in visible:
            draw.text((PAD, y), text, font=self.font, fill=COLORS[color])
            y += self.line_h
        if cursor and visible:
            color, text = visible[-1]
            x = PAD + self.font.getlength(text) + 2
            draw.rectangle([x, y - self.line_h + 3, x + 9, y - LINE_GAP], fill=COLORS["you"])
        draw.line([0, HEIGHT - FOOTER, WIDTH, HEIGHT - FOOTER], fill=COLORS["rule"])
        draw.text((PAD, HEIGHT - FOOTER // 2), self.caption, font=self.small, fill=COLORS["dim"], anchor="lm")
        self.frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE, colors=48))
        self.durations.append(duration)

    def user(self, text):
        prefix = "you › "
        wrapped = wrap(prefix + text, self.font, self.text_w)
        self.buffer.append(("dim", ""))
        typed = ""
        target = "\n".join(wrapped)
        step = max(2, len(target) // 40)
        for i in range(step, len(target) + step, step):
            typed = target[:i]
            parts = typed.split("\n")
            self.buffer = self.buffer[: len(self.buffer) - (self._typing or 0)]
            self.buffer += [("you", p) for p in parts]
            self._typing = len(parts)
            self.frame(45, cursor=True)
        self._typing = 0
        self.frame(500)

    _typing = 0

    def assistant(self, text, tools):
        summary = tool_summary(tools)
        if summary:
            self.buffer.append(("status", f"  ⋯ {summary}"))
            self.frame(900)
        self.buffer.append(("coach", "coach ›"))
        for line in wrap(text, self.font, self.text_w - 16):
            self.buffer.append(("text", "  " + line if line else ""))
            self.frame(110 if line else 60)
        self.frame(2200)

    def save(self, path):
        self.frames[0].save(path, save_all=True, append_images=self.frames[1:], duration=self.durations,
                            loop=0, optimize=True, disposal=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="code-understanding-coach")
    parser.add_argument("--caption", default="Replay of a recorded run on a synthetic project · text is the agent's actual output")
    parser.add_argument("--font", default=DEFAULT_FONT)
    args = parser.parse_args()

    if not Path(args.font).exists():
        sys.exit(f"font not found: {args.font} (pass --font with a font that covers your language)")
    renderer = Renderer(args.font, args.title, args.caption)
    for role, text, tools in parse(args.transcript.read_text(encoding="utf-8")):
        if role == "Developer":
            renderer.user(text)
        else:
            renderer.assistant(text, tools)
    renderer.frame(4000)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    renderer.save(args.output)
    size = args.output.stat().st_size / 1024
    print(f"wrote {args.output} ({len(renderer.frames)} frames, {size:.0f} KB)")


if __name__ == "__main__":
    main()
