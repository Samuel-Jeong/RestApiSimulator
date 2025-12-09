"""Project management"""

import json
import orjson
from pathlib import Path
from typing import List, Dict, Optional
from ..models.config import ProjectConfig, HostConfig
from ..models.scenario import Scenario


class ProjectManager:
    """Manages projects, scenarios, and configurations"""
    
    def __init__(self, projects_root: str = "projects"):
        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(exist_ok=True)
    
    def list_projects(self) -> List[str]:
        """List all available projects"""
        projects = []
        if self.projects_root.exists():
            for item in self.projects_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    projects.append(item.name)
        return sorted(projects)
    
    def create_project(self, name: str) -> Path:
        """Create a new project directory structure"""
        project_path = self.projects_root / name
        
        if project_path.exists():
            raise ValueError(f"Project '{name}' already exists")
        
        # Create directory structure
        project_path.mkdir(parents=True)
        (project_path / "config").mkdir()
        (project_path / "scenario").mkdir()
        (project_path / "result").mkdir()
        
        # Create default config
        default_config = {
            "default": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "REST-API-Simulator/1.0"
                },
                "verify_ssl": True
            }
        }
        
        config_file = project_path / "config" / "hosts.json"
        with open(config_file, 'wb') as f:
            f.write(orjson.dumps(default_config, option=orjson.OPT_INDENT_2))
        
        # Create sample scenario
        sample_scenario = {
            "name": "Sample API Test",
            "description": "Sample scenario template",
            "steps": [
                {
                    "name": "Health Check",
                    "method": "GET",
                    "path": "/health",
                    "assertions": [
                        {"field": "status", "operator": "eq", "value": 200}
                    ]
                }
            ]
        }
        
        scenario_file = project_path / "scenario" / "sample.json"
        with open(scenario_file, 'wb') as f:
            f.write(orjson.dumps(sample_scenario, option=orjson.OPT_INDENT_2))
        
        return project_path
    
    def get_project_path(self, project_name: str) -> Path:
        """Get path to project directory"""
        project_path = self.projects_root / project_name
        if not project_path.exists():
            raise ValueError(f"Project '{project_name}' does not exist")
        return project_path
    
    def load_hosts_config(self, project_name: str) -> Dict[str, HostConfig]:
        """Load hosts configuration for a project"""
        config_file = self.get_project_path(project_name) / "config" / "hosts.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"hosts.json not found in project '{project_name}'")
        
        with open(config_file, 'rb') as f:
            data = orjson.loads(f.read())
        
        hosts = {}
        for name, config in data.items():
            hosts[name] = HostConfig(**config)
        
        return hosts
    
    def list_scenarios(self, project_name: str) -> List[str]:
        """List all scenarios in a project"""
        scenario_dir = self.get_project_path(project_name) / "scenario"
        
        if not scenario_dir.exists():
            return []
        
        scenarios = []
        for file in scenario_dir.glob("*.json"):
            scenarios.append(file.stem)
        
        return sorted(scenarios)
    
    def load_scenario(self, project_name: str, scenario_name: str) -> Scenario:
        """Load a scenario from a project"""
        scenario_file = self.get_project_path(project_name) / "scenario" / f"{scenario_name}.json"
        
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario '{scenario_name}' not found in project '{project_name}'")
        
        with open(scenario_file, 'rb') as f:
            data = orjson.loads(f.read())
        
        return Scenario(**data)
    
    def save_scenario(self, project_name: str, scenario_name: str, scenario: Scenario):
        """Save a scenario to a project"""
        scenario_file = self.get_project_path(project_name) / "scenario" / f"{scenario_name}.json"
        
        with open(scenario_file, 'wb') as f:
            f.write(orjson.dumps(
                scenario.model_dump(), 
                option=orjson.OPT_INDENT_2
            ))
    
    def delete_scenario(self, project_name: str, scenario_name: str):
        """Delete a scenario from a project"""
        scenario_file = self.get_project_path(project_name) / "scenario" / f"{scenario_name}.json"
        
        if scenario_file.exists():
            scenario_file.unlink()
    
    def get_results_dir(self, project_name: str) -> Path:
        """Get results directory for a project"""
        results_dir = self.get_project_path(project_name) / "result"
        results_dir.mkdir(exist_ok=True)
        return results_dir
    
    def list_results(self, project_name: str) -> List[str]:
        """List all test results in a project"""
        results_dir = self.get_results_dir(project_name)
        
        results = []
        # Search recursively for JSON files
        for file in results_dir.rglob("*.json"):
            # Get relative path from results_dir
            rel_path = file.relative_to(results_dir)
            results.append(str(rel_path))
        
        return sorted(results, reverse=True)

