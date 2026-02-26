#!/usr/bin/env python3
"""Android App Builder MCP Server - provides curriculum and docs search tools."""

import os
import re
from pathlib import Path
from mcp.server.fastmcp import FastMCP

CURRICULUM_DIR = Path(os.environ.get(
    "ANDROID_CURRICULUM_DIR",
    os.path.expanduser("~/Downloads/Android-Instructor-Led-Curriculum-v1.0")
))
DOCS_DIR = Path(__file__).parent / "docs"

# Pre-load content at startup
_lessons: dict[str, str] = {}
_docs: dict[str, str] = {}

def _load():
    for f in sorted(CURRICULUM_DIR.glob("*.txt")):
        _lessons[f.stem] = f.read_text(errors="replace")
    for f in sorted(DOCS_DIR.glob("*.md")):
        _docs[f.stem] = f.read_text(errors="replace")

_load()

mcp = FastMCP("android-app-builder")

LESSON_BUCKETS = {
    "Kotlin Fundamentals": ["Lesson 1", "Lesson 2", "Lesson 3"],
    "First App & Layouts": ["Lesson 4", "Lesson 5"],
    "Navigation & Flow": ["Lesson 6", "Lesson 7"],
    "Architecture & UI Layer": ["Lesson 8"],
    "Data Persistence": ["Lesson 9"],
    "RecyclerView": ["Lesson 10"],
    "Networking & Data": ["Lesson 11"],
    "Architecture & Background Work": ["Lesson 12"],
    "App UI Design": ["Lesson 13"],
}

DOC_LINKS = {
    "Android Studio Intro": "https://developer.android.com/studio/intro",
    "Gemini in Android": "https://developer.android.com/gemini-in-android",
    "UI Design": "https://developer.android.com/design/ui",
    "AI on Android": "https://developer.android.com/ai",
    "Excellent Experiences": "https://developer.android.com/quality/excellent",
    "Gradle API Reference": "https://developer.android.com/reference/tools/gradle-api",
    "Android Tools": "https://developer.android.com/tools",
    "Performance Overview": "https://developer.android.com/topic/performance/overview",
    "Testing": "https://developer.android.com/training/testing",
    "Gradle Build Overview": "https://developer.android.com/build/gradle-build-overview",
}


@mcp.tool()
def search_android_curriculum(query: str, max_results: int = 5) -> str:
    """Search across all curriculum lessons and doc summaries for a topic.
    Returns matching excerpts with lesson/doc attribution."""
    query_lower = query.lower()
    terms = query_lower.split()
    hits = []
    for name, content in {**_lessons, **_docs}.items():
        lower = content.lower()
        score = sum(lower.count(t) for t in terms)
        if score > 0:
            # Find best matching paragraph
            best_para, best_score = "", 0
            for para in re.split(r'\n\s*\n', content):
                ps = sum(para.lower().count(t) for t in terms)
                if ps > best_score:
                    best_para, best_score = para, ps
            hits.append((score, name, best_para.strip()[:600]))
    hits.sort(key=lambda x: -x[0])
    if not hits:
        return "No results found. Try different search terms."
    lines = []
    for score, name, excerpt in hits[:max_results]:
        lines.append(f"### {name} (relevance: {score})\n{excerpt}\n")
    return "\n".join(lines)


@mcp.tool()
def get_lesson(lesson_number: int) -> str:
    """Get the full content of a specific curriculum lesson (1-13).
    Also accepts 0 for the Introduction."""
    if lesson_number == 0:
        key = "Introduction_ Android Development with Kotlin"
    else:
        matches = [k for k in _lessons if k.startswith(f"Lesson {lesson_number}")]
        if not matches:
            return f"Lesson {lesson_number} not found. Available: 0 (Intro), 1-13."
        key = matches[0]
    return f"# {key}\n\n{_lessons[key]}"


@mcp.tool()
def list_lessons() -> str:
    """List all available curriculum lessons with their topics and bucket groupings."""
    lines = ["# Curriculum Lessons\n"]
    for name in sorted(_lessons.keys()):
        lines.append(f"- {name}")
    lines.append("\n# Topic Buckets\n")
    for bucket, lessons in LESSON_BUCKETS.items():
        lines.append(f"**{bucket}**: {', '.join(lessons)}")
    return "\n".join(lines)


