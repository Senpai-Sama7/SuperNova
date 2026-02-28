import asyncio
import time
import logging
from typing import Any
from .base import BaseSkill

logger = logging.getLogger(__name__)

async def sandboxed_execute(skill: BaseSkill, params: dict, timeout: float = 30.0) -> dict:
    """Execute skill with timeout, error handling, and audit logging."""
    start_time = time.time()
    
    try:
        logger.info(f"Executing skill: {skill.manifest.name} with params: {params}")
        
        async with asyncio.timeout(timeout):
            result = await skill.execute(params)
            
        execution_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Skill {skill.manifest.name} completed in {execution_time}ms")
        
        return {
            "status": "success",
            "result": result,
            "error": None,
            "execution_time_ms": execution_time
        }
        
    except asyncio.TimeoutError:
        execution_time = int((time.time() - start_time) * 1000)
        logger.error(f"Skill {skill.manifest.name} timed out after {timeout}s")
        return {
            "status": "timeout",
            "result": None,
            "error": f"Execution timed out after {timeout}s",
            "execution_time_ms": execution_time
        }
        
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        logger.error(f"Skill {skill.manifest.name} failed: {str(e)}")
        return {
            "status": "error",
            "result": None,
            "error": str(e),
            "execution_time_ms": execution_time
        }