"""HTTP client for making API requests"""

import asyncio
import httpx
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from ..models.config import HostConfig
from ..models.scenario import ScenarioStep, HttpMethod


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
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
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
    ) -> Tuple[int, Dict[str, str], Any, float]:
        """Execute a scenario step with variable substitution"""
        
        # Apply delay before
        if step.delay_before > 0:
            await asyncio.sleep(step.delay_before)
        
        # Substitute variables in path, headers, params, body
        context = variables or {}
        
        path = self._substitute_variables(step.path, context)
        headers = self._substitute_dict(step.headers, context) if step.headers else None
        query_params = self._substitute_dict(step.query_params, context) if step.query_params else None
        body = self._substitute_value(step.body, context) if step.body is not None else None
        
        result = await self.execute_request(
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
        
        return result
    
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

