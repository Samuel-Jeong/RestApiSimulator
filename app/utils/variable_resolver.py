"""Variable resolution and substitution utilities"""

import re
from typing import Any, Dict, Optional


class VariableResolver:
    """Resolve variables in strings and data structures"""
    
    # Pattern to match {{variable_name}} or {{env.variable_name}}
    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')
    
    def __init__(self, variables: Dict[str, Any]):
        """
        Initialize resolver with variables
        
        Args:
            variables: Dictionary of variables to resolve (includes env.params at top level)
        """
        self.variables = variables
    
    def resolve(self, value: Any) -> Any:
        """
        Resolve variables in a value
        
        Args:
            value: Value to resolve (can be str, dict, list, or primitive)
            
        Returns:
            Resolved value with variables substituted
        """
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(item) for item in value]
        else:
            return value
    
    def _resolve_string(self, text: str, max_depth: int = 10) -> Any:
        """
        Resolve variables in a string recursively
        
        Args:
            text: String containing {{variable}} references
            max_depth: Maximum recursion depth to prevent infinite loops
            
        Returns:
            Resolved string or value
        """
        if max_depth <= 0:
            # Prevent infinite recursion
            return text
        
        # Check if entire string is a single variable reference
        match = self.VARIABLE_PATTERN.fullmatch(text)
        if match:
            var_path = match.group(1).strip()
            value = self._get_variable_value(var_path)
            if value is not None:
                # If resolved value is a string with variables, resolve recursively
                if isinstance(value, str) and self.VARIABLE_PATTERN.search(value):
                    return self._resolve_string(value, max_depth - 1)
                return value
            return text
        
        # Replace all variable references in string
        def replace_var(match):
            var_path = match.group(1).strip()
            value = self._get_variable_value(var_path)
            return str(value) if value is not None else match.group(0)
        
        resolved = self.VARIABLE_PATTERN.sub(replace_var, text)
        
        # If resolved string still contains variables, resolve recursively
        if resolved != text and self.VARIABLE_PATTERN.search(resolved):
            return self._resolve_string(resolved, max_depth - 1)
        
        return resolved
    
    def _get_variable_value(self, var_path: str) -> Optional[Any]:
        """
        Get variable value by path (e.g., 'user.id' or 'env.api_key')
        
        Args:
            var_path: Variable path with dot notation
            
        Returns:
            Variable value or None if not found
        """
        parts = var_path.split('.')
        value = self.variables
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                # Fallback: if not found at root and there's no dot notation,
                # try looking in 'env' namespace
                if len(parts) == 1 and 'env' in self.variables:
                    env_value = self.variables['env'].get(var_path)
                    if env_value is not None:
                        return env_value
                return None
        
        return value
    
    def add_variables(self, new_vars: Dict[str, Any]) -> None:
        """Add or update variables"""
        self.variables.update(new_vars)
    
    def has_unresolved_variables(self, text: str) -> bool:
        """Check if string has unresolved variables"""
        if not isinstance(text, str):
            return False
        return bool(self.VARIABLE_PATTERN.search(text))
