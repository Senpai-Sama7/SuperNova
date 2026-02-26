"""
Safety Layer / Policy Engine

Enforces safety policies across all MCP servers.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    WARN = "warn"
    LOG = "log"


@dataclass
class Policy:
    """Safety policy definition."""
    name: str
    description: str
    condition: str
    action: PolicyAction
    severity: str = "medium"  # low, medium, high, critical
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyEvaluation:
    """Result of policy evaluation."""
    allowed: bool
    action: PolicyAction
    triggered_policies: List[Policy]
    messages: List[str]
    risk_score: int = 0


class PolicyEngine:
    """Engine for evaluating safety policies."""
    
    # Built-in default policies
    DEFAULT_POLICIES = [
        Policy(
            name="no_production_secrets",
            description="Block hardcoded secrets in production paths",
            condition="path.contains('/prod/') and content.matches('password|secret|key')",
            action=PolicyAction.DENY,
            severity="critical",
            message="Hardcoded secrets not allowed in production paths"
        ),
        Policy(
            name="no_rm_rf_root",
            description="Block rm -rf on root directory",
            condition="command.matches('rm\\s+-rf\\s+/')",
            action=PolicyAction.DENY,
            severity="critical",
            message="Destructive command blocked"
        ),
        Policy(
            name="large_deletion_warning",
            description="Warn on large-scale deletions",
            condition="deletion.count > 100",
            action=PolicyAction.REQUIRE_APPROVAL,
            severity="high",
            message="Large deletion requires approval"
        ),
        Policy(
            name="high_risk_security_scan",
            description="Require approval for high-risk security issues",
            condition="security.risk_score > 75",
            action=PolicyAction.REQUIRE_APPROVAL,
            severity="high",
            message="High security risk detected"
        ),
        Policy(
            name="database_write_protection",
            description="Require approval for database writes",
            condition="db.operation in ['insert', 'update', 'delete'] and not context.test_mode",
            action=PolicyAction.REQUIRE_APPROVAL,
            severity="high",
            message="Database modification requires approval"
        ),
        Policy(
            name="test_coverage_threshold",
            description="Warn when test coverage is below threshold",
            condition="coverage.percent < 50",
            action=PolicyAction.WARN,
            severity="medium",
            message="Test coverage is below 50%"
        ),
        Policy(
            name="audit_all_destructive",
            description="Log all destructive operations",
            condition="operation.is_destructive",
            action=PolicyAction.LOG,
            severity="low",
            message="Destructive operation logged"
        ),
    ]
    
    def __init__(self, custom_policies: Optional[List[Policy]] = None):
        self.policies = self.DEFAULT_POLICIES.copy()
        if custom_policies:
            self.policies.extend(custom_policies)
        
        self.audit_log: List[Dict[str, Any]] = []
    
    def evaluate(self, context: Dict[str, Any], operation: str, params: Dict[str, Any]) -> PolicyEvaluation:
        """
        Evaluate policies against an operation.
        
        Args:
            context: Execution context (session_id, user, environment, etc.)
            operation: Operation being performed (e.g., "file/delete", "db/query")
            params: Operation parameters
        
        Returns:
            PolicyEvaluation result
        """
        triggered = []
        messages = []
        risk_score = 0
        
        for policy in self.policies:
            if self._check_condition(policy.condition, context, operation, params):
                triggered.append(policy)
                
                if policy.action in [PolicyAction.DENY, PolicyAction.REQUIRE_APPROVAL]:
                    messages.append(f"[{policy.severity.upper()}] {policy.message}")
                
                # Calculate risk score
                severity_weights = {"low": 1, "medium": 5, "high": 10, "critical": 25}
                risk_score += severity_weights.get(policy.severity, 1)
        
        # Determine final action
        if any(p.action == PolicyAction.DENY for p in triggered):
            final_action = PolicyAction.DENY
            allowed = False
        elif any(p.action == PolicyAction.REQUIRE_APPROVAL for p in triggered):
            final_action = PolicyAction.REQUIRE_APPROVAL
            allowed = False  # Until approved
        elif any(p.action == PolicyAction.WARN for p in triggered):
            final_action = PolicyAction.WARN
            allowed = True
        else:
            final_action = PolicyAction.ALLOW
            allowed = True
        
        # Log evaluation
        self._log_evaluation(context, operation, params, triggered, allowed)
        
        return PolicyEvaluation(
            allowed=allowed,
            action=final_action,
            triggered_policies=triggered,
            messages=messages,
            risk_score=risk_score
        )
    
    def _check_condition(self, condition: str, context: Dict[str, Any], operation: str, params: Dict[str, Any]) -> bool:
        """Evaluate a policy condition."""
        # Create evaluation context
        eval_context = {
            "context": context,
            "operation": operation,
            "params": params,
            "path": params.get("path", params.get("file", "")),
            "command": params.get("command", ""),
            "content": params.get("content", ""),
        }
        
        # Parse simple conditions
        # Format: "condition.matches('pattern')"
        # Format: "value > threshold"
        
        try:
            # Check for .matches() conditions
            match_pattern = r"(\w+)\.matches\(['\"]([^'\"]+)['\"]\)"
            matches = re.findall(match_pattern, condition)
            
            for var, pattern in matches:
                value = str(eval_context.get(var, ""))
                if re.search(pattern, value, re.IGNORECASE):
                    return True
            
            # Check for .contains() conditions
            contains_pattern = r"(\w+)\.contains\(['\"]([^'\"]+)['\"]\)"
            contains = re.findall(contains_pattern, condition)
            
            for var, substring in contains:
                value = str(eval_context.get(var, ""))
                if substring in value:
                    return True
            
            # Check for comparison conditions
            # e.g., "coverage.percent < 50"
            comp_pattern = r"(\w+(?:\.\w+)*)\s*([<>=!]+)\s*(\d+)"
            comps = re.findall(comp_pattern, condition)
            
            for var, op, val in comps:
                actual_val = self._get_nested_value(eval_context, var)
                if actual_val is not None:
                    try:
                        actual_num = float(actual_val)
                        compare_num = float(val)
                        
                        if op == "<" and actual_num < compare_num:
                            return True
                        elif op == ">" and actual_num > compare_num:
                            return True
                        elif op == "==" and actual_num == compare_num:
                            return True
                        elif op == "<=" and actual_num <= compare_num:
                            return True
                        elif op == ">=" and actual_num >= compare_num:
                            return True
                    except (ValueError, TypeError):
                        pass
            
            # Check for 'in' conditions
            # e.g., "db.operation in ['insert', 'update']"
            in_pattern = r"(\w+(?:\.\w+)*)\s+in\s+\[([^\]]+)\]"
            in_checks = re.findall(in_pattern, condition)
            
            for var, values_str in in_checks:
                actual_val = self._get_nested_value(eval_context, var)
                values = [v.strip().strip('"\'') for v in values_str.split(",")]
                if str(actual_val) in values:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get a nested dictionary value by dot path."""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            if value is None:
                return None
        return value
    
    def _log_evaluation(self, context: Dict, operation: str, params: Dict, 
                        policies: List[Policy], allowed: bool) -> None:
        """Log policy evaluation."""
        log_entry = {
            "timestamp": context.get("timestamp"),
            "session_id": context.get("session_id"),
            "user_id": context.get("user_id"),
            "operation": operation,
            "allowed": allowed,
            "triggered_policies": [p.name for p in policies],
            "risk_score": sum({"low": 1, "medium": 5, "high": 10, "critical": 25}.get(p.severity, 1) for p in policies)
        }
        
        self.audit_log.append(log_entry)
        
        if policies:
            logger.info(f"Policy evaluation: {operation} - {len(policies)} policies triggered - allowed={allowed}")
    
    def add_policy(self, policy: Policy) -> None:
        """Add a custom policy."""
        self.policies.append(policy)
        logger.info(f"Added policy: {policy.name}")
    
    def remove_policy(self, name: str) -> bool:
        """Remove a policy by name."""
        for i, policy in enumerate(self.policies):
            if policy.name == name:
                self.policies.pop(i)
                logger.info(f"Removed policy: {name}")
                return True
        return False
    
    def get_audit_log(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit log, optionally filtered by session."""
        if session_id:
            return [entry for entry in self.audit_log if entry.get("session_id") == session_id]
        return self.audit_log.copy()
    
    def export_policies(self) -> str:
        """Export policies to JSON."""
        policy_dicts = []
        for p in self.policies:
            policy_dicts.append({
                "name": p.name,
                "description": p.description,
                "condition": p.condition,
                "action": p.action.value,
                "severity": p.severity,
                "message": p.message
            })
        return json.dumps(policy_dicts, indent=2)
    
    def import_policies(self, json_str: str) -> None:
        """Import policies from JSON."""
        policy_dicts = json.loads(json_str)
        for pd in policy_dicts:
            policy = Policy(
                name=pd["name"],
                description=pd["description"],
                condition=pd["condition"],
                action=PolicyAction(pd["action"]),
                severity=pd.get("severity", "medium"),
                message=pd.get("message", "")
            )
            self.add_policy(policy)


class SafetyMiddleware:
    """Middleware that wraps MCP server calls with safety checks."""
    
    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine
    
    def wrap_request(self, context: Dict[str, Any], server_name: str, tool_name: str, 
                     params: Dict[str, Any]) -> PolicyEvaluation:
        """
        Wrap an MCP request with safety evaluation.
        
        Args:
            context: Execution context
            server_name: Name of MCP server
            tool_name: Name of tool being called
            params: Tool parameters
        
        Returns:
            PolicyEvaluation result
        """
        operation = f"{server_name}/{tool_name}"
        
        # Add operation metadata
        enriched_context = context.copy()
        enriched_context["timestamp"] = __import__('time').time()
        
        # Evaluate policies
        result = self.policy_engine.evaluate(enriched_context, operation, params)
        
        return result


# Example usage and configuration
EXAMPLE_POLICY_CONFIG = """
policies:
  - name: block_production_deployment_on_weekend
    description: Prevent production deployments on weekends
    condition: "operation == 'execution/deploy' and context.day in ['Saturday', 'Sunday']"
    action: deny
    severity: high
    message: "Production deployments not allowed on weekends"
  
  - name: require_tests_before_merge
    description: Require passing tests before merging to main
    condition: "operation == 'git/merge' and params.target == 'main' and not context.tests_passed"
    action: deny
    severity: high
    message: "Tests must pass before merging to main"
  
  - name: warn_on_large_file_writes
    description: Warn when writing large files
    condition: "params.content.length > 10000"
    action: warn
    severity: low
    message: "Large file write detected"
"""


def main():
    """Demo the policy engine."""
    engine = PolicyEngine()
    
    # Test evaluation
    context = {
        "session_id": "test-123",
        "user_id": "user-456",
        "environment": "production"
    }
    
    # Test 1: Safe operation
    result = engine.evaluate(context, "file/read", {"path": "/project/src/main.py"})
    print(f"Test 1 - Safe operation: allowed={result.allowed}")
    
    # Test 2: Dangerous command
    result = engine.evaluate(context, "execution/execute", {"command": "rm -rf /"})
    print(f"Test 2 - Dangerous command: allowed={result.allowed}, messages={result.messages}")
    
    # Test 3: High security risk
    result = engine.evaluate(context, "qa/security_scan", {"security.risk_score": 85})
    print(f"Test 3 - High security risk: allowed={result.allowed}, action={result.action.value}")
    
    # Print audit log
    print("\nAudit Log:")
    for entry in engine.get_audit_log():
        print(f"  {entry['operation']}: allowed={entry['allowed']}, risk={entry['risk_score']}")


if __name__ == "__main__":
    main()
