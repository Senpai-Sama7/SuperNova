from typing import Any

def generate_skill_template(name: str, description: str) -> str:
    """Generate a Python file string with BaseSkill subclass boilerplate."""
    class_name = ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))
    
    return f'''from typing import Any
from supernova.core.skills.base import BaseSkill, SkillManifest

class {class_name}(BaseSkill):
    def __init__(self):
        self.manifest = SkillManifest(
            name="{name}",
            description="{description}",
            version="0.1.0",
            parameters={{
                "type": "object",
                "properties": {{
                    # Define your input parameters here
                }},
                "required": []
            }}
        )
    
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the {name} skill."""
        # Implement your skill logic here
        return {{"message": "Skill executed successfully"}}
'''