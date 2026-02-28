import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any
from supernova.core.skills.base import BaseSkill, SkillManifest

class EmailSkill(BaseSkill):
    def __init__(self):
        self.manifest = SkillManifest(
            name="email",
            description="Send emails via SMTP",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["compose", "send"]},
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "html": {"type": "boolean", "default": False}
                },
                "required": ["action"]
            },
            required_permissions=["network"],
            risk_level="medium"
        )
    
    def _get_smtp_config(self):
        return {
            "host": os.getenv("SMTP_HOST", "localhost"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        }
    
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        action = params["action"]
        
        if action == "compose":
            return {
                "template": {
                    "to": params.get("to", ""),
                    "subject": params.get("subject", ""),
                    "body": params.get("body", ""),
                    "html": params.get("html", False)
                }
            }
        
        elif action == "send":
            config = self._get_smtp_config()
            if not config["username"] or not config["password"]:
                return {"error": "SMTP credentials not configured"}
            
            msg = MIMEMultipart()
            msg["From"] = config["username"]
            msg["To"] = params["to"]
            msg["Subject"] = params["subject"]
            
            body_type = "html" if params.get("html") else "plain"
            msg.attach(MIMEText(params["body"], body_type))
            
            with smtplib.SMTP(config["host"], config["port"]) as server:
                if config["use_tls"]:
                    server.starttls()
                server.login(config["username"], config["password"])
                server.send_message(msg)
            
            return {"sent": True, "to": params["to"]}