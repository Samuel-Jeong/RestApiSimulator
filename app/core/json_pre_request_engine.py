"""JSON-based pre-request execution engine"""

import base64
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
    ) -> tuple[Dict[str, Any], list[Dict[str, Any]]]:
        """
        Execute a JSON pre-request configuration
        
        Args:
            config_name: Name of the config file (e.g., "pre_request.json")
            environment_vars: Environment variables
            scenario_vars: Scenario variables
            
        Returns:
            Tuple of (extracted_variables, step_infos)
        """
        config_path = self.package_library_path / config_name
        
        if not config_path.exists():
            return {}, []
        
        step_infos = []
        
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
                step_results, step_info = self._execute_step(step, all_vars)
                results.update(step_results)
                all_vars.update(step_results)  # Make results available for next steps
                step_infos.append(step_info)
            
            print(f"✅ Pre-request config '{config.name}' executed successfully")
            if results:
                print(f"   Extracted variables: {', '.join(results.keys())}")
            
            return results, step_infos
            
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
            raise
    
    def _execute_step(
        self,
        step: PreRequestStep,
        variables: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a single pre-request step
        
        Args:
            step: Pre-request step configuration
            variables: Available variables for resolution
            
        Returns:
            Tuple of (extracted_variables, step_info)
            step_info contains: url, status_code, response_time_ms, method, error
        """
        import time
        
        step_info = {
            'step_name': step.name,
            'method': step.method,
            'url': step.url,
            'status_code': None,
            'response_time_ms': 0,
            'error': None
        }
        
        try:
            # Resolve variables in step configuration
            resolver = VariableResolver(variables)
            
            url = resolver.resolve(step.url)
            headers = resolver.resolve(step.headers) if step.headers else {}
            query_params = resolver.resolve(step.query_params) if step.query_params else {}
            body = resolver.resolve(step.body) if step.body is not None else None
            
            # Auto-encode Basic Auth if needed
            if 'Authorization' in headers:
                headers['Authorization'] = self._process_auth_header(headers['Authorization'])
            
            step_info['url'] = url
            
            print(f"   Executing: {step.name}")
            print(f"   → {step.method} {url}")
            
            # Execute HTTP request
            start_time = time.time()
            with httpx.Client(timeout=step.timeout, verify=False) as client:
                response = client.request(
                    method=step.method,
                    url=url,
                    headers=headers,
                    params=query_params,
                    json=body if body is not None else None
                )
            response_time_ms = (time.time() - start_time) * 1000
            
            step_info['status_code'] = response.status_code
            step_info['response_time_ms'] = response_time_ms
            
            print(f"   ← Status: {response.status_code} ({response_time_ms:.0f}ms)")
            
            # Extract variables from response
            results = {}
            if step.extract and response.status_code < 400:
                try:
                    response_data = response.json()
                    results = self._extract_variables(response_data, step.extract)
                    
                    if results:
                        for key, value in results.items():
                            print(f"   ✓ Extracted {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                    else:
                        # Extract가 정의되어 있지만 결과가 비어있으면 실패
                        error_msg = f"Extract configuration defined but no data extracted from response. Expected fields: {list(step.extract.keys())}"
                        print(f"")
                        print(f"   {'─'*55}")
                        print(f"   ❌ PACKAGE LIBRARY EXTRACTION FAILED")
                        print(f"   {'─'*55}")
                        print(f"   Step Name:   {step.name}")
                        print(f"   Error:       {error_msg}")
                        print(f"   {'─'*55}")
                        print(f"")
                        step_info['error'] = error_msg
                        raise ValueError(error_msg)
                        
                except ValueError:
                    # Re-raise ValueError for extraction failure
                    raise
                except Exception as e:
                    error_msg = f"Failed to extract variables: {e}"
                    print(f"   ⚠️  {error_msg}")
                    step_info['error'] = error_msg
                    raise ValueError(error_msg)
            elif step.extract:
                # Extract가 정의되어 있지만 응답이 실패
                error_msg = f"Cannot extract variables: HTTP {response.status_code}"
                print(f"   ⚠️  {error_msg}")
                step_info['error'] = error_msg
                raise ValueError(error_msg)
            
            return results, step_info
            
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
            step_info['error'] = str(e)
            raise
    
    def _process_auth_header(self, auth_value: str) -> str:
        """
        Process Authorization header and auto-encode Basic Auth if needed
        
        Args:
            auth_value: Authorization header value
            
        Returns:
            Processed authorization header value
        """
        if not isinstance(auth_value, str):
            return auth_value
        
        # Check if it's Basic Auth
        if not auth_value.startswith('Basic '):
            return auth_value
        
        credentials = auth_value[6:].strip()  # Remove "Basic " prefix
        
        # Check if already Base64 encoded (Base64 doesn't contain colons)
        # If it contains a colon, it's in "user:password" format and needs encoding
        if ':' in credentials:
            # Encode to Base64
            encoded = base64.b64encode(credentials.encode()).decode()
            return f"Basic {encoded}"
        
        # Already encoded or invalid format, return as-is
        return auth_value
    
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
