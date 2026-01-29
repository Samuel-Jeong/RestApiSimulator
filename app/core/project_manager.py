"""Project management"""

import json
import os
import orjson
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
from ..models.config import ProjectConfig, HostConfig
from ..models.scenario import Scenario
from ..models.environment import Environment
from ..utils.variable_resolver import VariableResolver


class ProjectManager:
    """Manages projects, scenarios, and configurations"""
    
    def __init__(self, projects_root: str = "projects"):
        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(exist_ok=True)
    
    def list_projects(self) -> List[str]:
        """List all available projects (including nested projects with scenario folders)"""
        projects = []
        if not self.projects_root.exists():
            return projects
        
        # 재귀적으로 scenario 폴더를 찾아서 프로젝트로 인식
        def find_scenario_dirs(path: Path, prefix: str = ""):
            """재귀적으로 scenario 폴더 찾기"""
            for item in path.iterdir():
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    # scenario 폴더를 찾으면 해당 경로를 프로젝트로 추가
                    scenario_dir = item / "scenario"
                    if scenario_dir.exists() and scenario_dir.is_dir():
                        relative_path = item.relative_to(self.projects_root)
                        projects.append(str(relative_path).replace('\\', '/'))
                    
                    # 깊이 제한 (최대 3단계까지만)
                    current_depth = len(item.relative_to(self.projects_root).parts)
                    if current_depth < 3:
                        find_scenario_dirs(item, prefix)
        
        find_scenario_dirs(self.projects_root)
        return sorted(projects)
    
    def get_projects_tree(self) -> List[Dict[str, Any]]:
        """Get projects as a hierarchical tree structure"""
        if not self.projects_root.exists():
            return []
        
        tree = []
        project_paths = self.list_projects()
        
        # 트리 구조 생성
        def build_tree_node(path_parts: List[str], full_path: str, is_project: bool) -> Dict[str, Any]:
            return {
                "name": path_parts[-1] if path_parts else "",
                "full_path": full_path,
                "is_project": is_project,
                "children": []
            }
        
        # 경로별로 트리 구조화
        root_nodes = {}
        
        for project_path in project_paths:
            parts = project_path.split('/')
            
            # 각 depth의 노드를 생성하거나 찾기
            current_level = root_nodes
            current_path_parts = []
            
            for i, part in enumerate(parts):
                current_path_parts.append(part)
                current_full_path = '/'.join(current_path_parts)
                is_last = (i == len(parts) - 1)
                
                if part not in current_level:
                    node = {
                        "name": part,
                        "full_path": current_full_path,
                        "is_project": is_last,
                        "children": {}
                    }
                    current_level[part] = node
                else:
                    # 마지막 노드면 is_project를 True로 설정
                    if is_last:
                        current_level[part]["is_project"] = True
                
                current_level = current_level[part]["children"]
        
        # Dict를 List로 변환 (정렬)
        def dict_to_list(node_dict: Dict) -> List:
            result = []
            for key in sorted(node_dict.keys()):
                node = node_dict[key].copy()
                node["children"] = dict_to_list(node["children"])
                result.append(node)
            return result
        
        return dict_to_list(root_nodes)
    
    def create_project(self, name: str) -> Path:
        """Create a new project directory structure"""
        project_path = self.projects_root / name
        
        if project_path.exists():
            raise ValueError(f"Project '{name}' already exists")
        
        # Create directory structure
        project_path.mkdir(parents=True)
        (project_path / "config").mkdir()
        (project_path / "env").mkdir()
        (project_path / "package_library").mkdir()
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
        
        # Create sample scenario (YAML format)
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
        
        scenario_file = project_path / "scenario" / "sample.yaml"
        with open(scenario_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_scenario, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return project_path
    
    def get_project_path(self, project_name: str) -> Path:
        """Get path to project directory
        
        Supports nested paths like 'wpm/workercontroller'
        """
        # 경로 구분자를 Path로 변환
        project_path = self.projects_root / project_name.replace('/', os.sep)
        if not project_path.exists():
            raise ValueError(f"Project '{project_name}' does not exist")
        return project_path
    
    def list_host_configs(self, project_name: str) -> List[str]:
        """List all available host configurations for a project"""
        config_file = self.get_project_path(project_name) / "config" / "hosts.json"
        
        if not config_file.exists():
            return []
        
        try:
            with open(config_file, 'rb') as f:
                data = orjson.loads(f.read())
            return list(data.keys())
        except Exception:
            return []
    
    def load_host_config(
        self, 
        project_name: str, 
        host_name: str,
        environment: Optional[Environment] = None
    ) -> Optional[HostConfig]:
        """Load a specific host configuration with optional environment variable substitution"""
        hosts = self.load_hosts_config(project_name, environment)
        return hosts.get(host_name)
    
    def load_hosts_config(
        self, 
        project_name: str, 
        environment: Optional[Environment] = None
    ) -> Dict[str, HostConfig]:
        """Load hosts configuration for a project with optional environment variable substitution"""
        config_file = self.get_project_path(project_name) / "config" / "hosts.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"hosts.json not found in project '{project_name}'")
        
        with open(config_file, 'rb') as f:
            data = orjson.loads(f.read())
        
        # Apply environment variable substitution if environment is provided
        if environment:
            resolver = VariableResolver({"env": environment.variables})
            data = resolver.resolve(data)
        
        hosts = {}
        for name, config in data.items():
            hosts[name] = HostConfig(**config)
        
        return hosts
    
    def list_scenarios(self, project_name: str) -> List[str]:
        """List all scenarios in a project (flat list for backward compatibility)"""
        scenario_dir = self.get_project_path(project_name) / "scenario"
        
        if not scenario_dir.exists():
            return []
        
        scenarios = []
        # JSON and YAML files
        for pattern in ["**/*.json", "**/*.yaml", "**/*.yml"]:
            for file in scenario_dir.glob(pattern):
                # 상대 경로를 사용하여 폴더 구조 포함
                relative_path = file.relative_to(scenario_dir)
                scenarios.append(str(relative_path.with_suffix('')).replace('\\', '/'))
        
        return sorted(set(scenarios))
    
    def get_scenario_tree(self, project_name: str) -> Dict[str, Any]:
        """Get scenario file structure as a tree"""
        scenario_dir = self.get_project_path(project_name) / "scenario"
        
        if not scenario_dir.exists():
            return {}
        
        def build_tree(path: Path) -> Dict[str, Any]:
            """Recursively build folder tree"""
            tree = {
                'name': path.name,
                'path': str(path.relative_to(scenario_dir)) if path != scenario_dir else '',
                'type': 'folder',
                'children': []
            }
            
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for item in items:
                if item.name.startswith('.'):
                    continue
                    
                if item.is_dir():
                    tree['children'].append(build_tree(item))
                elif item.suffix in ['.json', '.yaml', '.yml']:
                    tree['children'].append({
                        'name': item.stem,
                        'path': str(item.relative_to(scenario_dir).with_suffix('')).replace('\\', '/'),
                        'type': 'file',
                        'full_name': item.name
                    })
            
            return tree
        
        return build_tree(scenario_dir)
    
    def load_scenario(self, project_name: str, scenario_name: str) -> Scenario:
        """Load a scenario from a project
        
        Args:
            project_name: Name of the project
            scenario_name: Scenario name or path (e.g., 'test' or 'success/test')
        """
        # Try to find the file with various extensions
        base_path = self.get_project_path(project_name) / "scenario"
        
        # If extension is provided, use it directly
        if scenario_name.endswith(('.json', '.yaml', '.yml')):
            scenario_file = base_path / scenario_name
        else:
            # Try different extensions
            scenario_file = None
            for ext in ['.yaml', '.yml', '.json']:
                candidate = base_path / f"{scenario_name}{ext}"
                if candidate.exists():
                    scenario_file = candidate
                    break
            
            if not scenario_file:
                raise FileNotFoundError(f"Scenario '{scenario_name}' not found in project '{project_name}'")
        
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario '{scenario_name}' not found in project '{project_name}'")
        
        # Load based on extension
        if scenario_file.suffix in ['.yaml', '.yml']:
            with open(scenario_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            with open(scenario_file, 'rb') as f:
                data = orjson.loads(f.read())
        
        return Scenario(**data)
    
    def save_scenario(self, project_name: str, scenario_name: str, scenario: Scenario, format: str = 'yaml'):
        """Save a scenario to a project
        
        Args:
            project_name: Name of the project
            scenario_name: Scenario name (without extension)
            scenario: Scenario object to save
            format: 'yaml' or 'json' (default: yaml)
        """
        # Remove extension if provided
        scenario_name = scenario_name.replace('.json', '').replace('.yaml', '').replace('.yml', '')
        
        ext = '.yaml' if format == 'yaml' else '.json'
        scenario_file = self.get_project_path(project_name) / "scenario" / f"{scenario_name}{ext}"
        
        data = scenario.model_dump(exclude_none=True, exclude_unset=True)
        
        if format == 'yaml':
            with open(scenario_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        else:
            with open(scenario_file, 'wb') as f:
                f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    
    def delete_scenario(self, project_name: str, scenario_name: str):
        """Delete a scenario from a project"""
        base_path = self.get_project_path(project_name) / "scenario"
        
        # Try all possible extensions
        for ext in ['.json', '.yaml', '.yml']:
            scenario_file = base_path / f"{scenario_name}{ext}"
            if scenario_file.exists():
                scenario_file.unlink()
                return
    
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
    
    def get_results_tree(self, project_name: str) -> Dict[str, Any]:
        """Get test results file structure as a tree"""
        results_dir = self.get_results_dir(project_name)
        
        if not results_dir.exists():
            return {}
        
        def build_tree(path: Path) -> Dict[str, Any]:
            """Recursively build folder tree"""
            tree = {
                'name': path.name,
                'path': str(path.relative_to(results_dir)) if path != results_dir else '',
                'type': 'folder',
                'children': []
            }
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()), reverse=True)
            except PermissionError:
                return tree
            
            for item in items:
                if item.name.startswith('.'):
                    continue
                    
                if item.is_dir():
                    child_tree = build_tree(item)
                    # Only add non-empty folders
                    if child_tree['children'] or any(results_dir.rglob(f"{item.relative_to(results_dir)}/*.json")):
                        tree['children'].append(child_tree)
                elif item.suffix == '.json':
                    # Parse file to get metadata
                    file_info = {
                        'name': item.stem,
                        'path': str(item.relative_to(results_dir)).replace('\\', '/'),
                        'type': 'file',
                        'full_name': item.name,
                        'size': item.stat().st_size,
                        'modified': item.stat().st_mtime
                    }
                    
                    # Try to extract test type from filename
                    if 'scenario_' in item.name:
                        file_info['test_type'] = 'scenario'
                    elif 'loadtest_' in item.name:
                        file_info['test_type'] = 'loadtest'
                    else:
                        file_info['test_type'] = 'unknown'
                    
                    tree['children'].append(file_info)
            
            return tree
        
        return build_tree(results_dir)
    
    def list_environments(self, project_name: str) -> List[str]:
        """List all available environments for a project"""
        env_dir = self.get_project_path(project_name) / "env"
        
        if not env_dir.exists():
            return []
        
        environments = []
        for file in env_dir.glob("*.json"):
            environments.append(file.stem)
        
        return sorted(environments)
    
    def load_environment(self, project_name: str, env_name: str) -> Optional[Environment]:
        """Load an environment configuration"""
        env_file = self.get_project_path(project_name) / "env" / f"{env_name}.json"
        
        if not env_file.exists():
            return None
        
        try:
            with open(env_file, 'rb') as f:
                data = orjson.loads(f.read())
            
            # If the JSON doesn't have a 'name' field, use the filename
            if 'name' not in data:
                data['name'] = env_name
            
            return Environment(**data)
        except Exception as e:
            print(f"Error loading environment {env_name}: {e}")
            return None
    
    def save_environment(self, project_name: str, env_name: str, environment: Environment):
        """Save an environment configuration"""
        env_dir = self.get_project_path(project_name) / "env"
        env_dir.mkdir(exist_ok=True)
        
        env_file = env_dir / f"{env_name}.json"
        
        with open(env_file, 'wb') as f:
            f.write(orjson.dumps(
                environment.model_dump(),
                option=orjson.OPT_INDENT_2
            ))
    
    def get_package_library_path(self, project_name: str) -> Path:
        """Get package_library directory for a project"""
        package_lib_dir = self.get_project_path(project_name) / "package_library"
        package_lib_dir.mkdir(exist_ok=True)
        return package_lib_dir

