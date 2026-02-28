"""supernova/core/security/sanitizer.py

ContentSanitizer validates and normalises user-supplied text before it enters
the agent context window or is persisted as memory. Defends against prompt
injection, PII exposure, and oversized payloads.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Compiled pattern registries
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)\s+\w+", re.IGNORECASE),
    re.compile(r"(?:system|assistant)\s*:\s*", re.IGNORECASE),
    re.compile(r"<\s*(?:system|assistant|user)\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
    re.compile(r"(?:jailbreak|DAN\b|do\s+anything\s+now)", re.IGNORECASE),
    re.compile(r"prompt\s+injection", re.IGNORECASE),
]

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_PII_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b")),
    (
        "API_KEY",
        re.compile(r"\b(?:sk|pk|api|token)[-_](?:live|test|prod)?[-_]?[A-Za-z0-9]{20,}\b"),
    ),
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class SanitizationResult:
    """Outcome of a single sanitization pass.

    Attributes:
        text: The (possibly modified) output string.
        was_modified: True if any transformation was applied.
        warnings: Human-readable descriptions of each finding.
        injection_detected: True if a prompt-injection pattern matched.
        pii_detected: Labels of each PII category found (e.g. ``['SSN']``).
    """

    text: str
    was_modified: bool
    warnings: List[str]
    injection_detected: bool
    pii_detected: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """True when no injection or PII was detected."""
        return not self.injection_detected and not self.pii_detected


# ---------------------------------------------------------------------------
# Sanitizer
# ---------------------------------------------------------------------------


class ContentSanitizer:
    """Validates and normalises user-supplied text for safe agent consumption.

    Example::

        sanitizer = ContentSanitizer(max_length=32_000)
        result = sanitizer.sanitize(raw_input)
        if result.injection_detected:
            raise PermissionError("Prompt injection blocked")
        safe_text = result.text

    Args:
        max_length: Hard truncation limit in characters. Default 32 000.
        strip_control_chars: Remove ASCII control characters. Default True.
        redact_pii: Replace detected PII with ``[REDACTED_<LABEL>]``. Default False.
        block_on_injection: Flag injection; callers decide whether to raise.
    """

    def __init__(
        self,
        max_length: int = 32_000,
        strip_control_chars: bool = True,
        redact_pii: bool = False,
        block_on_injection: bool = True,
    ) -> None:
        self.max_length = max_length
        self.strip_control_chars = strip_control_chars
        self.redact_pii = redact_pii
        self.block_on_injection = block_on_injection

    def sanitize(self, text: str, context_label: str = "input") -> SanitizationResult:
        """Run all sanitization passes over *text*.

        Args:
            text: Raw user-supplied string.
            context_label: Label included in warning messages for traceability.

        Returns:
            :class:`SanitizationResult` with cleaned text and audit metadata.
        """
        warnings: List[str] = []
        was_modified = False
        injection_detected = False
        pii_found: List[str] = []

        # 1. Unicode normalisation (NFC)
        out = unicodedata.normalize("NFC", text)
        if out != text:
            was_modified = True

        # 2. Strip control characters
        if self.strip_control_chars:
            cleaned = _CONTROL_CHAR_RE.sub("", out)
            if cleaned != out:
                warnings.append(f"{context_label}: control characters removed")
                was_modified = True
                out = cleaned

        # 3. Enforce length limit
        if len(out) > self.max_length:
            out = out[: self.max_length]
            warnings.append(f"{context_label}: truncated to {self.max_length} chars")
            was_modified = True

        # 4. Detect prompt injection
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(out):
                injection_detected = True
                warnings.append(f"{context_label}: prompt injection pattern detected")
                break

        # 5. Detect (and optionally redact) PII
        for label, pattern in _PII_PATTERNS:
            if pattern.search(out):
                pii_found.append(label)
                warnings.append(f"{context_label}: {label} pattern detected")
                if self.redact_pii:
                    out = pattern.sub(f"[REDACTED_{label}]", out)
                    was_modified = True

        return SanitizationResult(
            text=out,
            was_modified=was_modified,
            warnings=warnings,
            injection_detected=injection_detected,
            pii_detected=pii_found,
        )

    def is_safe(self, text: str) -> bool:
        """Convenience method: True only if sanitize() detects no threats."""
        return self.sanitize(text).is_clean
