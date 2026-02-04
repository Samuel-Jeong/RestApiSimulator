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
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
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
        
        # Create organized directory structure: scenarios/{scenario_name}/{yyyyMMddHHmmss}/
        import re
        safe_scenario_name = re.sub(r'[^\w\-_]', '_', result.scenario_name)
        organized_dir = output_dir / "scenarios" / safe_scenario_name / timestamp
        report_path = ReportGenerator._save_report(report, organized_dir)
        
        # Save scenario file and UML alongside result
        ReportGenerator._save_scenario_artifacts(result, organized_dir, output_dir, report_id)
        
        return report_path
    
    @staticmethod
    def save_load_test_report(
        result: LoadTestResult,
        output_dir: Path,
        project_name: str
    ) -> Path:
        """Save load test report"""
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
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
        
        # Create organized directory structure: loadtests/{test_name}/{yyyyMMddHHmmss}/
        import re
        safe_test_name = re.sub(r'[^\w\-_]', '_', result.test_name)
        organized_dir = output_dir / "loadtests" / safe_test_name / timestamp
        report_path = ReportGenerator._save_report(report, organized_dir)
        
        # Save scenario file and UML for load tests too
        ReportGenerator._save_load_test_artifacts(result, organized_dir, output_dir, report_id)
        
        return report_path
    
    @staticmethod
    def _save_scenario_artifacts(
        result: ScenarioResult,
        report_dir: Path,
        project_results_dir: Path,
        report_id: str
    ):
        """Save scenario file and UML alongside result"""
        import shutil
        from .uml_generator import UMLGenerator
        
        try:
            # Find scenario file in project directory
            project_dir = project_results_dir.parent  # results/ -> project/
            scenario_base_name = result.scenario_name
            
            # Search in scenario directory structure
            scenario_dir = project_dir / "scenario"
            scenario_file = None
            
            if scenario_dir.exists():
                # Search in success, failure, integration, load_test folders
                for category in ['success', 'failure', 'integration', 'load_test']:
                    category_dir = scenario_dir / category
                    if category_dir.exists():
                        # Search in API-specific folders
                        for api_folder in category_dir.iterdir():
                            if api_folder.is_dir():
                                # Try to find YAML file
                                yaml_file = api_folder / f"{scenario_base_name}.yaml"
                                if yaml_file.exists():
                                    scenario_file = yaml_file
                                    break
                        if scenario_file:
                            break
            
            # Copy scenario file if found
            if scenario_file:
                dest_scenario = report_dir / f"{report_id}_scenario.yaml"
                shutil.copy(scenario_file, dest_scenario)
                
                # Generate and save UML
                try:
                    uml_content = UMLGenerator.generate_text_diagram(str(scenario_file))
                    uml_file = report_dir / f"{report_id}_uml.txt"
                    with open(uml_file, 'w', encoding='utf-8') as f:
                        f.write(uml_content)
                except Exception as e:
                    # UML generation failed, but continue
                    pass
                    
        except Exception as e:
            # If any error occurs, just skip artifacts (not critical)
            pass
    
    @staticmethod
    def _save_load_test_artifacts(
        result: LoadTestResult,
        report_dir: Path,
        project_results_dir: Path,
        report_id: str
    ):
        """Save scenario file and UML for load tests"""
        import shutil
        from .uml_generator import UMLGenerator
        
        try:
            # Find scenario file in project directory
            project_dir = project_results_dir.parent  # results/ -> project/
            scenario_base_name = result.test_name
            
            # Search in scenario/load_test directory
            scenario_dir = project_dir / "scenario" / "load_test"
            scenario_file = None
            
            if scenario_dir.exists():
                # Try to find YAML file directly or in subdirectories
                yaml_file = scenario_dir / f"{scenario_base_name}.yaml"
                if yaml_file.exists():
                    scenario_file = yaml_file
                else:
                    # Search in subdirectories
                    for item in scenario_dir.iterdir():
                        if item.is_dir():
                            yaml_file = item / f"{scenario_base_name}.yaml"
                            if yaml_file.exists():
                                scenario_file = yaml_file
                                break
            
            # Copy scenario file if found
            if scenario_file:
                dest_scenario = report_dir / f"{report_id}_scenario.yaml"
                shutil.copy(scenario_file, dest_scenario)
                
                # Generate and save UML
                try:
                    uml_content = UMLGenerator.generate_text_diagram(str(scenario_file))
                    uml_file = report_dir / f"{report_id}_uml.txt"
                    with open(uml_file, 'w', encoding='utf-8') as f:
                        f.write(uml_content)
                except Exception as e:
                    # UML generation failed, but continue
                    pass
                    
        except Exception as e:
            # If any error occurs, just skip artifacts (not critical)
            pass
    
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

