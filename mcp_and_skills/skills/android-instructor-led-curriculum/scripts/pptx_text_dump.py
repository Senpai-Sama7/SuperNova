#!/usr/bin/env python3
"""
Extract slide text (and optionally speaker notes) from a .pptx and output Markdown.

Design goals:
- No third-party dependencies (pptx files are ZIPs of OOXML).
- Good-enough text extraction for outlines, agendas, quizzes, and lesson plans.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from dataclasses import dataclass
from typing import Iterable
from xml.etree import ElementTree as ET


_A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _read_zip_member(zf: zipfile.ZipFile, name: str) -> bytes:
    try:
        return zf.read(name)
    except KeyError:
        return b""


def _sorted_slide_xml_names(pptx_zf: zipfile.ZipFile, prefix: str) -> list[str]:
    # slide*.xml, notesSlide*.xml
    pat = re.compile(rf"^{re.escape(prefix)}(\d+)\.xml$")
    hits: list[tuple[int, str]] = []
    for n in pptx_zf.namelist():
        m = pat.match(n)
        if m:
            hits.append((int(m.group(1)), n))
    hits.sort(key=lambda t: t[0])
    return [n for _, n in hits]


def _extract_lines_from_xml(xml_bytes: bytes) -> list[str]:
    if not xml_bytes:
        return []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    lines: list[str] = []

    # Iterate paragraphs, collect all text runs beneath each paragraph.
    for p in root.iter():
        if p.tag != f"{_A_NS}p":
            continue
        parts: list[str] = []
        for t in p.iter(f"{_A_NS}t"):
            if t.text:
                parts.append(t.text.strip())
        line = " ".join([x for x in parts if x])
        if line:
            lines.append(line)

    # Fallback: if paragraph scan found nothing, grab all a:t.
    if not lines:
        parts = [t.text.strip() for t in root.iter(f"{_A_NS}t") if t.text and t.text.strip()]
        if parts:
            lines.append(" ".join(parts))

    # De-dupe adjacent identical lines (common in some PPTX exports).
    deduped: list[str] = []
    for ln in lines:
        if not deduped or deduped[-1] != ln:
            deduped.append(ln)
    return deduped


@dataclass(frozen=True)
class SlideText:
    slide_number: int
    lines: list[str]
    note_lines: list[str]


def extract_pptx_text(pptx_bytes: bytes, include_notes: bool) -> list[SlideText]:
    with zipfile.ZipFile(io.BytesIO(pptx_bytes)) as zf:
        slide_names = _sorted_slide_xml_names(zf, "ppt/slides/slide")
        note_names = _sorted_slide_xml_names(zf, "ppt/notesSlides/notesSlide") if include_notes else []

        slides: list[SlideText] = []
        for idx, slide_xml in enumerate(slide_names, start=1):
            slide_lines = _extract_lines_from_xml(_read_zip_member(zf, slide_xml))
            note_lines: list[str] = []
            if include_notes and idx <= len(note_names):
                note_lines = _extract_lines_from_xml(_read_zip_member(zf, note_names[idx - 1]))
            slides.append(SlideText(slide_number=idx, lines=slide_lines, note_lines=note_lines))
        return slides


def _md_escape(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def to_markdown(title: str, slides: Iterable[SlideText], include_notes: bool) -> str:
    out: list[str] = [f"# {_md_escape(title)}", ""]
    for st in slides:
        out.append(f"## Slide {st.slide_number}")
        if st.lines:
            for ln in st.lines:
                out.append(f"- {_md_escape(ln)}")
        else:
            out.append("- (no text detected)")

        if include_notes:
            out.append("")
            out.append("### Notes")
            if st.note_lines:
                for ln in st.note_lines:
                    out.append(f"- {_md_escape(ln)}")
            else:
                out.append("- (no notes detected)")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Dump PPTX slide text (and optionally notes) to Markdown without external deps."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--pptx", help="Path to a .pptx on disk.")
    src.add_argument("--zip", help="Path to a zip that contains .pptx files.")
    p.add_argument("--entry", help="When using --zip: the .pptx entry path inside the zip.")
    p.add_argument("--notes", action="store_true", help="Include speaker notes (if present).")
    p.add_argument("--max-slides", type=int, default=0, help="Limit number of slides (0 = all).")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    ns = _parse_args(argv)

    if ns.zip and not ns.entry:
        print("error: --entry is required when using --zip", file=sys.stderr)
        return 2

    if ns.pptx:
        pptx_path = ns.pptx
        title = pptx_path.rsplit("/", 1)[-1]
        with open(pptx_path, "rb") as f:
            pptx_bytes = f.read()
    else:
        zip_path = ns.zip
        entry = ns.entry
        title = entry.rsplit("/", 1)[-1]
        with zipfile.ZipFile(zip_path) as zf:
            try:
                pptx_bytes = zf.read(entry)
            except KeyError:
                print(f"error: entry not found in zip: {entry}", file=sys.stderr)
                return 2

    slides = extract_pptx_text(pptx_bytes, include_notes=bool(ns.notes))
    if ns.max_slides and ns.max_slides > 0:
        slides = slides[: ns.max_slides]

    sys.stdout.write(to_markdown(title=title, slides=slides, include_notes=bool(ns.notes)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

