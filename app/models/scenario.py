"""Scenario models"""

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class HttpMethod(str, Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AssertionOperator(str, Enum):
    """Assertion operators"""
    EQ = "eq"  # equal
    NE = "ne"  # not equal
    GT = "gt"  # greater than
    LT = "lt"  # less than
    GTE = "gte"  # greater than or equal
    LTE = "lte"  # less than or equal
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"
    EXISTS = "exists"


class Assertion(BaseModel):
    """Assertion for response validation"""
    field: str = Field(..., description="Field to check (e.g., 'status', 'body.user.id')")
    operator: AssertionOperator = Field(..., description="Comparison operator")
    value: Any = Field(default=None, description="Expected value")
    message: Optional[str] = Field(default=None, description="Custom error message")


class ScenarioStep(BaseModel):
    """Single step in a scenario"""
    name: str = Field(..., description="Step name")
    method: HttpMethod = Field(..., description="HTTP method")
    path: str = Field(..., description="API path")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Additional headers")
    query_params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")
    body: Optional[Any] = Field(default=None, description="Request body")
    timeout: Optional[int] = Field(default=None, description="Request timeout override")
    delay_before: Optional[float] = Field(default=0, description="Delay before request (seconds)")
    delay_after: Optional[float] = Field(default=0, description="Delay after request (seconds)")
    assertions: List[Assertion] = Field(default_factory=list, description="Response assertions")
    extract: Optional[Dict[str, str]] = Field(default=None, description="Extract variables from response")
    skip_on_failure: bool = Field(default=False, description="Continue scenario if step fails")
    retry: int = Field(default=0, description="Number of retries on failure")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Create User",
                "method": "POST",
                "path": "/api/users",
                "body": {
                    "username": "testuser",
                    "email": "test@example.com"
                },
                "assertions": [
                    {"field": "status", "operator": "eq", "value": 201},
                    {"field": "body.id", "operator": "exists"}
                ],
                "extract": {
                    "user_id": "body.id"
                }
            }
        }


class Scenario(BaseModel):
    """Test scenario"""
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(default=None, description="Scenario description")
    host: Optional[str] = Field(default=None, description="Host to use (default if not specified)")
    variables: Optional[Dict[str, Any]] = Field(default=None, description="Scenario variables")
    steps: List[ScenarioStep] = Field(..., description="Scenario steps", min_length=1)
    tags: List[str] = Field(default_factory=list, description="Scenario tags")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "User Registration Flow",
                "description": "Complete user registration and profile setup",
                "steps": []
            }
        }


class LoadTestConfig(BaseModel):
    """Load test configuration"""
    duration_seconds: int = Field(..., description="Test duration in seconds", gt=0)
    target_tps: int = Field(..., description="Target transactions per second", gt=0)
    ramp_up_seconds: int = Field(default=0, description="Ramp up time in seconds", ge=0)
    max_concurrent: int = Field(default=100, description="Maximum concurrent requests", gt=0)
    distribution: Literal["constant", "linear", "exponential"] = Field(
        default="constant", 
        description="Load distribution pattern"
    )

