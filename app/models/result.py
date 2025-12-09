"""Test result models"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TestStatus(str, Enum):
    """Test status"""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    """Result of a single step"""
    step_name: str
    method: str
    url: str
    status: TestStatus
    status_code: Optional[int] = None
    response_time_ms: float
    request_headers: Dict[str, str]
    request_body: Optional[Any] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[Any] = None
    error_message: Optional[str] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    assertion_details: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_variables: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ScenarioResult(BaseModel):
    """Result of a scenario execution"""
    scenario_name: str
    status: TestStatus
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    steps: List[StepResult]
    variables: Dict[str, Any] = Field(default_factory=dict)
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    error_requests: int = 0


class LoadTestMetrics(BaseModel):
    """Load test metrics"""
    timestamp: datetime
    elapsed_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_requests: int
    current_tps: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    active_connections: int


class LoadTestResult(BaseModel):
    """Load test result"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    target_tps: int
    actual_avg_tps: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_requests: int
    success_rate: float
    response_times: List[float] = Field(default_factory=list)
    status_code_distribution: Dict[int, int] = Field(default_factory=dict)
    error_distribution: Dict[str, int] = Field(default_factory=dict)
    metrics_timeline: List[LoadTestMetrics] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TestReport(BaseModel):
    """Complete test report"""
    report_id: str
    test_type: str  # "scenario", "load", "tps"
    project_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    scenario_results: List[ScenarioResult] = Field(default_factory=list)
    load_test_result: Optional[LoadTestResult] = None
    summary: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

