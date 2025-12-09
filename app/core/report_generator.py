"""Test report generation"""

import orjson
from pathlib import Path
from datetime import datetime
from typing import Optional
from ..models.result import TestReport, ScenarioResult, LoadTestResult


class ReportGenerator:
    """Generates and saves test reports"""
    
    @staticmethod
    def save_scenario_report(
        result: ScenarioResult,
        output_dir: Path,
        project_name: str
    ) -> Path:
        """Save scenario test report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_str = datetime.now().strftime("%Y%m%d")
        report_id = f"scenario_{result.scenario_name}_{timestamp}"
        
        report = TestReport(
            report_id=report_id,
            test_type="scenario",
            project_name=project_name,
            scenario_results=[result],
            summary={
                "scenario_name": result.scenario_name,
                "status": result.status.value,
                "duration_seconds": result.duration_seconds,
                "total_steps": len(result.steps),
                "successful_steps": result.successful_requests,
                "failed_steps": result.failed_requests,
                "error_steps": result.error_requests
            }
        )
        
        # Create organized directory structure: scenarios/YYYYMMDD/
        organized_dir = output_dir / "scenarios" / date_str
        return ReportGenerator._save_report(report, organized_dir)
    
    @staticmethod
    def save_load_test_report(
        result: LoadTestResult,
        output_dir: Path,
        project_name: str
    ) -> Path:
        """Save load test report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_str = datetime.now().strftime("%Y%m%d")
        report_id = f"loadtest_{result.test_name}_{timestamp}"
        
        report = TestReport(
            report_id=report_id,
            test_type="load_test",
            project_name=project_name,
            load_test_result=result,
            summary={
                "test_name": result.test_name,
                "target_tps": result.target_tps,
                "actual_avg_tps": round(result.actual_avg_tps, 2),
                "duration_seconds": result.duration_seconds,
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "error_requests": result.error_requests,
                "success_rate": round(result.success_rate, 2)
            }
        )
        
        # Create organized directory structure: loadtests/YYYYMMDD/
        organized_dir = output_dir / "loadtests" / date_str
        return ReportGenerator._save_report(report, organized_dir)
    
    @staticmethod
    def _save_report(report: TestReport, output_dir: Path) -> Path:
        """Save report to file"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{report.report_id}.json"
        filepath = output_dir / filename
        
        # Use orjson for better performance and datetime handling
        data = report.model_dump()
        
        # Convert int keys to str for orjson compatibility
        if report.load_test_result:
            if 'status_code_distribution' in data.get('load_test_result', {}):
                data['load_test_result']['status_code_distribution'] = {
                    str(k): v for k, v in data['load_test_result']['status_code_distribution'].items()
                }
        
        with open(filepath, 'wb') as f:
            f.write(orjson.dumps(
                data,
                option=orjson.OPT_INDENT_2 | orjson.OPT_NAIVE_UTC
            ))
        
        return filepath
    
    @staticmethod
    def load_report(filepath: Path) -> TestReport:
        """Load report from file"""
        with open(filepath, 'rb') as f:
            data = orjson.loads(f.read())
        
        return TestReport(**data)
    
    @staticmethod
    def generate_summary_text(report: TestReport) -> str:
        """Generate human-readable summary"""
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"Test Report: {report.report_id}")
        lines.append(f"{'='*60}")
        lines.append(f"Project: {report.project_name}")
        lines.append(f"Test Type: {report.test_type}")
        lines.append(f"Created: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        if report.test_type == "scenario":
            for result in report.scenario_results:
                lines.append(f"Scenario: {result.scenario_name}")
                lines.append(f"Status: {result.status.value}")
                lines.append(f"Duration: {result.duration_seconds:.2f}s")
                lines.append(f"Steps: {len(result.steps)}")
                lines.append(f"  Success: {result.successful_requests}")
                lines.append(f"  Failed: {result.failed_requests}")
                lines.append(f"  Errors: {result.error_requests}")
        
        elif report.test_type == "load_test" and report.load_test_result:
            result = report.load_test_result
            lines.append(f"Load Test: {result.test_name}")
            lines.append(f"Duration: {result.duration_seconds:.2f}s")
            lines.append(f"Target TPS: {result.target_tps}")
            lines.append(f"Actual TPS: {result.actual_avg_tps:.2f}")
            lines.append(f"Total Requests: {result.total_requests}")
            lines.append(f"  Success: {result.successful_requests} ({result.success_rate:.1f}%)")
            lines.append(f"  Failed: {result.failed_requests}")
            lines.append(f"  Errors: {result.error_requests}")
            
            if result.response_times:
                import statistics
                sorted_times = sorted(result.response_times)
                p50_idx = int(len(sorted_times) * 0.50)
                p95_idx = int(len(sorted_times) * 0.95)
                p99_idx = int(len(sorted_times) * 0.99)
                
                lines.append("")
                lines.append("Response Times:")
                lines.append(f"  Avg: {statistics.mean(sorted_times):.2f}ms")
                lines.append(f"  Min: {min(sorted_times):.2f}ms")
                lines.append(f"  Max: {max(sorted_times):.2f}ms")
                lines.append(f"  P50: {sorted_times[p50_idx]:.2f}ms")
                lines.append(f"  P95: {sorted_times[p95_idx]:.2f}ms")
                lines.append(f"  P99: {sorted_times[p99_idx]:.2f}ms")
        
        lines.append(f"{'='*60}")
        
        return "\n".join(lines)

