---
name: android-instructor-led-curriculum
description: Work with the "Android Instructor-Led Curriculum" PPTX slide deck set (typically delivered as a zip, e.g. `Android-Instructor-Led-Curriculum-v1.0.zip`). Use when you need to index the lessons, extract slide text/speaker notes, and generate instructor artifacts (agenda, lesson plan, labs, quizzes, homework) that reference lesson numbers and slide ranges. Use when you need to answer questions like "What does Lesson 8 cover?" or "Make a 2-day workshop plan using these decks."
---

# Android Instructor Led Curriculum

## Overview

Use the bundled scripts to extract text from `.pptx` files inside the curriculum zip (no third-party deps) and then generate teaching materials that stay traceable to the source decks.

## Quick Start

Assume the zip is at:
- `/home/donovan/Downloads/Android-Instructor-Led-Curriculum-v1.0.zip`

Index the zip (lesson list + slide counts):
```bash
python3 /home/donovan/.codex/skills/android-instructor-led-curriculum/scripts/index_curriculum.py \
  /home/donovan/Downloads/Android-Instructor-Led-Curriculum-v1.0.zip
```

Extract slide text for a lesson (first N slides):
```bash
python3 /home/donovan/.codex/skills/android-instructor-led-curriculum/scripts/pptx_text_dump.py \
  --zip /home/donovan/Downloads/Android-Instructor-Led-Curriculum-v1.0.zip \
  --entry "Android-Instructor-Led-Curriculum-v1.0/Lesson 4 Build your first Android app.pptx" \
  --max-slides 10
```

Include speaker notes if present:
```bash
python3 /home/donovan/.codex/skills/android-instructor-led-curriculum/scripts/pptx_text_dump.py \
  --zip /home/donovan/Downloads/Android-Instructor-Led-Curriculum-v1.0.zip \
  --entry "Android-Instructor-Led-Curriculum-v1.0/Lesson 8 App architecture (UI Layer).pptx" \
  --notes --max-slides 10
```

## Workflow

### 1) Identify the right lesson(s)

1. Run `scripts/index_curriculum.py` on the zip.
2. Pick lessons by topic and time constraints.
3. When asked for "beginner / 1-day / 2-day", prefer Lessons 0-6 and only bring in later lessons if time remains.

Reference: `references/curriculum_index.md` (generated from the v1.0 zip).

### 2) Extract an outline you can cite

1. Dump slide text for each selected lesson with `scripts/pptx_text_dump.py`.
2. Convert that dump into:
   - a short lesson summary
   - a section-by-section outline
   - a timebox estimate (roughly: slides / 2-3 minutes, adjusted for demos)
3. Keep traceability: cite `Lesson N` and (if helpful) slide numbers.

### 3) Generate instructor artifacts

Depending on the request, generate one of:
- **Agenda**: day-by-day schedule with breaks, demos, labs, and review blocks.
- **Lesson plan**: learning objectives, key concepts, misconceptions, checks-for-understanding.
- **Lab plan**: prerequisites, starter code expectations, steps, acceptance criteria, extensions.
- **Quiz**: 10-20 questions with answer key (mix: multiple choice + short answer + "spot the bug").

### 4) Keep outputs compatible with PPTX edits

If the user asks to modify or generate slides, use the separate `pptx` skill; this skill is primarily for indexing/extraction and building instructor-facing materials.

## Resources

### scripts/
- `scripts/index_curriculum.py`: list lessons in a curriculum zip, include slide counts.
- `scripts/pptx_text_dump.py`: extract slide text (and optional notes) to Markdown.

### references/
- `references/curriculum_index.md`: lesson/topic/slide-count index for the v1.0 zip.
