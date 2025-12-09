"""Load testing and TPS testing engine"""

import asyncio
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from collections import defaultdict
from ..models.scenario import Scenario, LoadTestConfig
from ..models.result import LoadTestResult, LoadTestMetrics, TestStatus
from ..models.config import HostConfig
from .scenario_engine import ScenarioEngine


class LoadTestEngine:
    """Executes load tests and TPS tests"""
    
    def __init__(self, host_config: HostConfig):
        self.host_config = host_config
        self.scenario_engine = ScenarioEngine(host_config)
        
        # Metrics tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.error_requests = 0
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.errors: Dict[str, int] = defaultdict(int)
        self.active_tasks = 0
        
        self.start_time: Optional[datetime] = None
        self.metrics_history: List[LoadTestMetrics] = []
    
    async def execute_load_test(
        self,
        scenario: Scenario,
        config: LoadTestConfig,
        progress_callback: Optional[Callable[[LoadTestMetrics], None]] = None
    ) -> LoadTestResult:
        """
        Execute load test with specified configuration
        
        Args:
            scenario: The scenario to execute repeatedly
            config: Load test configuration
            progress_callback: Optional callback for real-time metrics updates
        
        Returns:
            LoadTestResult with complete test results
        """
        self._reset_metrics()
        self.start_time = datetime.now()
        
        # Start metrics collector
        metrics_task = asyncio.create_task(
            self._collect_metrics(progress_callback)
        )
        
        # Start load generator
        generator_task = asyncio.create_task(
            self._generate_load(scenario, config)
        )
        
        # Wait for test duration
        await asyncio.sleep(config.duration_seconds)
        
        # Stop generator and wait for completion
        generator_task.cancel()
        try:
            await generator_task
        except asyncio.CancelledError:
            pass
        
        # Wait for active requests to complete (max 30s)
        wait_start = time.time()
        while self.active_tasks > 0 and (time.time() - wait_start) < 30:
            await asyncio.sleep(0.1)
        
        # Stop metrics collector
        metrics_task.cancel()
        try:
            await metrics_task
        except asyncio.CancelledError:
            pass
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate final metrics
        actual_avg_tps = self.total_requests / duration if duration > 0 else 0
        success_rate = (self.successful_requests / self.total_requests * 100) \
            if self.total_requests > 0 else 0
        
        return LoadTestResult(
            test_name=scenario.name,
            start_time=self.start_time,
            end_time=end_time,
            duration_seconds=duration,
            target_tps=config.target_tps,
            actual_avg_tps=actual_avg_tps,
            total_requests=self.total_requests,
            successful_requests=self.successful_requests,
            failed_requests=self.failed_requests,
            error_requests=self.error_requests,
            success_rate=success_rate,
            response_times=self.response_times.copy(),
            status_code_distribution=dict(self.status_codes),
            error_distribution=dict(self.errors),
            metrics_timeline=self.metrics_history.copy()
        )
    
    async def _generate_load(self, scenario: Scenario, config: LoadTestConfig):
        """Generate load according to configuration"""
        interval = 1.0 / config.target_tps
        request_count = 0
        
        try:
            while True:
                # Calculate current target TPS based on ramp-up
                elapsed = (datetime.now() - self.start_time).total_seconds()
                
                if config.ramp_up_seconds > 0 and elapsed < config.ramp_up_seconds:
                    # Ramp up phase
                    if config.distribution == "linear":
                        current_tps = config.target_tps * (elapsed / config.ramp_up_seconds)
                    elif config.distribution == "exponential":
                        progress = elapsed / config.ramp_up_seconds
                        current_tps = config.target_tps * (progress ** 2)
                    else:
                        current_tps = config.target_tps
                    
                    current_interval = 1.0 / max(current_tps, 1)
                else:
                    current_interval = interval
                
                # Respect max concurrent limit
                if self.active_tasks < config.max_concurrent:
                    task = asyncio.create_task(self._execute_single_request(scenario))
                    request_count += 1
                
                await asyncio.sleep(current_interval)
        
        except asyncio.CancelledError:
            pass
    
    async def _execute_single_request(self, scenario: Scenario):
        """Execute a single request and track metrics"""
        self.active_tasks += 1
        
        try:
            result = await self.scenario_engine.execute_scenario(scenario)
            
            self.total_requests += 1
            
            # Track results
            if result.status == TestStatus.SUCCESS:
                self.successful_requests += 1
            elif result.status == TestStatus.FAILURE:
                self.failed_requests += 1
            else:
                self.error_requests += 1
            
            # Track response times and status codes
            for step in result.steps:
                if step.response_time_ms > 0:
                    self.response_times.append(step.response_time_ms)
                
                if step.status_code:
                    self.status_codes[step.status_code] += 1
                
                if step.error_message:
                    self.errors[step.error_message] += 1
        
        except Exception as e:
            self.total_requests += 1
            self.error_requests += 1
            self.errors[str(e)] += 1
        
        finally:
            self.active_tasks -= 1
    
    async def _collect_metrics(self, callback: Optional[Callable[[LoadTestMetrics], None]]):
        """Collect and report metrics periodically"""
        try:
            while True:
                await asyncio.sleep(1)  # Collect metrics every second
                
                metrics = self._calculate_current_metrics()
                self.metrics_history.append(metrics)
                
                if callback:
                    callback(metrics)
        
        except asyncio.CancelledError:
            pass
    
    def _calculate_current_metrics(self) -> LoadTestMetrics:
        """Calculate current metrics snapshot"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate TPS
        current_tps = self.total_requests / elapsed if elapsed > 0 else 0
        
        # Calculate response time percentiles
        if self.response_times:
            sorted_times = sorted(self.response_times)
            avg_time = statistics.mean(sorted_times)
            min_time = min(sorted_times)
            max_time = max(sorted_times)
            p50 = statistics.median(sorted_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            p95 = sorted_times[p95_idx] if p95_idx < len(sorted_times) else max_time
            p99 = sorted_times[p99_idx] if p99_idx < len(sorted_times) else max_time
        else:
            avg_time = min_time = max_time = p50 = p95 = p99 = 0
        
        return LoadTestMetrics(
            timestamp=datetime.now(),
            elapsed_seconds=elapsed,
            total_requests=self.total_requests,
            successful_requests=self.successful_requests,
            failed_requests=self.failed_requests,
            error_requests=self.error_requests,
            current_tps=current_tps,
            avg_response_time_ms=avg_time,
            min_response_time_ms=min_time,
            max_response_time_ms=max_time,
            p50_response_time_ms=p50,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            active_connections=self.active_tasks
        )
    
    def _reset_metrics(self):
        """Reset all metrics"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.error_requests = 0
        self.response_times.clear()
        self.status_codes.clear()
        self.errors.clear()
        self.active_tasks = 0
        self.metrics_history.clear()

