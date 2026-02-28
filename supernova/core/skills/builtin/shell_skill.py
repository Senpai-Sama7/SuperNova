from typing import Any
from supernova.core.skills.base import BaseSkill, SkillManifest
from supernova.core.security.sandbox import ExecutionSandbox

class ShellSkill(BaseSkill):
    def __init__(self):
        self.manifest = SkillManifest(
            name="shell",
            description="Execute whitelisted shell commands",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "string"}, "default": []},
                    "timeout": {"type": "number", "default": 10}
                },
                "required": ["command"]
            },
            required_permissions=["execute"],
            risk_level="high"
        )
        self.whitelist = {
            "ls", "pwd", "echo", "cat", "head", "tail", "grep", "find", 
            "wc", "sort", "uniq", "date", "whoami", "uname"
        }
    
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        command = params["command"]
        args = params.get("args", [])
        timeout = params.get("timeout", 10)
        
        if command not in self.whitelist:
            return {"error": f"Command '{command}' not in whitelist"}
        
        sandbox = ExecutionSandbox()
        full_command = [command] + args
        
        try:
            result = await sandbox.execute_command(
                full_command, 
                timeout=timeout,
                capture_output=True
            )
            
            return {
                "command": " ".join(full_command),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "exit_code": result.get("exit_code", 0),
                "execution_time": result.get("execution_time", 0)
            }
        except Exception as e:
            return {"error": str(e)}