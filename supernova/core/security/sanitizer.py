"""supernova/core/security/sanitizer.py

ContentSanitizer: validates and cleans user-supplied text before it enters
the agent context window or is persisted as memory.  Defends against prompt
injection, PII leakage, control-character smuggling, and oversized payloads.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Tuple

# ── Pattern tables ────────────────────────────────────────────────────────────

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)\s+\w+", re.IGNORECASE),
    re.compile(r"(?:system|assistant)\s*:\s*", re.IGNORECASE),
    re.compile(r"<\s*(?:system|assistant|user)\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>"),
    re.compile(r"(?:jailbreak|DAN mode|do\s+anything\s+now)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:your\s+)?(?:previous\s+)?(?:instructions?|training)", re.IGNORECASE),
]

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_PII_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b")),
    (
        "API_KEY",
        re.compile(r"\b(?:sk|pk|api)[_\-](?:live|test|prod)?[_\-]?[A-Za-z0-9]{20,}\b"),
    ),
    ("AWS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
]


# ── Result dataclass ──────────────────────────────────────────────────────────


@dataclass
class SanitizationResult:
    """Output of a single ContentSanitizer.sanitize() call."""

    text: str
    was_modified: bool
    warnings: List[str]
    injection_detected: bool
    pii_detected: List[str]

    @property
    def is_clean(self) -> bool:
        """True when no injection pattern or PII was found."""
        return not self.injection_detected and not self.pii_detected


# ── Sanitizer ─────────────────────────────────────────────────────────────────


class ContentSanitizer:
    """Validates and normalises user-supplied text for safe agent consumption.

    Passes applied in order:
    1. Unicode NFC normalisation (collapses visually identical glyphs).
    2. Control-character stripping (prevents terminal-escape attacks).
    3. Length enforcement (prevents context-window flooding).
    4. Prompt-injection pattern detection.
    5. PII pattern detection and optional redaction.

    Example::

        sanitizer = ContentSanitizer(max_length=32_000, redact_pii=True)
        result = sanitizer.sanitize(user_message, context_label="chat")
        if result.injection_detected:
            raise PermissionError("Prompt injection blocked")
        safe_text = result.text

    Args:
        max_length: Hard character limit; excess is truncated. Default 32 000.
        strip_control_chars: Remove ASCII control characters. Default True.
        redact_pii: Replace detected PII with ``[REDACTED_<TYPE>]``. Default False.
        block_on_injection: Raise ValueError on injection detection. Default False
            (callers should check ``result.injection_detected`` themselves).
    """

    def __init__(
        self,
        max_length: int = 32_000,
        strip_control_chars: bool = True,
        redact_pii: bool = False,
        block_on_injection: bool = False,
    ) -> None:
        self.max_length = max_length
        self.strip_control_chars = strip_control_chars
        self.redact_pii = redact_pii
        self.block_on_injection = block_on_injection

    def sanitize(self, text: str, context_label: str = "input") -> SanitizationResult:
        """Run all sanitisation passes on *text*.

        Args:
            text: Raw user-supplied string.
            context_label: Short label used in warning messages
                (e.g. ``'chat_message'``, ``'tool_argument.query'``).

        Returns:
            SanitizationResult with the cleaned string and audit metadata.

        Raises:
            ValueError: If ``block_on_injection=True`` and injection is detected.
        """
        warnings: List[str] = []
        was_modified = False
        injection_detected = False
        pii_found: List[str] = []

        # Pass 1 — Unicode normalisation
        normalized = unicodedata.normalize("NFC", text)
        if normalized != text:
            was_modified = True

        # Pass 2 — control-character removal
        if self.strip_control_chars:
            cleaned = _CONTROL_CHARS.sub("", normalized)
            if cleaned != normalized:
                warnings.append(f"{context_label}: control characters removed")
                was_modified = True
                normalized = cleaned

        # Pass 3 — length enforcement
        if len(normalized) > self.max_length:
            normalized = normalized[: self.max_length]
            warnings.append(
                f"{context_label}: truncated to {self.max_length} characters"
            )
            was_modified = True

        # Pass 4 — injection detection
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(normalized):
                injection_detected = True
                warnings.append(
                    f"{context_label}: prompt injection pattern detected"
                    f" (pattern: {pattern.pattern[:60]})"
                )
                break

        if injection_detected and self.block_on_injection:
            raise ValueError(
                f"Prompt injection detected in {context_label}: "
                + "; ".join(warnings)
            )

        # Pass 5 — PII detection / redaction
        for label, pattern in _PII_PATTERNS:
            if pattern.search(normalized):
                pii_found.append(label)
                warnings.append(f"{context_label}: {label} pattern detected")
                if self.redact_pii:
                    normalized = pattern.sub(f"[REDACTED_{label}]", normalized)
                    was_modified = True

        return SanitizationResult(
            text=normalized,
            was_modified=was_modified,
            warnings=warnings,
            injection_detected=injection_detected,
            pii_detected=pii_found,
        )

    def is_safe(self, text: str) -> bool:
        """Quick boolean check — True only when no injection or PII is detected."""
        return self.sanitize(text).is_clean
