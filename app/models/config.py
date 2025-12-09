"""Configuration models"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, HttpUrl


class HostConfig(BaseModel):
    """Host configuration"""
    base_url: str = Field(..., description="Base URL of the API")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    headers: Dict[str, str] = Field(default_factory=dict, description="Default headers")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    auth: Optional[Dict[str, Any]] = Field(default=None, description="Authentication config")
    
    class Config:
        json_schema_extra = {
            "example": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "REST-API-Simulator/1.0"
                },
                "verify_ssl": True
            }
        }


class ProjectConfig(BaseModel):
    """Project configuration"""
    name: str = Field(..., description="Project name")
    hosts: Dict[str, HostConfig] = Field(..., description="Host configurations")
    default_host: str = Field(default="default", description="Default host to use")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Global variables")

