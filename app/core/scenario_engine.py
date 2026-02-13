"""Scenario execution engine"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from urllib.parse import urlencode
from ..models.scenario import Scenario, ScenarioStep
from ..models.result import StepResult, ScenarioResult, TestStatus, PreRequestResult
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
            
            # Add params to top-level variables for direct access ({{userId}} instead of {{env.userId}})
            if hasattr(self.environment, 'params') and self.environment.params:
                variables.update(self.environment.params)
        else:
            variables['env'] = {}
        
        # Execute pre-request scripts from scenario
        pre_request_scripts = scenario.pre_request_scripts or []
        
        # Fallback to deprecated pre_request_script parameter
        if pre_request_script and pre_request_script not in pre_request_scripts:
            pre_request_scripts.append(pre_request_script)
        
        # Collect pre-request results
        pre_request_results = []
        
        # Execute all pre-request scripts sequentially
        for script_name in pre_request_scripts:
            try:
                # Try JSON config first (*.json)
                if script_name.endswith('.json') and self.json_pre_request_engine:
                    print(f"")
                    print(f"🔧 Executing package library config: {script_name}")
                    print(f"{'─'*60}")
                    pre_request_vars, step_infos = self.json_pre_request_engine.execute_config(
                        script_name,
                        self.environment.variables if self.environment else {},
                        variables
                    )
                    # Merge pre-request results into env namespace
                    variables['env'].update(pre_request_vars)
                    
                    # Convert step_infos to PreRequestResult objects
                    for step_info in step_infos:
                        pre_req_result = PreRequestResult(
                            step_name=step_info['step_name'],
                            method=step_info['method'],
                            url=step_info['url'],
                            status=TestStatus.ERROR if step_info['error'] else TestStatus.SUCCESS,
                            status_code=step_info.get('status_code'),
                            response_time_ms=step_info.get('response_time_ms', 0),
                            extracted_variables=pre_request_vars if not step_info['error'] else {},
                            error_message=step_info.get('error')
                        )
                        pre_request_results.append(pre_req_result)
                        
                # Fallback to Python script (*.py)
                elif script_name.endswith('.py') and self.pre_request_engine:
                    print(f"")
                    print(f"🔧 Executing package library script: {script_name}")
                    print(f"{'─'*60}")
                    pre_request_vars, step_info = self.pre_request_engine.execute_script(
                        script_name,
                        self.environment.variables if self.environment else {},
                        variables
                    )
                    # Merge pre-request results into env namespace
                    variables['env'].update(pre_request_vars)
                    
                    # Convert step_info to PreRequestResult object
                    pre_req_result = PreRequestResult(
                        step_name=step_info['step_name'],
                        method=step_info['method'],
                        url=step_info['url'],
                        status=TestStatus.ERROR if step_info['error'] else TestStatus.SUCCESS,
                        status_code=step_info.get('status_code'),
                        response_time_ms=step_info.get('response_time_ms', 0),
                        extracted_variables=pre_request_vars,
                        error_message=step_info.get('error')
                    )
                    pre_request_results.append(pre_req_result)
                    
            except Exception as e:
                print(f"")
                print(f"{'='*60}")
                print(f"❌ PRE-REQUEST (PACKAGE LIBRARY) FAILED")
                print(f"{'='*60}")
                print(f"Script: {script_name}")
                print(f"Error:  {e}")
                print(f"{'='*60}")
                print(f"")
                
                # Create failed pre-request result
                failed_pre_req_result = PreRequestResult(
                    step_name=script_name,
                    method='JSON' if script_name.endswith('.json') else 'PYTHON',
                    url=script_name,
                    status=TestStatus.ERROR,
                    status_code=None,
                    response_time_ms=0,
                    extracted_variables={},
                    error_message=str(e)
                )
                pre_request_results.append(failed_pre_req_result)
                
                # Pre-request 실패 시 시나리오 API 요청 실행 안함 (무조건 중단)
                print(f"⚠️  Scenario steps will NOT be executed due to pre-request failure.")
                print(f"")
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                return ScenarioResult(
                    scenario_name=scenario.name,
                    status=TestStatus.ERROR,
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    steps=[],
                    pre_request_results=pre_request_results,
                    variables=variables,
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    error_requests=1
                )
        
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
            pre_request_results=pre_request_results,
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
                
                # Build URL for logging (query_params가 있으면 ?key=value 포함)
                url = f"{self.http_client.base_url}{step.path}"
                if resolved_query_params:
                    url = f"{url}?{urlencode(resolved_query_params, doseq=True)}"
                
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
                    request_query_params=resolved_query_params,  # Add query params
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
        resolver = VariableResolver(variables)
        resolved_headers = resolver.resolve(step.headers) if step.headers else {}
        resolved_query_params = resolver.resolve(step.query_params) if step.query_params else None
        resolved_body = resolver.resolve(step.body) if step.body is not None else None
        
        # Build URL (query_params가 있으면 ?key=value 포함)
        url = f"{self.http_client.base_url}{step.path}"
        if resolved_query_params:
            url = f"{url}?{urlencode(resolved_query_params, doseq=True)}"
        
        # Add prefix to distinguish API errors from package library errors
        error_prefix = "[API_REQUEST_ERROR] " if last_error and "[PACKAGE_LIBRARY_ERROR]" not in str(last_error) else ""
        
        return StepResult(
            step_name=step.name,
            method=step.method.value,
            url=url,
            status=TestStatus.ERROR,
            response_time_ms=0,
            request_headers=resolved_headers,
            request_query_params=resolved_query_params,
            request_body=resolved_body,
            error_message=f"{error_prefix}{last_error}" if error_prefix else last_error
        )

