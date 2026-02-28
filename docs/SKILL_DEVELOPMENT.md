# Skill Development Guide

## Overview

Skills are modular components that extend SuperNova's capabilities. Each skill inherits from `BaseSkill` and implements the `execute()` method.

## Creating a Skill

### 1. Basic Structure

```python
from typing import Any
from supernova.core.skills.base import BaseSkill, SkillManifest

class MySkill(BaseSkill):
    def __init__(self):
        self.manifest = SkillManifest(
            name="my-skill",
            description="What this skill does",
            version="0.1.0",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input parameter"}
                },
                "required": ["input"]
            },
            risk_level="low"  # low/medium/high/critical
        )
    
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        # Your implementation here
        return {"result": "success"}
```

### 2. Manifest Format

- `name`: Unique skill identifier (kebab-case)
- `description`: Brief explanation of functionality
- `version`: Semantic version string
- `parameters`: JSON Schema for input validation
- `required_permissions`: List of required system permissions
- `risk_level`: Security classification

### 3. Sandbox Constraints

Skills run in a sandboxed environment with:
- 30-second execution timeout (configurable)
- Memory and CPU limits
- Restricted file system access
- Network access controls
- Audit logging of all operations

### 4. Execution

Use `sandboxed_execute()` to run skills safely:

```python
from supernova.core.skills.sandbox import sandboxed_execute

result = await sandboxed_execute(skill, params, timeout=30.0)
```

### 5. Quick Example

```python
class GreetingSkill(BaseSkill):
    def __init__(self):
        self.manifest = SkillManifest(
            name="greeting",
            description="Generate personalized greetings",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                },
                "required": ["name"]
            }
        )
    
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name", "World")
        return {"greeting": f"Hello, {name}!"}
```

## Best Practices

- Keep skills focused on single responsibilities
- Validate input parameters thoroughly
- Handle errors gracefully
- Use appropriate risk levels
- Document parameters clearly
- Test with various inputs