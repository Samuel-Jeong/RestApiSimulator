"""Scenario execution engine"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from ..models.scenario import Scenario, ScenarioStep
from ..models.result import StepResult, ScenarioResult, TestStatus
from ..models.config import HostConfig
from ..models.environment import Environment
from .http_client import HttpClient
from .assertion_engine import AssertionEngine
from .pre_request_engine import PreRequestEngine
from .json_pre_request_engine import JsonPreRequestEngine
from ..utils.variable_resolver import VariableResolver


class ScenarioEngine:
    """Executes test scenarios"""
    
    def __init__(self, host_config: HostConfig, project_path: Optional[str] = None, environment: Optional[Environment] = None):
        self.http_client = HttpClient(host_config)
        self.assertion_engine = AssertionEngine()
        self.project_path = project_path
        self.environment = environment
        self.pre_request_engine = PreRequestEngine(project_path) if project_path else None
        self.json_pre_request_engine = JsonPreRequestEngine(project_path) if project_path else None
    
    async def execute_scenario(
        self,
        scenario: Scenario,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        pre_request_script: Optional[str] = None
    ) -> ScenarioResult:
        """
        Execute a complete scenario
        
        Args:
            scenario: The scenario to execute
            progress_callback: Optional callback for progress updates (step_name, current, total)
            pre_request_script: Optional pre-request script to execute before scenario (deprecated, use scenario.pre_request_scripts)
        
        Returns:
            ScenarioResult with execution details
        """
        start_time = datetime.now()
        variables = scenario.variables.copy() if scenario.variables else {}
        
        # Add environment variables
        if self.environment:
            variables['env'] = self.environment.variables.copy()
        else:
            variables['env'] = {}
        
        # Execute pre-request scripts from scenario
        pre_request_scripts = scenario.pre_request_scripts or []
        
        # Fallback to deprecated pre_request_script parameter
        if pre_request_script and pre_request_script not in pre_request_scripts:
            pre_request_scripts.append(pre_request_script)
        
        # Execute all pre-request scripts sequentially
        for script_name in pre_request_scripts:
            try:
                # Try JSON config first (*.json)
                if script_name.endswith('.json') and self.json_pre_request_engine:
                    print(f"")
                    print(f"🔧 Executing package library config: {script_name}")
                    print(f"{'─'*60}")
                    pre_request_vars = self.json_pre_request_engine.execute_config(
                        script_name,
                        self.environment.variables if self.environment else {},
                        variables
                    )
                    # Merge pre-request results into env namespace
                    variables['env'].update(pre_request_vars)
                # Fallback to Python script (*.py)
                elif script_name.endswith('.py') and self.pre_request_engine:
                    print(f"")
                    print(f"🔧 Executing package library script: {script_name}")
                    print(f"{'─'*60}")
                    pre_request_vars = self.pre_request_engine.execute_script(
                        script_name,
                        self.environment.variables if self.environment else {},
                        variables
                    )
                    # Merge pre-request results into env namespace
                    variables['env'].update(pre_request_vars)
            except Exception as e:
                print(f"")
                print(f"{'='*60}")
                print(f"❌ PACKAGE LIBRARY EXECUTION FAILED")
                print(f"{'='*60}")
                print(f"Script: {script_name}")
                print(f"Error:  {e}")
                print(f"{'='*60}")
                print(f"")
                # Continue or stop based on scenario configuration
                if not scenario.continue_on_error:
                    # Re-raise with clear prefix for error tracking
                    raise Exception(f"[PACKAGE_LIBRARY_ERROR] {script_name}: {e}") from e
        
        steps_results = []
        
        total_steps = len(scenario.steps)
        scenario_status = TestStatus.SUCCESS
        
        for idx, step in enumerate(scenario.steps, 1):
            if progress_callback:
                progress_callback(step.name, idx, total_steps)
            
            step_result = await self._execute_step(step, variables)
            steps_results.append(step_result)
            
            # Update variables with extracted values (merge into env namespace)
            if step_result.extracted_variables:
                variables['env'].update(step_result.extracted_variables)
            
            # Check if we should continue
            if step_result.status == TestStatus.FAILURE:
                scenario_status = TestStatus.FAILURE
                # Continue if either scenario-level or step-level skip is enabled
                if not (scenario.continue_on_error or step.skip_on_failure):
                    break
            elif step_result.status == TestStatus.ERROR:
                scenario_status = TestStatus.ERROR
                # Continue if either scenario-level or step-level skip is enabled
                if not (scenario.continue_on_error or step.skip_on_failure):
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
                # Execute request (returns resolved values)
                status_code, response_headers, response_body, response_time_ms, \
                    resolved_headers, resolved_query_params, resolved_body = \
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
                    request_headers=resolved_headers,  # Use resolved headers
                    request_body=resolved_body,  # Use resolved body
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
        
        # All retries failed - resolve variables for logging
        url = f"{self.http_client.base_url}{step.path}"
        resolver = VariableResolver(variables)
        resolved_headers = resolver.resolve(step.headers) if step.headers else {}
        resolved_body = resolver.resolve(step.body) if step.body is not None else None
        
        # Add prefix to distinguish API errors from package library errors
        error_prefix = "[API_REQUEST_ERROR] " if last_error and "[PACKAGE_LIBRARY_ERROR]" not in str(last_error) else ""
        
        return StepResult(
            step_name=step.name,
            method=step.method.value,
            url=url,
            status=TestStatus.ERROR,
            response_time_ms=0,
            request_headers=resolved_headers,
            request_body=resolved_body,
            error_message=f"{error_prefix}{last_error}" if error_prefix else last_error
        )

