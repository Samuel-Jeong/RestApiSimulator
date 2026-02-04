"""HTTP client for making API requests"""

import asyncio
import httpx
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from ..models.config import HostConfig
from ..models.scenario import ScenarioStep, HttpMethod
from ..utils.variable_resolver import VariableResolver


class HttpClient:
    """Async HTTP client wrapper"""
    
    def __init__(self, host_config: HostConfig):
        self.host_config = host_config
        self.base_url = host_config.base_url.rstrip('/')
        self.default_headers = host_config.headers.copy()
        self.timeout = host_config.timeout
        self.verify_ssl = host_config.verify_ssl
    
    async def execute_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, Dict[str, str], Any, float]:
        """
        Execute HTTP request
        
        Returns:
            Tuple of (status_code, response_headers, response_body, response_time_ms)
        """
        url = f"{self.base_url}{path}"
        
        # Merge headers
        req_headers = self.default_headers.copy()
        if headers:
            req_headers.update(headers)
        
        # Determine timeout
        req_timeout = timeout if timeout is not None else self.timeout
        
        start_time = datetime.now()
        
        try:
            # DEBUG: Log actual headers being sent
            print(f"")
            print(f"{'='*80}")
            print(f"🔍 DEBUG - Actual HTTP Request Headers")
            print(f"{'='*80}")
            print(f"Method: {method.upper()}")
            print(f"URL: {url}")
            print(f"Headers:")
            for key, value in req_headers.items():
                if key.lower() == 'authorization':
                    # Mask sensitive auth data but show format
                    if value.startswith('Basic '):
                        print(f"  {key}: Basic {value[6:16]}...")
                    elif value.startswith('Bearer '):
                        print(f"  {key}: Bearer {value[7:17]}...")
                    else:
                        print(f"  {key}: {value[:20]}...")
                else:
                    print(f"  {key}: {value}")
            print(f"{'='*80}")
            print(f"")
            
            # Disable HTTP/2 to preserve header case sensitivity
            async with httpx.AsyncClient(
                verify=self.verify_ssl,
                http2=False
            ) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=req_headers,
                    params=query_params,
                    json=body if body is not None else None,
                    timeout=req_timeout
                )
                
                end_time = datetime.now()
                response_time_ms = (end_time - start_time).total_seconds() * 1000
                
                # Parse response body
                try:
                    response_body = response.json()
                except:
                    response_body = response.text
                
                return (
                    response.status_code,
                    dict(response.headers),
                    response_body,
                    response_time_ms
                )
        
        except httpx.TimeoutException as e:
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            raise TimeoutError(f"Request timeout after {req_timeout}s") from e
        
        except Exception as e:
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            raise RuntimeError(f"Request failed: {str(e)}") from e
    
    async def execute_step(
        self,
        step: ScenarioStep,
        variables: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, str], Any, float, Dict[str, Any], Dict[str, Any], Any]:
        """Execute a scenario step with variable substitution
        
        Args:
            step: Scenario step to execute
            variables: Variables for substitution (includes env.params)
        
        Returns:
            Tuple of (status_code, response_headers, response_body, response_time_ms, 
                     resolved_headers, resolved_query_params, resolved_body)
        """
        
        # Apply delay before
        if step.delay_before > 0:
            await asyncio.sleep(step.delay_before)
        
        # Substitute variables in path, headers, params, body using VariableResolver
        context = variables or {}
        resolver = VariableResolver(context)
        
        # DEBUG: Log variable context
        print(f"")
        print(f"{'='*80}")
        print(f"🔍 DEBUG - Variable Resolution Context")
        print(f"{'='*80}")
        print(f"Available variables (top-level keys): {list(context.keys())}")
        if 'env' in context and isinstance(context['env'], dict):
            print(f"Environment variables: {list(context['env'].keys())}")
        print(f"{'='*80}")
        print(f"")
        
        path = resolver.resolve(step.path)
        headers = resolver.resolve(step.headers) if step.headers else None
        query_params = resolver.resolve(step.query_params) if step.query_params else None
        body = resolver.resolve(step.body) if step.body is not None else None
        
        # DEBUG: Log resolved headers
        print(f"")
        print(f"{'='*80}")
        print(f"🔍 DEBUG - Header Resolution")
        print(f"{'='*80}")
        print(f"Original headers: {step.headers}")
        print(f"Resolved headers: {headers}")
        print(f"{'='*80}")
        print(f"")
        
        status_code, response_headers, response_body, response_time_ms = await self.execute_request(
            method=step.method.value,
            path=path,
            headers=headers,
            query_params=query_params,
            body=body,
            timeout=step.timeout
        )
        
        # Apply delay after
        if step.delay_after > 0:
            await asyncio.sleep(step.delay_after)
        
        # Return both response and resolved request data
        return (status_code, response_headers, response_body, response_time_ms, 
                headers or {}, query_params or {}, body)
    
    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Substitute variables in text using {{variable}} syntax"""
        if not isinstance(text, str):
            return text
        
        result = text
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result
    
    def _substitute_dict(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute variables in dictionary"""
        result = {}
        for key, value in data.items():
            result[key] = self._substitute_value(value, context)
        return result
    
    def _substitute_value(self, value: Any, context: Dict[str, Any]) -> Any:
        """Substitute variables in any value"""
        if isinstance(value, str):
            return self._substitute_variables(value, context)
        elif isinstance(value, dict):
            return self._substitute_dict(value, context)
        elif isinstance(value, list):
            return [self._substitute_value(item, context) for item in value]
        else:
            return value

