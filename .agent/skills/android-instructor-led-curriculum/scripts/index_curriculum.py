#!/usr/bin/env python3
"""
Index the Android Instructor-Led Curriculum zip and emit a small JSON/Markdown summary.

Input is expected to be a .zip containing .pptx files (the curriculum).
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from typing import Any
from xml.etree import ElementTree as ET


_A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _extract_first_slide_title(pptx_bytes: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(pptx_bytes)) as zf:
            slide1 = "ppt/slides/slide1.xml"
            if slide1 not in zf.namelist():
                return ""
            root = ET.fromstring(zf.read(slide1))
            parts = [t.text.strip() for t in root.iter(f"{_A_NS}t") if t.text and t.text.strip()]
            if not parts:
                return ""
            # Heuristic: first non-trivial line is the "title".
            joined = " ".join(parts)
            return joined[:200]
    except Exception:
        return ""


def _count_slides(pptx_bytes: bytes) -> int:
    try:
        with zipfile.ZipFile(io.BytesIO(pptx_bytes)) as zf:
            pat = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
            nums = []
            for n in zf.namelist():
                m = pat.match(n)
                if m:
                    nums.append(int(m.group(1)))
            return max(nums) if nums else 0
    except Exception:
        return 0


@dataclass(frozen=True)
class Lesson:
    lesson_number: int | None
    kind: str  # intro | lesson | other
    topic: str
    zip_entry: str
    size_bytes: int
    slide_count: int
    first_slide_text: str


_LESSON_RE = re.compile(r"^Lesson\s+(\d+)\s+(.*)$", re.IGNORECASE)


def _parse_name(base_name: str) -> tuple[int | None, str, str]:
    # Return (lesson_number, kind, topic)
    if base_name.lower().startswith("introduction"):
        return (0, "intro", base_name)
    m = _LESSON_RE.match(base_name)
    if m:
        return (int(m.group(1)), "lesson", m.group(2).strip())
    return (None, "other", base_name)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Index a curriculum zip of PPTX files.")
    p.add_argument("zip_path", help="Path to curriculum zip (e.g. Android-Instructor-Led-Curriculum-v1.0.zip).")
    p.add_argument("--json", action="store_true", help="Emit JSON (default: Markdown).")
    p.add_argument("--no-first-slide", action="store_true", help="Skip extracting first-slide text.")
    return p.parse_args(argv)


def _to_markdown(lessons: list[Lesson]) -> str:
    out: list[str] = []
    out.append("# Android Instructor-Led Curriculum (Index)")
    out.append("")
    out.append("| Lesson | Topic | Slides | PPTX |")
    out.append("|---:|---|---:|---|")
    for l in lessons:
        num = "" if l.lesson_number is None else str(l.lesson_number)
        topic = l.topic.replace("|", "\\|")
        out.append(f"| {num} | {topic} | {l.slide_count} | `{l.zip_entry}` |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ns = _parse_args(argv)
    lessons: list[Lesson] = []

    with zipfile.ZipFile(ns.zip_path) as zf:
        entries = [i for i in zf.infolist() if i.filename.lower().endswith(".pptx")]
        entries.sort(key=lambda i: i.filename)

        for info in entries:
            base = info.filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            lesson_number, kind, topic = _parse_name(base)

            pptx_bytes = zf.read(info.filename)
            slide_count = _count_slides(pptx_bytes)
            first_slide_text = "" if ns.no_first_slide else _extract_first_slide_title(pptx_bytes)

            lessons.append(
                Lesson(
                    lesson_number=lesson_number,
                    kind=kind,
                    topic=topic,
                    zip_entry=info.filename,
                    size_bytes=info.file_size,
                    slide_count=slide_count,
                    first_slide_text=first_slide_text,
                )
            )

    # Sort by lesson_number if present, otherwise by name.
    lessons.sort(key=lambda l: (10_000 if l.lesson_number is None else l.lesson_number, l.topic))

    if ns.json:
        payload: list[dict[str, Any]] = [asdict(l) for l in lessons]
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_to_markdown(lessons))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

