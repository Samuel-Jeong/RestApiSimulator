"""JSON-based pre-request execution engine"""

import httpx
import orjson
from pathlib import Path
from typing import Dict, Any
from ..models.pre_request import PreRequestConfig, PreRequestStep
from ..utils.variable_resolver import VariableResolver


class JsonPreRequestEngine:
    """Execute JSON-based pre-request configurations"""
    
    def __init__(self, project_path: str):
        """
        Initialize JSON pre-request engine
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.package_library_path = self.project_path / "package_library"
    
    def execute_config(
        self,
        config_name: str,
        environment_vars: Dict[str, Any],
        scenario_vars: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a JSON pre-request configuration
        
        Args:
            config_name: Name of the config file (e.g., "pre_request.json")
            environment_vars: Environment variables
            scenario_vars: Scenario variables
            
        Returns:
            Extracted variables from all steps
        """
        config_path = self.package_library_path / config_name
        
        if not config_path.exists():
            return {}
        
        try:
            # Load configuration
            with open(config_path, 'rb') as f:
                config_data = orjson.loads(f.read())
            
            config = PreRequestConfig(**config_data)
            
            # Initialize variables for resolution
            all_vars = {
                'env': environment_vars.copy(),
                **scenario_vars
            }
            
            # Execute all steps
            results = {}
            for step in config.steps:
                step_results = self._execute_step(step, all_vars)
                results.update(step_results)
                all_vars.update(step_results)  # Make results available for next steps
            
            print(f"✅ Pre-request config '{config.name}' executed successfully")
            if results:
                print(f"   Extracted variables: {', '.join(results.keys())}")
            
            return results
            
        except Exception as e:
            print(f"")
            print(f"{'='*60}")
            print(f"❌ PACKAGE LIBRARY EXECUTION FAILED")
            print(f"{'='*60}")
            print(f"Config File: {config_name}")
            print(f"Error Type:  {type(e).__name__}")
            print(f"Error:       {e}")
            print(f"{'='*60}")
            print(f"")
            return {}
    
    def _execute_step(
        self,
        step: PreRequestStep,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single pre-request step
        
        Args:
            step: Pre-request step configuration
            variables: Available variables for resolution
            
        Returns:
            Extracted variables from this step
        """
        try:
            # Resolve variables in step configuration
            resolver = VariableResolver(variables)
            
            url = resolver.resolve(step.url)
            headers = resolver.resolve(step.headers) if step.headers else {}
            query_params = resolver.resolve(step.query_params) if step.query_params else {}
            body = resolver.resolve(step.body) if step.body is not None else None
            
            print(f"   Executing: {step.name}")
            print(f"   → {step.method} {url}")
            
            # Execute HTTP request
            with httpx.Client(timeout=step.timeout, verify=False) as client:
                response = client.request(
                    method=step.method,
                    url=url,
                    headers=headers,
                    params=query_params,
                    json=body if body is not None else None
                )
            
            print(f"   ← Status: {response.status_code}")
            
            # Extract variables from response
            results = {}
            if step.extract and response.status_code < 400:
                try:
                    response_data = response.json()
                    results = self._extract_variables(response_data, step.extract)
                    
                    if results:
                        for key, value in results.items():
                            print(f"   ✓ Extracted {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                except Exception as e:
                    print(f"   ⚠️  Failed to extract variables: {e}")
            
            return results
            
        except Exception as e:
            print(f"")
            print(f"   {'─'*55}")
            print(f"   ❌ PACKAGE LIBRARY STEP FAILED")
            print(f"   {'─'*55}")
            print(f"   Step Name:   {step.name}")
            print(f"   Request:     {step.method} {step.url}")
            print(f"   Error Type:  {type(e).__name__}")
            print(f"   Error:       {e}")
            print(f"   {'─'*55}")
            print(f"")
            return {}
    
    def _extract_variables(
        self,
        response_data: Any,
        extract_config: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract variables from response data using JSON path
        
        Args:
            response_data: Response JSON data
            extract_config: Dictionary mapping variable names to JSON paths
            
        Returns:
            Extracted variables
        """
        results = {}
        
        for var_name, json_path in extract_config.items():
            try:
                value = self._get_by_path(response_data, json_path)
                if value is not None:
                    results[var_name] = value
            except Exception:
                # Skip if path not found
                pass
        
        return results
    
    def _get_by_path(self, data: Any, path: str) -> Any:
        """
        Get value from data using dot notation path
        
        Args:
            data: Data to traverse
            path: Dot notation path (e.g., 'data.user.id')
            
        Returns:
            Value at path or None
        """
        if not path:
            return data
        
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if 0 <= idx < len(current) else None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def has_config(self, config_name: str) -> bool:
        """Check if a config exists"""
        config_path = self.package_library_path / config_name
        return config_path.exists()
    
    def list_configs(self) -> list:
        """List all available JSON configs"""
        if not self.package_library_path.exists():
            return []
        
        return [
            f.name for f in self.package_library_path.glob("*.json")
            if f.is_file() and not f.name.startswith("_")
        ]
