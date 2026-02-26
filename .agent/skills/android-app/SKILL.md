---
name: android-app
description: >
  Build, modify, or audit Android applications using Android Studio + Gradle, Jetpack Compose UI,
  modern app architecture, testing, performance, and quality best practices. Use when Codex is
  asked to create an Android app, add screens/navigation, integrate
  networking/persistence/repositories/WorkManager, add tests, tune performance, or align with
  Android "excellent" quality guidance. Use when a PPTX curriculum zip (Android Instructor-Led
  Curriculum) is provided and you need to map work to lessons and cite lesson/slide numbers.
---

# Android App

## Overview

Use official Android developer docs as the source of truth and use the curriculum slide decks as a teaching/traceability layer. Prefer extracting slide text/notes instead of guessing what a lesson covers.

## Inputs

- Android project repo path (if building/modifying an app)
- Optional curriculum zip:
  - `/home/donovan/Downloads/Android-Instructor-Led-Curriculum-v1.0.zip`

## Workflow

### 1) Clarify scope and constraints

Ask for:
- Target audience and primary user flow(s)
- Min Android version policy (`minSdk`)
- Whether this is a greenfield app or changes to an existing repo
- Requirements around offline mode, auth, analytics, and background work

### 2) Choose the implementation path

1. **Greenfield**: create a project structure aligned with Compose + modern architecture.
2. **Existing app**: audit, then implement incremental changes without rewriting everything.

Run `scripts/android_repo_audit.sh` early if you have a repo path.

### 3) Build UI intentionally (Compose-first)

Do:
- Prefer Compose UI and Material guidance.
- Keep screens composable and testable; push side effects to ViewModel/use-cases.

Avoid:
- Coupling network/db calls directly inside composables.

### 4) Use a layered architecture

Default layering (adapt as needed):
- UI layer (screens, state, navigation)
- Domain/use-cases (optional for complex apps)
- Data layer (repositories, network, persistence)

When the curriculum is available, map work to:
- Navigation/lifecycle lessons for screen flows
- Architecture lessons for UI/persistence/repositories
- Internet lesson for networking
- WorkManager lesson for background work

### 5) Testing, performance, and quality gates

Do:
- Add unit tests for core logic and UI state reducers.
- Add instrumentation tests for critical flows where appropriate.
- Use Android performance guidance for hotspots (startup, jank, memory).
- Align with Android "excellent" app quality guidance.

### 6) AI features (optional)

If asked to integrate AI features (Gemini/AI APIs), follow the official Android AI/Gemini guidance and keep the feature behind clear UX and failure handling.

## Curriculum Use (when the zip is provided)

Use the existing `android-instructor-led-curriculum` skill/scripts to extract slide text and cite sources.

Index:
```bash
python3 /home/donovan/.codex/skills/android-instructor-led-curriculum/scripts/index_curriculum.py \
  /home/donovan/Downloads/Android-Instructor-Led-Curriculum-v1.0.zip
```

Extract a lesson outline:
```bash
python3 /home/donovan/.codex/skills/android-instructor-led-curriculum/scripts/pptx_text_dump.py \
  --zip /home/donovan/Downloads/Android-Instructor-Led-Curriculum-v1.0.zip \
  --entry "Android-Instructor-Led-Curriculum-v1.0/Lesson 8 App architecture (UI Layer).pptx" \
  --max-slides 20
```

## References

Start with:
- `references/android_docs_links.md`
- `references/curriculum_lesson_map.md`

## Resources

### scripts/
- `scripts/android_repo_audit.sh`: quick, safe checks to understand what an Android repo looks like (Gradle files, Compose, tests, etc.).
- `scripts/predict_cmd_runner.py`: invoke OpenAI or Ollama without a full SDK; pass `--stack`, `--model`, and `--prompt` and let the script source `~/Documents/.cred/cred.txt` for `OPENAI_API_KEY`/`OLLAMA_API_KEY`.

### references/
- `references/android_docs_links.md`: official docs links and when to consult them.
- `references/curriculum_lesson_map.md`: lesson-to-topic mapping for the provided slide decks.
