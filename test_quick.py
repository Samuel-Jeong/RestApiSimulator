#!/usr/bin/env python3
"""Quick test script to verify the simulator works"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.project_manager import ProjectManager
from app.core.scenario_engine import ScenarioEngine
from app.core.load_test_engine import LoadTestEngine
from app.core.report_generator import ReportGenerator
from app.core.uml_generator import UMLGenerator
from app.models.scenario import LoadTestConfig


async def test_scenario():
    """Test scenario execution"""
    print("\n" + "="*60)
    print("Testing Scenario Execution")
    print("="*60)
    
    pm = ProjectManager()
    
    # Load scenario and config
    scenario = pm.load_scenario("example", "simple_get")
    hosts = pm.load_hosts_config("example")
    
    print(f"✓ Loaded scenario: {scenario.name}")
    print(f"✓ Loaded host config: {hosts['default'].base_url}")
    
    # Execute scenario
    engine = ScenarioEngine(hosts["default"])
    
    def progress(step_name, current, total):
        print(f"  [{current}/{total}] {step_name}")
    
    result = await engine.execute_scenario(scenario, progress)
    
    print(f"\n✓ Scenario completed: {result.status.value}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print(f"  Total steps: {result.total_requests}")
    print(f"  Successful: {result.successful_requests}")
    print(f"  Failed: {result.failed_requests}")
    
    # Save report
    results_dir = pm.get_results_dir("example")
    report_path = ReportGenerator.save_scenario_report(result, results_dir, "example")
    print(f"✓ Report saved: {report_path.name}")
    
    return result.status.value == "success"


async def test_load_test():
    """Test load test execution"""
    print("\n" + "="*60)
    print("Testing Load Test (10s)")
    print("="*60)
    
    pm = ProjectManager()
    
    # Load scenario and config
    scenario = pm.load_scenario("example", "load_test_scenario")
    hosts = pm.load_hosts_config("example")
    
    print(f"✓ Loaded scenario: {scenario.name}")
    
    # Configure load test
    config = LoadTestConfig(
        duration_seconds=10,
        target_tps=5,
        ramp_up_seconds=2,
        max_concurrent=10,
        distribution="linear"
    )
    
    print(f"✓ Config: {config.target_tps} TPS for {config.duration_seconds}s")
    
    # Execute load test
    engine = LoadTestEngine(hosts["default"])
    
    def progress(metrics):
        if metrics.elapsed_seconds % 2 == 0:  # Print every 2 seconds
            print(f"  [{metrics.elapsed_seconds:.0f}s] "
                  f"TPS: {metrics.current_tps:.1f} | "
                  f"Requests: {metrics.total_requests} | "
                  f"Success: {metrics.successful_requests}")
    
    result = await engine.execute_load_test(scenario, config, progress)
    
    print(f"\n✓ Load test completed")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print(f"  Target TPS: {result.target_tps}")
    print(f"  Actual TPS: {result.actual_avg_tps:.2f}")
    print(f"  Total requests: {result.total_requests}")
    print(f"  Success rate: {result.success_rate:.1f}%")
    
    # Save report
    results_dir = pm.get_results_dir("example")
    report_path = ReportGenerator.save_load_test_report(result, results_dir, "example")
    print(f"✓ Report saved: {report_path.name}")
    
    return result.success_rate > 50  # At least 50% success


def test_uml():
    """Test UML generation"""
    print("\n" + "="*60)
    print("Testing UML Generation")
    print("="*60)
    
    pm = ProjectManager()
    scenario = pm.load_scenario("example", "user_crud")
    
    # Generate text diagram
    text_diagram = UMLGenerator.generate_text_diagram(scenario)
    print(text_diagram)
    
    # Generate PlantUML diagrams
    sequence = UMLGenerator.generate_sequence_diagram(scenario)
    flowchart = UMLGenerator.generate_flowchart(scenario)
    
    print(f"✓ Generated sequence diagram ({len(sequence)} chars)")
    print(f"✓ Generated flowchart ({len(flowchart)} chars)")
    
    # Save diagrams to organized directory
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = Path("projects/example/result") / "uml" / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scenario_name = scenario.name.replace(" ", "_")
    UMLGenerator.save_diagram(sequence, str(output_dir / f"{scenario_name}_sequence.puml"))
    UMLGenerator.save_diagram(flowchart, str(output_dir / f"{scenario_name}_flowchart.puml"))
    print(f"✓ Diagrams saved to {output_dir}")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("REST API Simulator - Quick Test")
    print("="*60)
    
    results = []
    
    try:
        # Test 1: Scenario execution
        results.append(("Scenario Test", await test_scenario()))
        
        # Test 2: Load test
        results.append(("Load Test", await test_load_test()))
        
        # Test 3: UML generation
        results.append(("UML Generation", test_uml()))
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return True
    else:
        print("\n✗ Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