@mcp.tool()
def get_android_doc_reference(topic: str = "") -> str:
    """Get official Android developer documentation links and summaries.
    Optionally filter by topic keyword."""
    if topic:
        topic_lower = topic.lower()
        # Search doc summaries
        matches = {k: v for k, v in _docs.items() if topic_lower in v.lower()}
        links = {k: v for k, v in DOC_LINKS.items() if topic_lower in k.lower()}
        lines = []
        if links:
            lines.append("# Matching Doc Links")
            for name, url in links.items():
                lines.append(f"- [{name}]({url})")
        if matches:
            lines.append("\n# Matching Doc Summaries")
            for name, content in matches.items():
                lines.append(f"\n## {name}\n{content[:800]}")
        return "\n".join(lines) if lines else f"No docs matching '{topic}'. Try: studio, gradle, testing, performance, ui, design, ai"
    # Return all
    lines = ["# Official Android Documentation Links\n"]
    for name, url in DOC_LINKS.items():
        lines.append(f"- [{name}]({url})")
    lines.append("\n# Available Doc Summaries\n")
    for name in sorted(_docs.keys()):
        lines.append(f"- {name}")
    return "\n".join(lines)


@mcp.tool()
def map_request_to_buckets(requirements: str) -> str:
    """Given app requirements, map them to relevant curriculum buckets and doc references.
    Use this to plan which lessons and docs to consult before building an app."""
    req_lower = requirements.lower()
    keyword_map = {
        "Kotlin Fundamentals": ["kotlin", "variable", "function", "class", "object", "lambda", "null", "type"],
        "First App & Layouts": ["layout", "constraintlayout", "linearlayout", "view", "xml", "first app", "activity"],
        "Navigation & Flow": ["navigation", "fragment", "nav", "safeargs", "drawer", "bottom nav", "lifecycle"],
        "Architecture & UI Layer": ["viewmodel", "livedata", "ui layer", "data binding", "architecture"],
        "Data Persistence": ["room", "database", "dao", "entity", "persistence", "sqlite", "data layer"],
        "RecyclerView": ["recyclerview", "list", "adapter", "viewholder", "diffutil"],
        "Networking & Data": ["retrofit", "network", "api", "internet", "http", "json", "moshi"],
        "Architecture & Background Work": ["repository", "workmanager", "background", "sync", "coroutine", "worker"],
        "App UI Design": ["material", "theme", "style", "color", "typography", "design", "ui design"],
    }
    doc_keyword_map = {
        "Android Studio Intro": ["studio", "ide", "project", "emulator"],
        "Gradle Build Overview": ["gradle", "build", "dependency", "variant", "apk"],
        "Testing": ["test", "junit", "espresso", "instrumented"],
        "Performance Overview": ["performance", "memory", "battery", "render", "anr", "profile"],
        "UI Design": ["design", "material", "adaptive", "ui"],
        "Gemini in Android": ["gemini", "ai"],
    }
    matched_buckets = []
    for bucket, keywords in keyword_map.items():
        if any(kw in req_lower for kw in keywords):
            matched_buckets.append(bucket)
    matched_docs = []
    for doc, keywords in doc_keyword_map.items():
        if any(kw in req_lower for kw in keywords):
            matched_docs.append(doc)
    lines = [f"# Architecture Mapping for: {requirements}\n"]
    lines.append("## Relevant Curriculum Buckets")
    for b in (matched_buckets or ["Kotlin Fundamentals", "First App & Layouts"]):
        lessons = LESSON_BUCKETS.get(b, [])
        lines.append(f"- **{b}**: {', '.join(lessons)}")
    lines.append("\n## Relevant Documentation")
    for d in (matched_docs or ["Android Studio Intro", "Gradle Build Overview"]):
        lines.append(f"- [{d}]({DOC_LINKS.get(d, '')})")
    lines.append("\n## Recommended Architecture")
    lines.append("Fragment → ViewModel → Repository → Room DAO (local) / Retrofit (remote)")
    lines.append("WorkManager for background sync | Navigation Component for screen flow")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
