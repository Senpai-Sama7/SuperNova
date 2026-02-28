"""Tests for compute_salience (supernova/core/memory/salience.py).

All paths are pure Python — no mocking required.

ToT paths covered:
  A  Empty / too-short input                  -> 0.0
  B  Positive keywords                        -> score > 0
  C  Negative keywords                        -> score < 0
  D  Urgency keywords                         -> score > 0
  E  Neutral indicator penalty reduces score
  F  Score clamped to +1.0 upper bound
  G  Score clamped to -1.0 lower bound
  H  No matching keywords                     -> 0.0
  I  Mixed positive + negative                -> score between extremes
"""
from __future__ import annotations

import pytest
from supernova.core.memory.salience import compute_salience


# ---------------------------------------------------------------------------
# Path A: edge cases
# ---------------------------------------------------------------------------

def test_empty_string_returns_zero() -> None:
    assert compute_salience("") == 0.0


def test_whitespace_only_returns_zero() -> None:
    assert compute_salience("   ") == 0.0


def test_two_char_string_returns_zero() -> None:
    assert compute_salience("hi") == 0.0


# ---------------------------------------------------------------------------
# Path B: positive keywords
# ---------------------------------------------------------------------------

def test_love_keyword_produces_positive_score() -> None:
    assert compute_salience("I love this product.") > 0.0


def test_multiple_positive_keywords_compound() -> None:
    result = compute_salience("This is amazing and excellent work.")
    assert result > 0.0


# ---------------------------------------------------------------------------
# Path C: negative keywords
# ---------------------------------------------------------------------------

def test_hate_keyword_produces_negative_score() -> None:
    assert compute_salience("I hate this terrible experience.") < 0.0


def test_multiple_negative_keywords_compound() -> None:
    result = compute_salience("Awful horrible disaster failed completely.")
    assert result < 0.0


# ---------------------------------------------------------------------------
# Path D: urgency keywords
# ---------------------------------------------------------------------------

def test_critical_emergency_produces_positive_score() -> None:
    result = compute_salience("This is a critical emergency.")
    assert result > 0.0


def test_urgent_asap_produces_positive_score() -> None:
    result = compute_salience("Urgent response needed asap immediately.")
    assert result > 0.0


# ---------------------------------------------------------------------------
# Path E: neutral indicator penalty
# ---------------------------------------------------------------------------

def test_neutral_heavy_text_reduces_positive_score() -> None:
    # Pure keyword signal
    pure = compute_salience("love love love love")
    # Same keywords diluted by many neutral connector words
    diluted = compute_salience(
        "love the and or but if then when where how what why love function method class"
    )
    assert diluted <= pure


# ---------------------------------------------------------------------------
# Path F & G: clamping
# ---------------------------------------------------------------------------

def test_score_never_exceeds_positive_one() -> None:
    result = compute_salience(
        "love amazing fantastic brilliant wonderful excellent perfect great"
    )
    assert result <= 1.0


def test_score_never_below_negative_one() -> None:
    result = compute_salience(
        "hate terrible awful horrible disaster failed broken bad wrong"
    )
    assert result >= -1.0


# ---------------------------------------------------------------------------
# Path H: no matching keywords
# ---------------------------------------------------------------------------

def test_no_keyword_matches_returns_zero() -> None:
    result = compute_salience(
        "the quick brown fox jumps over the lazy dog"
    )
    assert result == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# Path I: mixed positive and negative
# ---------------------------------------------------------------------------

def test_mixed_keywords_score_between_extremes() -> None:
    pure_pos = compute_salience("love amazing excellent")
    pure_neg = compute_salience("hate terrible awful")
    mixed = compute_salience("love hate amazing terrible")
    assert pure_neg < mixed < pure_pos
