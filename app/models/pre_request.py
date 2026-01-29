"""Pre-request models for JSON-based pre-request configuration"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field


class PreRequestStep(BaseModel):
    """Single pre-request step (HTTP request)"""
    name: str = Field(..., description="Step name for logging")
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = Field(..., description="HTTP method")
    url: str = Field(..., description="Request URL (supports {{variable}} syntax)")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Request headers")
    query_params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")
    body: Optional[Any] = Field(default=None, description="Request body")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    extract: Optional[Dict[str, str]] = Field(
        default=None, 
        description="Extract variables from response (key: var_name, value: json_path)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Get Auth Token",
                "method": "POST",
                "url": "{{env.base_url}}/api/v1/auth/token",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "username": "{{env.username}}",
                    "password": "{{env.password}}"
                },
                "extract": {
                    "auth_token": "data.token",
                    "user_id": "data.user.id"
                }
            }
        }


class PreRequestConfig(BaseModel):
    """Pre-request configuration"""
    name: str = Field(..., description="Pre-request configuration name")
    description: Optional[str] = Field(default=None, description="Configuration description")
    steps: List[PreRequestStep] = Field(..., description="List of pre-request steps to execute")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Authentication Flow",
                "description": "Get authentication token before test execution",
                "steps": [
                    {
                        "name": "Get Auth Token",
                        "method": "POST",
                        "url": "{{env.base_url}}/api/v1/auth/token",
                        "body": {
                            "username": "{{env.username}}",
                            "password": "{{env.password}}"
                        },
                        "extract": {
                            "auth_token": "data.token"
                        }
                    }
                ]
            }
        }
