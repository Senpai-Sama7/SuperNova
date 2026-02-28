from .pipeline import ReasoningDepth

def select_depth(query: str) -> ReasoningDepth:
    """
    Classify queries to select appropriate reasoning depth:
    - Short factual questions → FAST
    - Multi-step or "how to" → STANDARD  
    - Planning, analysis, comparison, "write a" → DEEP
    """
    query_lower = query.lower()
    
    # DEEP indicators - complex tasks requiring multiple passes
    deep_keywords = [
        "plan", "strategy", "analyze", "analysis", "compare", "comparison", 
        "evaluate", "evaluation", "write a", "create a", "design", "develop",
        "pros and cons", "advantages", "disadvantages", "trade-offs",
        "step by step", "detailed", "comprehensive", "thorough"
    ]
    
    # STANDARD indicators - multi-step but not complex analysis
    standard_keywords = [
        "how to", "explain", "describe", "process", "procedure", "method",
        "steps", "guide", "tutorial", "implement", "solve", "fix"
    ]
    
    # FAST indicators - simple factual queries
    fast_keywords = [
        "what is", "who is", "when", "where", "define", "definition",
        "yes or no", "true or false", "quick", "simple"
    ]
    
    # Check for DEEP first (most complex)
    if any(keyword in query_lower for keyword in deep_keywords):
        return ReasoningDepth.DEEP
    
    # Check for STANDARD
    if any(keyword in query_lower for keyword in standard_keywords):
        return ReasoningDepth.STANDARD
    
    # Check for FAST
    if any(keyword in query_lower for keyword in fast_keywords):
        return ReasoningDepth.FAST
    
    # Default heuristics based on query length and complexity
    if len(query) < 50:
        return ReasoningDepth.FAST
    elif len(query) < 150:
        return ReasoningDepth.STANDARD
    else:
        return ReasoningDepth.DEEP