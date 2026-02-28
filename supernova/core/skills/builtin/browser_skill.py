import re
from typing import Any
import httpx
from supernova.core.skills.base import BaseSkill, SkillManifest

class BrowserSkill(BaseSkill):
    def __init__(self):
        self.manifest = SkillManifest(
            name="browser",
            description="Fetch URLs and extract text content",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri"},
                    "timeout": {"type": "number", "default": 10},
                    "extract_text": {"type": "boolean", "default": True}
                },
                "required": ["url"]
            },
            required_permissions=["network"],
            risk_level="medium"
        )
    
    def _strip_html(self, html: str) -> str:
        """Basic HTML tag removal and text extraction."""
        # Remove script and style elements
        html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        html = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        html = re.sub(r'\s+', ' ', html).strip()
        return html
    
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        url = params["url"]
        timeout = params.get("timeout", 10)
        extract_text = params.get("extract_text", True)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content = response.text
                
                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": len(content)
                }
                
                if extract_text and "text/html" in result["content_type"]:
                    result["text"] = self._strip_html(content)
                else:
                    result["content"] = content
                
                return result
                
        except httpx.TimeoutException:
            return {"error": f"Request timed out after {timeout}s"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.reason_phrase}"}
        except Exception as e:
            return {"error": str(e)}