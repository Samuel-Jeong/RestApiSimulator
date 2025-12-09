"""Scenario execution engine"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from ..models.scenario import Scenario, ScenarioStep
from ..models.result import StepResult, ScenarioResult, TestStatus
from ..models.config import HostConfig
from .http_client import HttpClient
from .assertion_engine import AssertionEngine


class ScenarioEngine:
    """Executes test scenarios"""
    
    def __init__(self, host_config: HostConfig):
        self.http_client = HttpClient(host_config)
        self.assertion_engine = AssertionEngine()
    
    async def execute_scenario(
        self,
        scenario: Scenario,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> ScenarioResult:
        """
        Execute a complete scenario
        
        Args:
            scenario: The scenario to execute
            progress_callback: Optional callback for progress updates (step_name, current, total)
        
        Returns:
            ScenarioResult with execution details
        """
        start_time = datetime.now()
        variables = scenario.variables.copy() if scenario.variables else {}
        steps_results = []
        
        total_steps = len(scenario.steps)
        scenario_status = TestStatus.SUCCESS
        
        for idx, step in enumerate(scenario.steps, 1):
            if progress_callback:
                progress_callback(step.name, idx, total_steps)
            
            step_result = await self._execute_step(step, variables)
            steps_results.append(step_result)
            
            # Update variables with extracted values
            if step_result.extracted_variables:
                variables.update(step_result.extracted_variables)
            
            # Check if we should continue
            if step_result.status == TestStatus.FAILURE:
                scenario_status = TestStatus.FAILURE
                if not step.skip_on_failure:
                    break
            elif step_result.status == TestStatus.ERROR:
                scenario_status = TestStatus.ERROR
                if not step.skip_on_failure:
                    break
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        total_requests = len(steps_results)
        successful = sum(1 for s in steps_results if s.status == TestStatus.SUCCESS)
        failed = sum(1 for s in steps_results if s.status == TestStatus.FAILURE)
        errors = sum(1 for s in steps_results if s.status == TestStatus.ERROR)
        
        return ScenarioResult(
            scenario_name=scenario.name,
            status=scenario_status,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            steps=steps_results,
            variables=variables,
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            error_requests=errors
        )
    
    async def _execute_step(
        self,
        step: ScenarioStep,
        variables: Dict[str, Any]
    ) -> StepResult:
        """Execute a single step with retry logic"""
        
        attempts = step.retry + 1
        last_error = None
        
        for attempt in range(attempts):
            try:
                # Execute request
                status_code, response_headers, response_body, response_time_ms = \
                    await self.http_client.execute_step(step, variables)
                
                # Build URL for logging
                url = f"{self.http_client.base_url}{step.path}"
                
                # Validate assertions
                assertions_passed = 0
                assertions_failed = 0
                assertion_details = []
                
                if step.assertions:
                    assertions_passed, assertions_failed, assertion_details = \
                        self.assertion_engine.validate_all(
                            step.assertions,
                            status_code,
                            response_body
                        )
                
                # Extract variables
                extracted_vars = {}
                if step.extract:
                    for var_name, field_path in step.extract.items():
                        value = self.assertion_engine.get_field_value(
                            {"body": response_body}, field_path
                        )
                        if value is not None:
                            extracted_vars[var_name] = value
                
                # Determine status
                if assertions_failed > 0:
                    status = TestStatus.FAILURE
                else:
                    status = TestStatus.SUCCESS
                
                return StepResult(
                    step_name=step.name,
                    method=step.method.value,
                    url=url,
                    status=status,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    request_headers=step.headers or {},
                    request_body=step.body,
                    response_headers=response_headers,
                    response_body=response_body,
                    assertions_passed=assertions_passed,
                    assertions_failed=assertions_failed,
                    assertion_details=assertion_details,
                    extracted_variables=extracted_vars
                )
            
            except Exception as e:
                last_error = str(e)
                
                # If not last attempt, wait before retry
                if attempt < attempts - 1:
                    await asyncio.sleep(1)
        
        # All retries failed
        url = f"{self.http_client.base_url}{step.path}"
        
        return StepResult(
            step_name=step.name,
            method=step.method.value,
            url=url,
            status=TestStatus.ERROR,
            response_time_ms=0,
            request_headers=step.headers or {},
            request_body=step.body,
            error_message=last_error
        )

