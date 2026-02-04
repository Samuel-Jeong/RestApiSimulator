"""Environment models for variable management"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class Environment(BaseModel):
    """Environment configuration with variables"""
    name: str = Field(..., description="Environment name")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Environment variables")
    params: Dict[str, Any] = Field(default_factory=dict, description="Request parameter defaults (auto-mapped by field name)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "development",
                "variables": {
                    "base_url": "https://api.dev.example.com",
                    "api_key": "dev-api-key-123",
                    "tenant_id": "tenant-001",
                    "timeout": 30
                },
                "params": {
                    "userId": "test-user-001",
                    "deviceId": "device-12345"
                }
            }
        }
