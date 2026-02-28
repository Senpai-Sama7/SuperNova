"""Memory salience scoring utilities."""

import re
from typing import Dict, Set

# Emotional salience keywords with weights
SALIENCE_KEYWORDS: Dict[str, float] = {
    # Strong positive
    'love': 0.8, 'amazing': 0.7, 'excellent': 0.6, 'fantastic': 0.7, 'wonderful': 0.6,
    'brilliant': 0.6, 'perfect': 0.5, 'great': 0.4, 'good': 0.3,
    
    # Strong negative  
    'hate': -0.8, 'terrible': -0.7, 'awful': -0.7, 'horrible': -0.6, 'disaster': -0.6,
    'failed': -0.5, 'broken': -0.4, 'bad': -0.3, 'wrong': -0.3,
    
    # Urgency/importance
    'critical': 0.7, 'urgent': 0.6, 'emergency': 0.8, 'important': 0.5, 'priority': 0.5,
    'deadline': 0.4, 'asap': 0.6, 'immediately': 0.6,
    
    # Emotional intensity
    'shocked': 0.5, 'surprised': 0.4, 'confused': 0.3, 'frustrated': -0.4, 'angry': -0.5,
    'excited': 0.5, 'thrilled': 0.6, 'worried': -0.3, 'concerned': -0.3,
}

# Neutral indicators (reduce salience)
NEUTRAL_INDICATORS: Set[str] = {
    'the', 'and', 'or', 'but', 'if', 'then', 'when', 'where', 'how', 'what', 'why',
    'function', 'method', 'class', 'variable', 'return', 'import', 'from', 'def',
    'documentation', 'example', 'tutorial', 'guide', 'reference',
}


def compute_salience(text: str) -> float:
    """Compute emotional salience score for memory text.
    
    Args:
        text: Memory content to analyze
        
    Returns:
        Float between -1.0 and 1.0 indicating emotional salience
    """
    if not text or len(text.strip()) < 3:
        return 0.0
        
    # Normalize text
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    
    # Calculate base salience from keywords
    salience_sum = 0.0
    keyword_count = 0
    
    for word in words:
        if word in SALIENCE_KEYWORDS:
            salience_sum += SALIENCE_KEYWORDS[word]
            keyword_count += 1
    
    # Count neutral indicators
    neutral_count = sum(1 for word in words if word in NEUTRAL_INDICATORS)
    neutral_ratio = neutral_count / len(words)
    
    # Base score from keywords
    if keyword_count > 0:
        base_score = salience_sum / keyword_count
    else:
        base_score = 0.0
    
    # Reduce score for highly neutral content
    if neutral_ratio > 0.3:
        base_score *= (1.0 - neutral_ratio * 0.5)
    
    # Clamp to [-1.0, 1.0]
    return max(-1.0, min(1.0, base_score))