"""Pre-request script execution engine"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path


class PreRequestEngine:
    """Execute pre-request scripts before scenario execution"""
    
    def __init__(self, project_path: str):
        """
        Initialize pre-request engine
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.package_library_path = self.project_path / "package_library"
        
    def execute_script(
        self,
        script_name: str,
        environment_vars: Dict[str, Any],
        scenario_vars: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a pre-request script
        
        Args:
            script_name: Name of the script file (e.g., "pre_request.py")
            environment_vars: Environment variables
            scenario_vars: Scenario variables
            
        Returns:
            Tuple of (updated_variables, step_info)
        """
        script_path = self.package_library_path / script_name
        
        step_info = {
            'step_name': script_name,
            'method': 'PYTHON',
            'url': str(script_path),
            'status_code': None,
            'response_time_ms': 0,
            'error': None
        }
        
        if not script_path.exists():
            return {}, step_info
        
        # Prepare context for script
        context = {
            'env': environment_vars.copy(),
            'vars': scenario_vars.copy(),
            'result': {}
        }
        
        try:
            import time
            
            # Add package_library to Python path
            if str(self.package_library_path) not in sys.path:
                sys.path.insert(0, str(self.package_library_path))
            
            # Read and execute script
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Execute in isolated namespace
            start_time = time.time()
            exec(script_content, {'__builtins__': __builtins__}, context)
            response_time_ms = (time.time() - start_time) * 1000
            
            step_info['response_time_ms'] = response_time_ms
            
            # Return result variables
            result = context.get('result', {})
            
            # Python 스크립트는 extract 검증을 하지 않음 (명시적 extract 설정이 없으므로)
            print(f"✅ Python script executed successfully ({response_time_ms:.0f}ms)")
            
            return result, step_info
            
        except Exception as e:
            print(f"")
            print(f"{'='*60}")
            print(f"❌ PACKAGE LIBRARY SCRIPT EXECUTION FAILED")
            print(f"{'='*60}")
            print(f"Script File: {script_name}")
            print(f"Error Type:  {type(e).__name__}")
            print(f"Error:       {e}")
            
            # Show traceback for detailed debugging
            import traceback
            print(f"\nTraceback:")
            print(f"{'─'*60}")
            traceback.print_exc()
            print(f"{'='*60}")
            print(f"")
            
            step_info['error'] = str(e)
            raise
        finally:
            # Clean up sys.path
            if str(self.package_library_path) in sys.path:
                sys.path.remove(str(self.package_library_path))
    
    def has_script(self, script_name: str) -> bool:
        """Check if a script exists"""
        script_path = self.package_library_path / script_name
        return script_path.exists()
    
    def list_scripts(self) -> list:
        """List all available scripts"""
        if not self.package_library_path.exists():
            return []
        
        return [
            f.name for f in self.package_library_path.glob("*.py")
            if f.is_file() and not f.name.startswith("_")
        ]
