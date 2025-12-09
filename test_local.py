#!/usr/bin/env python3
"""Test script for local dummy server"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.project_manager import ProjectManager
from app.core.scenario_engine import ScenarioEngine
from app.core.report_generator import ReportGenerator


async def test_local_scenarios():
    """Test all local scenarios"""
    print("\n" + "="*60)
    print("Testing Local Dummy Server Scenarios")
    print("="*60)
    
    pm = ProjectManager()
    
    # Load config
    hosts = pm.load_hosts_config("example")
    
    # Test scenarios
    scenarios = [
        "simple_get",
        "user_crud",
        "complex_workflow"
    ]
    
    results = []
    
    for scenario_name in scenarios:
        print(f"\n{'='*60}")
        print(f"Testing: {scenario_name}")
        print(f"{'='*60}")
        
        try:
            # Load scenario
            scenario = pm.load_scenario("example", scenario_name)
            print(f"✓ Loaded scenario: {scenario.name}")
            
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
            
            results.append({
                "name": scenario_name,
                "status": result.status.value,
                "success": result.status.value == "success",
                "steps": result.total_requests,
                "successful": result.successful_requests,
                "failed": result.failed_requests
            })
            
        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({
                "name": scenario_name,
                "status": "error",
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for result in results:
        status_icon = "✓" if result["success"] else "✗"
        print(f"{status_icon} {result['name']}: {result['status']}")
        if "steps" in result:
            print(f"   Steps: {result['successful']}/{result['steps']} successful")
    
    print("="*60)
    
    all_success = all(r["success"] for r in results)
    if all_success:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {sum(1 for r in results if not r['success'])} test(s) failed")
    
    return all_success


if __name__ == "__main__":
    success = asyncio.run(test_local_scenarios())
    sys.exit(0 if success else 1)

