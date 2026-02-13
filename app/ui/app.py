"""Main TUI application"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Label, Input, RichLog, Select
from textual.binding import Binding
from textual import work
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import json
import yaml
from rich.text import Text
from rich.panel import Panel

from ..core.project_manager import ProjectManager
from ..core.scenario_engine import ScenarioEngine
from ..core.load_test_engine import LoadTestEngine
from ..core.report_generator import ReportGenerator
from ..core.uml_generator import UMLGenerator
from ..models.scenario import LoadTestConfig


class RestApiSimulatorApp(App):
    """REST API Simulator TUI Application"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #header {
        background: $primary;
        color: $text;
        height: 3;
        content-align: center middle;
    }
    
    #main_container {
        height: 1fr;
        layout: horizontal;
    }
    
    #menu_panel {
        width: 25;
        background: $panel;
        border-right: solid $primary;
        overflow-y: auto;
        scrollbar-gutter: stable;
    }
    
    #content_panel {
        width: 1fr;
        padding: 1;
        overflow-y: auto;
        scrollbar-gutter: stable;
    }
    
    #input_container {
        height: auto;
        padding: 1 0;
    }
    
    #user_input {
        width: 100%;
    }
    
    #status_bar {
        height: 3;
        background: $panel;
        color: $text;
        padding: 1;
    }
    
    .menu_button {
        width: 100%;
        margin: 1 0;
    }
    
    .section_title {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    
    RichLog {
        border: solid $primary;
        height: 100%;
        width: 100%;
        scrollbar-gutter: stable;
    }
    
    #analysis_container {
        display: none;
        height: 1fr;
        layout: horizontal;
    }
    
    #analysis_container.visible {
        display: block;
    }
    
    #left_panel {
        width: 50%;
        height: 100%;
        padding: 0 1;
        overflow: hidden auto;
        scrollbar-gutter: stable;
    }
    
    #right_panel {
        width: 50%;
        height: 100%;
        padding: 0 1;
        layout: vertical;
    }
    
    #analysis_content {
        width: 100%;
        height: 100%;
        border: solid $primary;
        padding: 1;
        overflow-y: auto;
        scrollbar-gutter: stable;
    }
    
    #uml_section {
        height: 50%;
        min-height: 20;
        max-height: 50%;
        overflow-y: auto;
        scrollbar-gutter: stable;
    }
    
    #log_section {
        height: 50%;
        min-height: 20;
        max-height: 50%;
        overflow-y: auto;
        scrollbar-gutter: stable;
    }
    
    .panel_title {
        text-style: bold;
        color: $accent;
        padding: 0 1;
        background: $panel;
        width: 100%;
    }
    
    Static {
        width: 100%;
    }
    
    #content_area {
        width: 100%;
        height: auto;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("p", "show_projects", "Projects"),
        Binding("s", "show_scenarios", "Scenarios"),
        Binding("r", "show_results", "Results"),
        Binding("u", "show_uml", "UML"),
    ]
    
    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()
        self.current_project = None
        self.current_host_config = None
        self.current_environment = None  # Selected environment
        self.log_widget = None
        self.current_screen = "welcome"  # Track current screen
        self.selected_scenario = None  # Track selected scenario
        self._scenario_index_map = {}  # 번호 → 경로 매핑 (시나리오 트리 표시용)
        self._results_index_map = {}  # 번호 → 경로 매핑 (결과 트리 표시용)
        self.project_number_mapping = {}  # 번호 → 경로 매핑 (프로젝트 트리 표시용)
        self.current_result_data = {
            "analysis": [],
            "api_flow": [],
            "log": [],
            "result_path": None
        }  # Store current result data for export
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header(show_clock=True)
        
        with Container(id="main_container"):
            # Left menu panel
            with Vertical(id="menu_panel"):
                yield Button("📁 Projects", id="btn_projects", classes="menu_button")
                yield Button("📝 Scenarios", id="btn_scenarios", classes="menu_button")
                yield Button("📊 Results", id="btn_results", classes="menu_button")
                yield Button("🎨 UML Generator", id="btn_uml", classes="menu_button")
                yield Button("⚙️  Settings", id="btn_settings", classes="menu_button")
                yield Button("❌ Exit", id="btn_exit", classes="menu_button")
            
            # Right content panel
            with Vertical(id="content_panel"):
                yield Static("Welcome to REST API Simulator", id="content_area")
                
                # Analysis split view (left: data, right: UML)
                with Container(id="analysis_container"):
                    with Vertical(id="left_panel"):
                        yield Label("📊 Analysis Data", classes="panel_title")
                        yield RichLog(id="analysis_content", wrap=True, markup=True, auto_scroll=False)
                    
                    with Vertical(id="right_panel"):
                        with Container(id="uml_section"):
                            yield Label("🎨 API Flow Diagram", classes="panel_title")
                            yield RichLog(id="api_flow", wrap=False, auto_scroll=False)
                        
                        with Container(id="log_section"):
                            yield Label("📋 Detailed Log", classes="panel_title")
                            yield RichLog(id="log_output", wrap=True, highlight=True, auto_scroll=False)
                
                with Container(id="input_container"):
                    yield Input(placeholder="Enter command...", id="user_input")
        
        # Status bar
        yield Static("Ready | No project selected", id="status_bar")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts"""
        self.show_welcome_screen()
    
    def show_welcome_screen(self):
        """Show welcome screen"""
        # Hide analysis container
        try:
            analysis_container = self.query_one("#analysis_container")
            analysis_container.remove_class("visible")
            
            content = self.query_one("#content_area", Static)
            content.display = True
        except:
            pass  # Panels might not be mounted yet
        
        content = self.query_one("#content_area", Static)
        
        welcome_text = """
        ╔══════════════════════════════════════════════════════════╗
        ║                                                          ║
        ║           REST API Simulator v1.0                       ║
        ║                                                          ║
        ║  High-Performance API Testing & Load Testing Tool       ║
        ║                                                          ║
        ╚══════════════════════════════════════════════════════════╝
        
        Features:
        • 📁 Project Management
        • 📝 Scenario-based Testing
        • 📊 Detailed Results & Reports
        • 🎨 UML Diagram Generation
        
        Quick Start:
        1. Select or create a project (Press P)
        2. Select a scenario and run it (Press S)
        3. View test results (Press R)
        
        Press the menu buttons or use keyboard shortcuts to navigate.
        """
        
        content.update(welcome_text)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id
        
        if button_id == "btn_projects":
            self.show_projects_screen()
        elif button_id == "btn_scenarios":
            self.show_scenarios_screen()
        elif button_id == "btn_results":
            self.show_results_screen()
        elif button_id == "btn_uml":
            self.show_uml_screen()
        elif button_id == "btn_settings":
            self.show_settings_screen()
        elif button_id == "btn_exit":
            self.exit()
    
    def _render_project_tree(self, nodes: list, indent: int = 0, numbering: list = None) -> tuple[str, dict]:
        """Render project tree structure
        
        Returns:
            tuple: (rendered_text, number_to_path_mapping)
        """
        if numbering is None:
            numbering = [0]  # Use list to maintain reference
        
        text = ""
        mapping = {}
        
        for i, node in enumerate(nodes):
            is_last = (i == len(nodes) - 1)
            
            # Tree characters
            if indent == 0:
                prefix = ""
                branch = ""
            else:
                prefix = "  " * (indent - 1)
                branch = "└─ " if is_last else "├─ "
            
            # Only number projects (not intermediate folders)
            if node["is_project"]:
                numbering[0] += 1
                number_str = f"{numbering[0]}. "
                mapping[numbering[0]] = node["full_path"]
                marker = "▶ " if node["full_path"] == self.current_project else "  "
            else:
                number_str = ""
                marker = "  "
            
            # Project marker
            icon = "📁 " if node["is_project"] else "📂 "
            
            text += f"{marker}{prefix}{branch}{number_str}{icon}{node['name']}\n"
            
            # Recursively render children
            if node["children"]:
                child_text, child_mapping = self._render_project_tree(
                    node["children"], 
                    indent + 1, 
                    numbering
                )
                text += child_text
                mapping.update(child_mapping)
        
        return text, mapping
    
    def show_projects_screen(self):
        """Show projects management screen"""
        self.current_screen = "projects"
        
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        
        projects_tree = self.project_manager.get_projects_tree()
        
        text = "╔═ PROJECT MANAGEMENT ═══════════════════════════════════╗\n\n"
        
        if projects_tree:
            text += "Available Projects:\n\n"
            tree_text, self.project_number_mapping = self._render_project_tree(projects_tree)
            text += tree_text
        else:
            text += "No projects found. Create a new project to get started.\n"
            self.project_number_mapping = {}
        
        text += "\n" + "─" * 60 + "\n"
        
        # Show current project details if selected
        if self.current_project:
            text += f"\nCurrent Project: {self.current_project}\n"
            
            # Show available environments
            envs = self.project_manager.list_environments(self.current_project)
            if envs:
                text += f"Environments: {', '.join(envs)}\n"
                if self.current_environment:
                    text += f"Selected Environment: {self.current_environment.name}\n"
            
            # Show available hosts
            hosts = self.project_manager.list_host_configs(self.current_project)
            if hosts:
                text += f"Hosts: {', '.join(hosts)}\n"
                if self.current_host_config:
                    text += f"Selected Host: {self.current_host_config.name}\n"
        
        text += "\nActions:\n"
        text += "• Type project number or name to select\n"
        text += "• Type 'new:<name>' to create new project\n"
        text += "• Type 'env:<name>' to select environment\n"
        text += "• Type 'host:<name>' to select host\n"
        
        content.update(text)
        self.update_status("Projects screen")
        
        # Focus input
        self.query_one("#user_input", Input).focus()
    
    def show_scenarios_screen(self):
        """Show scenarios management screen"""
        if not self.current_project:
            self.show_error("Please select a project first")
            return
        
        self.current_screen = "scenarios"
        
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        
        # Get scenario tree structure
        scenario_tree = self.project_manager.get_scenario_tree(self.current_project)
        scenarios = self.project_manager.list_scenarios(self.current_project)
        
        text = f"╔═ SCENARIOS - {self.current_project} ═══════════════════════╗\n\n"
        
        if scenarios:
            text += "Available Scenarios:\n\n"
            
            # Display tree structure
            self._scenario_index_map = {}  # 번호 → 경로 매핑
            counter = [1]  # mutable counter for nested function
            
            def print_tree(node: dict, prefix: str = "", is_last: bool = True):
                """Recursively print tree structure"""
                nonlocal text
                
                if node['type'] == 'folder' and node['path'] != '':
                    # 폴더 표시
                    connector = "└── " if is_last else "├── "
                    text += f"{prefix}{connector}📁 {node['name']}/\n"
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    
                    children = node.get('children', [])
                    for i, child in enumerate(children):
                        print_tree(child, new_prefix, i == len(children) - 1)
                
                elif node['type'] == 'file':
                    # 파일 표시
                    connector = "└── " if is_last else "├── "
                    idx = counter[0]
                    text += f"{prefix}{connector}[{idx:2d}] 📄 {node['name']}\n"
                    self._scenario_index_map[idx] = node['path']
                    counter[0] += 1
                
                elif node['type'] == 'folder' and node['path'] == '':
                    # 루트 폴더 - 자식들만 표시
                    children = node.get('children', [])
                    for i, child in enumerate(children):
                        print_tree(child, "", i == len(children) - 1)
            
            print_tree(scenario_tree)
            
        else:
            text += "No scenarios found in this project.\n"
        
        text += "\n" + "─" * 60 + "\n"
        text += "\nActions:\n"
        text += "• Type scenario number to view/run\n"
        text += "• Type scenario path (e.g., 'success/test_api') to run\n"
        text += "• Type 'new:<name>' to create new scenario\n"
        
        content.update(text)
        self.update_status(f"Scenarios: {len(scenarios)} files | Project: {self.current_project}")
        
        # Focus input
        self.query_one("#user_input", Input).focus()
    
    
    def show_results_screen(self):
        """Show test results screen"""
        if not self.current_project:
            self.show_error("Please select a project first")
            return
        
        self.current_screen = "results"
        
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        
        # Get results tree structure
        results_tree = self.project_manager.get_results_tree(self.current_project)
        results = self.project_manager.list_results(self.current_project)
        
        text = f"╔═ TEST RESULTS - {self.current_project} ═══════════════════╗\n\n"
        
        if results:
            text += "Test Results by Folder:\n\n"
            
            # Display tree structure
            self._results_index_map = {}  # 번호 → 경로 매핑
            counter = [1]  # mutable counter for nested function
            
            def print_tree(node: dict, prefix: str = "", is_last: bool = True):
                """Recursively print tree structure"""
                nonlocal text
                
                if node['type'] == 'folder' and node['path'] != '':
                    # 폴더 표시 (타임스탬프 폴더, 시나리오 폴더, scenarios, loadtests 등)
                    connector = "└── " if is_last else "├── "
                    
                    # 아이콘 결정: 타임스탬프(14자리) = 🕐, 날짜(8자리) = 📅, 기타 = 📁
                    if node['name'].isdigit() and len(node['name']) == 14:
                        folder_icon = "🕐 "
                    elif node['name'].isdigit() and len(node['name']) == 8:
                        folder_icon = "📅 "
                    else:
                        folder_icon = "📁 "
                    
                    # 폴더 타입 추가 정보
                    folder_label = node['name']
                    if node['name'] == 'scenarios':
                        folder_label = f"{node['name']} (Scenario Tests)"
                    elif node['name'] == 'loadtests':
                        folder_label = f"{node['name']} (Load Tests)"
                    
                    text += f"{prefix}{connector}{folder_icon}{folder_label}\n"
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    
                    children = node.get('children', [])
                    for i, child in enumerate(children):
                        print_tree(child, new_prefix, i == len(children) - 1)
                
                elif node['type'] == 'file':
                    # 파일 표시
                    connector = "└── " if is_last else "├── "
                    idx = counter[0]
                    
                    # Test type icon
                    if node.get('test_type') == 'scenario':
                        icon = "📄 "
                    elif node.get('test_type') == 'loadtest':
                        icon = "⚡ "
                    else:
                        icon = "📋 "
                    
                    # File size
                    size_kb = node.get('size', 0) / 1024
                    size_str = f"{size_kb:.1f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"
                    
                    # Wrap long names with proper indentation
                    display_name = node['name']
                    max_width = 80  # 최대 너비
                    if len(display_name) > max_width:
                        # 첫 줄
                        text += f"{prefix}{connector}[{idx:2d}] {icon}{display_name[:max_width]}\n"
                        # 나머지 줄들 (들여쓰기 적용)
                        remaining = display_name[max_width:]
                        indent_prefix = prefix + ("    " if is_last else "│   ") + "    "  # 번호와 아이콘 자리만큼 들여쓰기
                        while remaining:
                            text += f"{indent_prefix}{remaining[:max_width]}\n"
                            remaining = remaining[max_width:]
                        # 파일 크기는 마지막에 추가
                        text += f"{indent_prefix}({size_str})\n"
                    else:
                        text += f"{prefix}{connector}[{idx:2d}] {icon}{display_name} ({size_str})\n"
                    
                    self._results_index_map[idx] = node['path']
                    counter[0] += 1
                
                elif node['type'] == 'folder' and node['path'] == '':
                    # 루트 폴더 - 자식들만 표시
                    children = node.get('children', [])
                    for i, child in enumerate(children):
                        print_tree(child, "", i == len(children) - 1)
            
            print_tree(results_tree)
            
            text += f"\n📊 Total: {len(results)} result files\n"
        else:
            text += "No test results found.\n"
            text += "\nRun some scenarios to generate results.\n"
        
        text += "\n" + "─" * 60 + "\n"
        text += "\nActions:\n"
        text += "• Type result number to view details\n"
        text += "• Type 'all' to list all results (flat view)\n"
        
        content.update(text)
        self.update_status(f"Results: {len(results)} files | Project: {self.current_project}")
        
        # Focus input
        self.query_one("#user_input", Input).focus()
    
    def show_uml_screen(self):
        """Show UML generator screen"""
        if not self.current_project:
            self.show_error("Please select a project first")
            return
        
        self.current_screen = "uml"
        
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        
        scenarios = self.project_manager.list_scenarios(self.current_project)
        
        text = f"╔═ UML GENERATOR - {self.current_project} ═════════════════╗\n\n"
        text += "Generate UML diagrams from scenarios:\n\n"
        
        if scenarios:
            text += "Available Scenarios:\n\n"
            for idx, scenario in enumerate(scenarios, 1):
                text += f"  {idx}. {scenario}\n"
            
            text += "\n" + "─" * 60 + "\n"
            text += "\nDiagram Types:\n"
            text += "• Sequence Diagram (PlantUML)\n"
            text += "• Flowchart (PlantUML)\n"
            text += "• Text Diagram (ASCII)\n"
            text += "\nType scenario number or name to generate diagram\n"
        else:
            text += "No scenarios available.\n"
        
        content.update(text)
        self.update_status("UML Generator")
        
        # Focus input
        self.query_one("#user_input", Input).focus()
    
    def show_settings_screen(self):
        """Show settings screen"""
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        
        text = "╔═ SETTINGS ═════════════════════════════════════════════╗\n\n"
        text += "Application Settings:\n\n"
        text += f"• Projects Root: projects/\n"
        
        if self.current_project:
            text += f"• Current Project: {self.current_project}\n"
            
            hosts = self.project_manager.load_hosts_config(
                self.current_project, 
                self.current_environment
            )
            text += f"• Configured Hosts: {len(hosts)}\n"
            
            for name, config in hosts.items():
                text += f"  - {name}: {config.base_url}\n"
        
        content.update(text)
        self.update_status("Settings")
    
    def show_error(self, message: str):
        """Show error message"""
        # Hide analysis container
        try:
            analysis_container = self.query_one("#analysis_container")
            analysis_container.remove_class("visible")
            
            content = self.query_one("#content_area", Static)
            content.display = True
        except:
            pass
        
        content = self.query_one("#content_area", Static)
        content.update(f"\n⚠️  ERROR: {message}\n")
        self.update_status(f"Error: {message}")
    
    def update_status(self, message: str):
        """Update status bar"""
        status = self.query_one("#status_bar", Static)
        status.update(message)
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()
    
    def action_show_projects(self) -> None:
        """Show projects screen"""
        self.show_projects_screen()
    
    def action_show_scenarios(self) -> None:
        """Show scenarios screen"""
        self.show_scenarios_screen()
    
    def action_show_results(self) -> None:
        """Show results screen"""
        self.show_results_screen()
    
    def action_show_uml(self) -> None:
        """Show UML screen"""
        self.show_uml_screen()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission"""
        user_input = event.value.strip()
        input_widget = self.query_one("#user_input", Input)
        
        if not user_input:
            return
        
        # Clear input
        input_widget.value = ""
        
        # Process based on current screen
        if self.current_screen == "projects":
            self.handle_project_input(user_input)
        elif self.current_screen == "scenarios":
            self.handle_scenario_input(user_input)
        elif self.current_screen == "results":
            self.handle_results_input(user_input)
        elif self.current_screen == "uml":
            self.handle_uml_input(user_input)
    
    def handle_project_input(self, user_input: str):
        """Handle project selection/creation"""
        projects = self.project_manager.list_projects()
        
        # Check if selecting environment
        if user_input.startswith("env:"):
            if not self.current_project:
                self.show_error("Please select a project first")
                return
            
            env_name = user_input[4:].strip()
            environment = self.project_manager.load_environment(self.current_project, env_name)
            if environment:
                self.current_environment = environment
                self.update_status(f"Selected environment: {env_name}")
                self.show_projects_screen()
            else:
                self.show_error(f"Environment not found: {env_name}")
            return
        
        # Check if selecting host
        if user_input.startswith("host:"):
            if not self.current_project:
                self.show_error("Please select a project first")
                return
            
            host_name = user_input[5:].strip()
            host_config = self.project_manager.load_host_config(
                self.current_project, 
                host_name,
                self.current_environment
            )
            if host_config:
                self.current_host_config = host_config
                self.update_status(f"Selected host: {host_name}")
                self.show_projects_screen()
            else:
                self.show_error(f"Host not found: {host_name}")
            return
        
        # Check if creating new project
        if user_input.startswith("new:"):
            project_name = user_input[4:].strip()
            if project_name:
                self.project_manager.create_project(project_name)
                self.select_project(project_name, created=True)
                self.show_projects_screen()
            else:
                self.show_error("Project name cannot be empty")
            return
        
        # Check if number input
        if user_input.isdigit():
            num = int(user_input)
            if num in self.project_number_mapping:
                self.select_project(self.project_number_mapping[num])
                self.show_projects_screen()
            else:
                self.show_error(f"Invalid project number: {user_input}")
            return
        
        # Check if project name
        if user_input in projects:
            self.select_project(user_input)
            self.show_projects_screen()
        else:
            self.show_error(f"Project not found: {user_input}")

    def select_project(self, project_name: str, created: bool = False):
        """Select project and re-apply environment from the selected project."""
        previous_env_name = self.current_environment.name if self.current_environment else None
        self.current_project = project_name
        self.current_host_config = None
        self.current_environment = None

        env_name = self._apply_project_environment(project_name, previous_env_name)
        if created:
            status = f"Created and selected project: {project_name}"
        else:
            status = f"Selected project: {project_name}"

        if env_name:
            status += f" | Environment applied: {env_name}"
        else:
            status += " | Environment not found"

        self.update_status(status)

    def _apply_project_environment(self, project_name: str, preferred_env_name: Optional[str] = None) -> Optional[str]:
        """Load and apply an environment for the selected project."""
        env_names = self.project_manager.list_environments(project_name)
        if not env_names:
            return None

        target_env_name = None
        if preferred_env_name and preferred_env_name in env_names:
            target_env_name = preferred_env_name
        else:
            target_env_name = env_names[0]

        environment = self.project_manager.load_environment(project_name, target_env_name)
        if not environment:
            return None

        self.current_environment = environment
        return target_env_name
    
    def handle_scenario_input(self, user_input: str):
        """Handle scenario selection/creation/execution"""
        if not self.current_project:
            self.show_error("No project selected")
            return
        
        scenarios = self.project_manager.list_scenarios(self.current_project)
        
        # Check if back command
        if user_input.lower() == "back":
            self.selected_scenario = None
            # Hide panels
            log_panel = self.query_one("#log_panel")
            api_visualizer = self.query_one("#api_visualizer")
            log_panel.remove_class("visible")
            api_visualizer.remove_class("visible")
            self.show_scenarios_screen()
            return
        
        # Check if running selected scenario
        if user_input.lower() == "run" and self.selected_scenario:
            self.run_scenario(self.selected_scenario)
            return
        
        # Check if creating new scenario
        if user_input.startswith("new:"):
            scenario_name = user_input[4:].strip()
            if scenario_name:
                # Create basic scenario file (YAML format)
                scenario_path = Path("projects") / self.current_project / "scenario" / f"{scenario_name}.yaml"
                scenario_path.parent.mkdir(parents=True, exist_ok=True)
                
                basic_scenario = {
                    "name": scenario_name,
                    "description": "New scenario",
                    "steps": []
                }
                
                with open(scenario_path, 'w', encoding='utf-8') as f:
                    yaml.dump(basic_scenario, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                
                self.update_status(f"Created scenario: {scenario_name}")
                self.show_scenarios_screen()
            else:
                self.show_error("Scenario name cannot be empty")
            return
        
        # Check if number input (using index map from tree display)
        if user_input.isdigit():
            num = int(user_input)
            if hasattr(self, '_scenario_index_map') and num in self._scenario_index_map:
                scenario_name = self._scenario_index_map[num]
                self.selected_scenario = scenario_name
                self.show_scenario_detail(scenario_name)
            else:
                self.show_error(f"Invalid scenario number: {user_input}")
            return
        
        # Check if scenario name or path
        if user_input in scenarios:
            self.selected_scenario = user_input
            self.show_scenario_detail(user_input)
        else:
            self.show_error(f"Scenario not found: {user_input}")
    
    def handle_results_input(self, user_input: str):
        """Handle result viewing"""
        if not self.current_project:
            self.show_error("No project selected")
            return
        
        results = self.project_manager.list_results(self.current_project)
        
        if not results:
            self.show_error("No results available")
            return
        
        # Check if export command
        if user_input.lower() == "export":
            self.export_result_data()
            return
        
        # Check if back command
        if user_input.lower() == "back":
            # Hide analysis container
            analysis_container = self.query_one("#analysis_container")
            analysis_container.remove_class("visible")
            self.show_results_screen()
            return
        
        # Check if 'all' command for flat view
        if user_input.lower() == "all":
            self.show_results_flat_view()
            return
        
        # Check if number input (using index map from tree display)
        if user_input.isdigit():
            num = int(user_input)
            if hasattr(self, '_results_index_map') and num in self._results_index_map:
                result_path = self._results_index_map[num]
                self.show_result_detail(result_path)
            else:
                # Fallback to old index-based method
                idx = int(user_input) - 1
                if 0 <= idx < len(results):
                    result_path = results[idx]
                    self.show_result_detail(result_path)
                else:
                    self.show_error(f"Invalid result number: {user_input}")
            return
        
        self.show_error(f"Unknown command: {user_input}")
    
    def show_results_flat_view(self):
        """Show results in flat list view"""
        if not self.current_project:
            self.show_error("No project selected")
            return
        
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        
        results = self.project_manager.list_results(self.current_project)
        
        text = f"╔═ TEST RESULTS (Flat View) - {self.current_project} ═══════╗\n\n"
        
        if results:
            text += f"All Test Results (Total: {len(results)}):\n\n"
            
            # Group by type
            scenario_results = [r for r in results if 'scenario' in r.lower()]
            loadtest_results = [r for r in results if 'loadtest' in r.lower()]
            other_results = [r for r in results if r not in scenario_results and r not in loadtest_results]
            
            if scenario_results:
                text += f"📄 Scenario Tests ({len(scenario_results)}):\n"
                for idx, result in enumerate(scenario_results[:15], 1):
                    # Wrap long filenames
                    max_width = 80
                    if len(result) > max_width:
                        text += f"  {idx}. {result[:max_width]}\n"
                        remaining = result[max_width:]
                        while remaining:
                            text += f"      {remaining[:max_width]}\n"
                            remaining = remaining[max_width:]
                    else:
                        text += f"  {idx}. {result}\n"
                if len(scenario_results) > 15:
                    text += f"  ... and {len(scenario_results) - 15} more\n"
                text += "\n"
            
            if loadtest_results:
                text += f"⚡ Load Tests ({len(loadtest_results)}):\n"
                for idx, result in enumerate(loadtest_results[:10], len(scenario_results) + 1):
                    # Wrap long filenames
                    max_width = 80
                    if len(result) > max_width:
                        text += f"  {idx}. {result[:max_width]}\n"
                        remaining = result[max_width:]
                        while remaining:
                            text += f"      {remaining[:max_width]}\n"
                            remaining = remaining[max_width:]
                    else:
                        text += f"  {idx}. {result}\n"
                if len(loadtest_results) > 10:
                    text += f"  ... and {len(loadtest_results) - 10} more\n"
                text += "\n"
            
            if other_results:
                text += f"📋 Other Results ({len(other_results)}):\n"
                for idx, result in enumerate(other_results[:5], len(scenario_results) + len(loadtest_results) + 1):
                    # Wrap long filenames
                    max_width = 80
                    if len(result) > max_width:
                        text += f"  {idx}. {result[:max_width]}\n"
                        remaining = result[max_width:]
                        while remaining:
                            text += f"      {remaining[:max_width]}\n"
                            remaining = remaining[max_width:]
                    else:
                        text += f"  {idx}. {result}\n"
                text += "\n"
            
            # Create mapping for flat view
            self._results_index_map = {i+1: path for i, path in enumerate(results)}
        else:
            text += "No test results found.\n"
        
        text += "\n" + "─" * 60 + "\n"
        text += "\nActions:\n"
        text += "• Type result number to view details\n"
        text += "• Type 'back' to return to tree view\n"
        
        content.update(text)
        self.update_status(f"Results (Flat View): {len(results)} files")
        
        # Focus input
        self.query_one("#user_input", Input).focus()
    
    def show_result_detail(self, result_path: str):
        """Show detailed result information"""
        import statistics
        
        # Reset result data storage
        self.current_result_data = {
            "analysis": [],
            "api_flow": [],
            "log": [],
            "result_path": result_path
        }
        
        # Hide main content and show analysis container
        content = self.query_one("#content_area", Static)
        content.display = False
        
        analysis_container = self.query_one("#analysis_container")
        analysis_container.add_class("visible")
        
        # Get widgets
        analysis_content = self.query_one("#analysis_content", RichLog)
        log_output = self.query_one("#log_output", RichLog)
        api_flow = self.query_one("#api_flow", RichLog)
        
        log_output.clear()
        api_flow.clear()
        
        full_path = self.project_manager.get_results_dir(self.current_project) / result_path
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # Check test type
            test_type = result_data.get('test_type', 'scenario')
            
            if test_type == 'load_test':
                # Handle load test results
                self._show_load_test_detail(result_data, analysis_content, api_flow, log_output, result_path)
                return
            
            # Get scenario result
            scenario_result = result_data.get('scenario_results', [{}])[0]
            steps = scenario_result.get('steps', [])
            pre_request_results = scenario_result.get('pre_request_results', [])
            
            # Check if pre-request failed
            pre_request_failed = any(pr.get('status') == 'error' for pr in pre_request_results)
            
            # Calculate statistics
            response_times = [s['response_time_ms'] for s in steps if s.get('response_time_ms')]
            avg_response = statistics.mean(response_times) if response_times else 0
            min_response = min(response_times) if response_times else 0
            max_response = max(response_times) if response_times else 0
            
            # P50, P95, P99
            if response_times:
                sorted_times = sorted(response_times)
                p50 = sorted_times[int(len(sorted_times) * 0.50)]
                p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0]
                p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else sorted_times[0]
            else:
                p50 = p95 = p99 = 0
            
            total_assertions = sum(s.get('assertions_passed', 0) + s.get('assertions_failed', 0) for s in steps)
            passed_assertions = sum(s.get('assertions_passed', 0) for s in steps)
            failed_assertions = sum(s.get('assertions_failed', 0) for s in steps)
            
            # Clear and prepare left panel
            analysis_content.clear()
            
            # Helper functions to write and store
            def write_analysis(text):
                analysis_content.write(text)
                self.current_result_data["analysis"].append(text)
            
            def write_api_flow(text):
                api_flow.write(text)
                self.current_result_data["api_flow"].append(text)
            
            def write_log(text):
                log_output.write(text)
                self.current_result_data["log"].append(text)
            
            # Header
            write_analysis("╔═ RESULT ANALYSIS ══════════════════════════════╗")
            write_analysis(f"{scenario_result.get('scenario_name', 'Test')}")
            write_analysis("")
            
            status_emoji = "✓" if scenario_result.get('status') == 'success' else "✗"
            status_text = scenario_result.get('status', 'unknown').upper()
            
            # Pre-request 실패 강조 표시
            if pre_request_failed:
                write_analysis(f"{status_emoji} Status: {status_text}")
                write_analysis(f"⚠️  PRE-REQUEST (PACKAGE LIBRARY) FAILED")
            else:
                write_analysis(f"{status_emoji} Status: {status_text}")
            
            write_analysis(f"⏱  Duration: {scenario_result.get('duration_seconds', 0):.3f}s")
            write_analysis(f"📅 Time: {result_data.get('created_at', 'N/A')}")
            write_analysis("")
            
            # Request Summary
            write_analysis("═══ REQUEST SUMMARY ═══")
            write_analysis(f"Total Requests:    {scenario_result.get('total_requests', 0)}")
            write_analysis(f"✓ Successful:      {scenario_result.get('successful_requests', 0)}")
            write_analysis(f"✗ Failed:          {scenario_result.get('failed_requests', 0)}")
            write_analysis(f"⚠ Errors:          {scenario_result.get('error_requests', 0)}")
            write_analysis("")
            
            # Response Time Metrics
            write_analysis("═══ RESPONSE TIME METRICS ═══")
            write_analysis(f"Average:           {avg_response:.2f}ms")
            write_analysis(f"Min:               {min_response:.2f}ms")
            write_analysis(f"Max:               {max_response:.2f}ms")
            write_analysis(f"P50 (median):      {p50:.2f}ms")
            write_analysis(f"P95:               {p95:.2f}ms")
            write_analysis(f"P99:               {p99:.2f}ms")
            write_analysis("")
            
            # Assertion Results
            write_analysis("═══ ASSERTION RESULTS ═══")
            write_analysis(f"Total Assertions:  {total_assertions}")
            write_analysis(f"✓ Passed:          {passed_assertions}")
            write_analysis(f"✗ Failed:          {failed_assertions}")
            write_analysis("")
            
            # Pre-request Results
            if pre_request_results:
                write_analysis("═══ PRE-REQUEST (PACKAGE LIBRARY) ═══")
                
                # 실패한 pre-request 개수 계산
                failed_pre_reqs = sum(1 for pr in pre_request_results if pr.get('status') == 'error')
                success_pre_reqs = len(pre_request_results) - failed_pre_reqs
                
                write_analysis(f"Total: {len(pre_request_results)} | Success: {success_pre_reqs} | Failed: {failed_pre_reqs}")
                write_analysis("")
                
                for idx, pre_req in enumerate(pre_request_results, 1):
                    status_icon = "✓" if pre_req.get('status') == 'success' else "✗"
                    pre_req_name = pre_req.get('step_name', 'Unknown')
                    response_time = pre_req.get('response_time_ms', 0)
                    status_code = pre_req.get('status_code', 'N/A')
                    
                    write_analysis(f"{status_icon} [{idx}] {pre_req_name}")
                    write_analysis(f"     {pre_req.get('method', 'N/A')} | {status_code} | {response_time:.1f}ms")
                    
                    if pre_req.get('extracted_variables'):
                        extracted = pre_req['extracted_variables']
                        write_analysis(f"     Extracted: {', '.join(extracted.keys())}")
                    
                    if pre_req.get('error_message'):
                        error = pre_req['error_message']
                        if len(error) > 50:
                            error = error[:47] + "..."
                        write_analysis(f"     ❌ Error: {error}")
                
                write_analysis("")
            
            # Variables
            variables = scenario_result.get('variables', {})
            if variables:
                write_analysis("═══ EXTRACTED VARIABLES ═══")
                for key, value in variables.items():
                    write_analysis(f"  {key:<20} = {value}")
                write_analysis("")
            
            # Step Summary
            if steps:
                write_analysis("═══ STEP SUMMARY ═══")
                write_analysis("─" * 60)
                write_analysis(f"{'#':<3} {'Step Name':<32} {'Status':<6} {'Time':<10}")
                write_analysis("─" * 60)
                
                for idx, step in enumerate(steps, 1):
                    status_icon = "✓" if step.get('status') == 'success' else "✗"
                    step_name = step.get('step_name', 'Unknown')
                    if len(step_name) > 32:
                        step_name = step_name[:29] + "..."
                    response_time = f"{step.get('response_time_ms', 0):.1f}ms"
                    write_analysis(f"{idx:<3} {step_name:<32} {status_icon:<6} {response_time:<10}")
                
                write_analysis("─" * 60)
                write_analysis("")
            elif pre_request_failed:
                write_analysis("═══ SCENARIO NOT EXECUTED ═══")
                write_analysis("Scenario steps were not executed due to")
                write_analysis("pre-request (package library) failure.")
                write_analysis("")
            
            write_analysis("Type 'export' to save analysis to files")
            
            # Clear right panel
            api_flow.clear()
            log_output.clear()
            
            # Generate UML in API visualizer
            write_api_flow("╔" + "═" * 58 + "╗")
            write_api_flow("║" + " " * 20 + "API FLOW DIAGRAM" + " " * 22 + "║")
            write_api_flow("╚" + "═" * 58 + "╝")
            write_api_flow("")
            
            # Show pre-request steps in flow
            if pre_request_results:
                write_api_flow("🔧 Pre-request (Package Library):")
                write_api_flow("")
                
                for idx, pre_req in enumerate(pre_request_results, 1):
                    status_icon = "✓" if pre_req.get('status') == 'success' else "✗"
                    method = pre_req.get('method', 'N/A')
                    status_code = pre_req.get('status_code', 'N/A')
                    response_time = pre_req.get('response_time_ms', 0)
                    
                    # Shorten step name
                    step_name = pre_req.get('step_name', 'Step')
                    if len(step_name) > 35:
                        step_name = step_name[:32] + "..."
                    
                    write_api_flow(f"[P{idx}] {step_name}")
                    write_api_flow(f"     │")
                    write_api_flow(f"     ├─► {method}")
                    write_api_flow(f"     │")
                    
                    # Error 표시 강조
                    if pre_req.get('status') == 'error':
                        write_api_flow(f"     ◄─┤ [{status_icon}] ❌ FAILED | {response_time:.1f}ms")
                        if pre_req.get('error_message'):
                            error_msg = pre_req['error_message']
                            if len(error_msg) > 45:
                                error_msg = error_msg[:42] + "..."
                            write_api_flow(f"     │   Error: {error_msg}")
                    else:
                        write_api_flow(f"     ◄─┤ [{status_icon}] {status_code} | {response_time:.1f}ms")
                        
                        # Extracted variables
                        if pre_req.get('extracted_variables'):
                            vars_str = ", ".join(pre_req['extracted_variables'].keys())
                            if len(vars_str) > 40:
                                vars_str = vars_str[:37] + "..."
                            write_api_flow(f"     │   Extracted: {vars_str}")
                    
                    write_api_flow(f"     │")
                
                write_api_flow("─" * 58)
                
                if pre_request_failed:
                    write_api_flow("")
                    write_api_flow("❌ Pre-request failed - Scenario not executed")
                    write_api_flow("")
                else:
                    write_api_flow("")
                    write_api_flow("Main Scenario Steps:")
                    write_api_flow("")
            
            for idx, step in enumerate(steps, 1):
                status_icon = "✓" if step.get('status') == 'success' else "✗"
                method = step.get('method', 'GET')
                status_code = step.get('status_code', 'N/A')
                response_time = step.get('response_time_ms', 0)
                
                # Shorten step name
                step_name = step.get('step_name', 'Step')
                if len(step_name) > 35:
                    step_name = step_name[:32] + "..."
                
                # Request
                write_api_flow(f"[{idx}] {step_name}")
                write_api_flow(f"    │")
                write_api_flow(f"    ├─► {method}")
                
                # Response
                write_api_flow(f"    │")
                write_api_flow(f"    ◄─┤ [{status_icon}] {status_code} | {response_time:.1f}ms")
                
                # Assertions
                if step.get('assertion_details'):
                    passed = step.get('assertions_passed', 0)
                    failed = step.get('assertions_failed', 0)
                    write_api_flow(f"    │   ✓{passed} ✗{failed}")
                
                # Extracted variables
                if step.get('extracted_variables'):
                    vars_str = ", ".join(f"{k}={v}" for k, v in step['extracted_variables'].items())
                    if len(vars_str) > 40:
                        vars_str = vars_str[:37] + "..."
                    write_api_flow(f"    │   Var: {vars_str}")
                
                write_api_flow(f"    │")
            
            write_api_flow("")
            if pre_request_failed:
                write_api_flow("❌ Flow stopped - Pre-request failed")
            elif steps:
                write_api_flow("✓ Flow completed")
            else:
                write_api_flow("ℹ No scenario steps executed")
            
            # Detailed logs
            write_log("═" * 58)
            write_log(f"STEP-BY-STEP DETAILS")
            write_log("═" * 58)
            write_log("")
            
            # Pre-request details first
            if pre_request_results:
                write_log("─" * 58)
                write_log("🔧 PRE-REQUEST (PACKAGE LIBRARY)")
                write_log("─" * 58)
                write_log("")
                
                for idx, pre_req in enumerate(pre_request_results, 1):
                    status_icon = "✓" if pre_req.get('status') == 'success' else "✗"
                    
                    write_log(f"{status_icon} [{idx}] {pre_req.get('step_name', 'Unknown')}")
                    write_log(f"Method:      {pre_req.get('method', 'N/A')}")
                    write_log(f"URL:         {pre_req.get('url', 'N/A')}")
                    
                    if pre_req.get('status_code'):
                        write_log(f"Status:      {pre_req['status_code']}")
                    
                    write_log(f"Time:        {pre_req.get('response_time_ms', 0):.2f}ms")
                    
                    # Extracted variables
                    if pre_req.get('extracted_variables'):
                        write_log("")
                        write_log("Extracted Variables:")
                        for key, value in pre_req['extracted_variables'].items():
                            value_str = str(value)
                            if len(value_str) > 100:
                                value_str = value_str[:97] + "..."
                            write_log(f"  {key} = {value_str}")
                    
                    # Error message
                    if pre_req.get('error_message'):
                        write_log("")
                        write_log("=" * 58)
                        write_log("❌ PRE-REQUEST (PACKAGE LIBRARY) FAILED")
                        write_log("=" * 58)
                        write_log(f"Error: {pre_req['error_message']}")
                        write_log("=" * 58)
                    
                    write_log("")
                
                write_log("─" * 58)
                
                if pre_request_failed:
                    write_log("")
                    write_log("❌ Scenario steps were not executed due to")
                    write_log("   pre-request (package library) failure.")
                    write_log("")
                
                write_log("")
            
            for idx, step in enumerate(steps, 1):
                status_icon = "✓" if step.get('status') == 'success' else "✗"
                
                write_log("─" * 58)
                write_log(f"{status_icon} [{idx}] {step.get('step_name', 'Unknown Step')}")
                write_log("─" * 58)
                
                write_log(f"Method:      {step.get('method', 'GET')}")
                url = step.get('url', 'N/A')
                write_log(f"URL:         {url}")
                write_log(f"Status:      {step.get('status_code', 'N/A')}")
                write_log(f"Time:        {step.get('response_time_ms', 0):.2f}ms")
                
                # Request headers
                if step.get('request_headers'):
                    write_log("")
                    write_log("Request Headers:")
                    headers_str = json.dumps(step['request_headers'], indent=2, ensure_ascii=False)
                    lines = headers_str.split('\n')
                    for line in lines:
                        write_log(line)
                
                # Request query parameters
                if step.get('request_query_params'):
                    write_log("")
                    write_log("Request Query Params:")
                    params_str = json.dumps(step['request_query_params'], indent=2, ensure_ascii=False)
                    lines = params_str.split('\n')
                    for line in lines:
                        write_log(line)
                
                # Request body (full)
                if step.get('request_body'):
                    write_log("")
                    write_log("Request:")
                    body_str = json.dumps(step['request_body'], indent=2, ensure_ascii=False)
                    lines = body_str.split('\n')
                    for line in lines:
                        write_log(line)
                
                # Response body (full)
                if step.get('response_body'):
                    write_log("")
                    write_log("Response:")
                    body_str = json.dumps(step['response_body'], indent=2, ensure_ascii=False)
                    lines = body_str.split('\n')
                    for line in lines:
                        write_log(line)
                
                # Assertions
                if step.get('assertion_details'):
                    write_log("")
                    write_log("Assertions:")
                    for assertion in step['assertion_details']:
                        icon = "✓" if assertion.get('passed') else "✗"
                        msg = assertion.get('message', 'N/A')
                        write_log(f"  {icon} {msg}")
                
                # Extracted variables
                if step.get('extracted_variables'):
                    write_log("")
                    write_log("Variables:")
                    for key, value in step['extracted_variables'].items():
                        write_log(f"  {key} = {value}")
                
                # Error message with clear indication
                if step.get('error_message'):
                    write_log("")
                    error_msg = step['error_message']
                    
                    # Check error type by prefix
                    if '[PACKAGE_LIBRARY_ERROR]' in error_msg:
                        write_log("=" * 58)
                        write_log("❌ PACKAGE LIBRARY EXECUTION FAILED")
                        write_log("=" * 58)
                        # Remove prefix for cleaner display
                        clean_msg = error_msg.replace('[PACKAGE_LIBRARY_ERROR]', '').strip()
                        write_log(f"Error: {clean_msg}")
                        write_log("=" * 58)
                    elif '[API_REQUEST_ERROR]' in error_msg:
                        # Remove prefix for cleaner display
                        clean_msg = error_msg.replace('[API_REQUEST_ERROR]', '').strip()
                        write_log(f"⚠ API Request Error: {clean_msg}")
                    else:
                        # Fallback for backward compatibility
                        if 'package_library' in error_msg.lower() or 'pre-request' in error_msg.lower() or 'pre_request' in error_msg.lower():
                            write_log("=" * 58)
                            write_log("❌ PACKAGE LIBRARY EXECUTION FAILED")
                            write_log("=" * 58)
                            write_log(f"Error: {error_msg}")
                            write_log("=" * 58)
                        else:
                            write_log(f"⚠ Error: {error_msg}")
                
                write_log("")
            
            write_log("═" * 58)
            write_log("END OF LOG")
            write_log("═" * 58)
            
            self.update_status(f"Analyzing: {result_path}")
            
            # Focus input
            self.query_one("#user_input", Input).focus()
            
        except Exception as e:
            self.show_error(f"Failed to load result: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def export_result_data(self):
        """Export current result data to text files"""
        from pathlib import Path
        from datetime import datetime
        import re
        
        if not self.current_result_data.get("result_path"):
            self.show_error("No result loaded to export")
            return
        
        try:
            # Generate base filename from result path
            result_path = self.current_result_data["result_path"]
            base_name = Path(result_path).stem
            
            # Get scenario name (시나리오 이름 추출) - 파일시스템 안전한 이름으로 변환
            scenario_name = re.sub(r'[^\w\-_]', '_', base_name)
            
            # Generate timestamp directory (yyyyMMddHHmmss)
            timestamp_dir = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Create export directory structure: exports/{scenario_name}/{yyyyMMddHHmmss}/
            export_dir = self.project_manager.get_results_dir(self.current_project) / "exports" / scenario_name / timestamp_dir
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export Analysis Data
            analysis_file = export_dir / f"analysis.txt"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.current_result_data["analysis"]))
            
            # Export API Flow Diagram (UML)
            api_flow_file = export_dir / f"scenario_uml.txt"
            with open(api_flow_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.current_result_data["api_flow"]))
            
            # Export Detailed Log
            log_file = export_dir / f"detailed_log.txt"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.current_result_data["log"]))
            
            # Copy original scenario file
            import shutil
            scenario_file = None
            if Path(result_path).exists():
                # result 파일 경로에서 시나리오 파일 경로 유추
                result_file = Path(result_path)
                # results/xxx.json -> scenario/xxx.yaml 찾기
                scenario_dir = result_file.parent.parent / "scenario"
                
                # API별 폴더 구조 탐색
                for category in ['success', 'failure', 'integration', 'load_test']:
                    category_dir = scenario_dir / category
                    if category_dir.exists():
                        # API 폴더 탐색
                        for api_folder in category_dir.iterdir():
                            if api_folder.is_dir():
                                # YAML 파일 찾기
                                yaml_file = api_folder / f"{base_name}.yaml"
                                if yaml_file.exists():
                                    scenario_file = export_dir / f"scenario.yaml"
                                    shutil.copy(yaml_file, scenario_file)
                                    break
                    if scenario_file:
                        break
            
            # Show success message
            log_output = self.query_one("#log_output", RichLog)
            log_output.write("")
            log_output.write("═" * 58)
            log_output.write("✓ EXPORT COMPLETED")
            log_output.write("═" * 58)
            log_output.write("")
            log_output.write(f"Exported to: {export_dir}")
            log_output.write("")
            log_output.write(f"1. {analysis_file.name}")
            log_output.write(f"2. {api_flow_file.name}")
            log_output.write(f"3. {log_file.name}")
            if scenario_file:
                log_output.write(f"4. {scenario_file.name}")
            log_output.write("")
            
            file_count = 4 if scenario_file else 3
            self.update_status(f"✓ Exported {file_count} files to exports/{scenario_name}/{timestamp_dir}/")
            
        except Exception as e:
            self.show_error(f"Export failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _show_load_test_detail(self, result_data, analysis_content, api_flow, log_output, result_path):
        """Show load test result details"""
        import statistics
        
        load_result = result_data.get('load_test_result', {})
        
        # Clear panels
        analysis_content.clear()
        api_flow.clear()
        log_output.clear()
        
        # Helper functions to write and store
        def write_analysis(text):
            analysis_content.write(text)
            self.current_result_data["analysis"].append(text)
        
        def write_api_flow(text):
            api_flow.write(text)
            self.current_result_data["api_flow"].append(text)
        
        def write_log(text):
            log_output.write(text)
            self.current_result_data["log"].append(text)
        
        # === LEFT PANEL: Analysis Data ===
        write_analysis("╔═ LOAD TEST RESULT ANALYSIS ═══════════════════╗")
        analysis_content.write(f"{load_result.get('test_name', 'Load Test')}")
        analysis_content.write("")
        
        # Test Configuration
        analysis_content.write("═══ TEST CONFIGURATION ═══")
        analysis_content.write(f"Duration:          {load_result.get('duration_seconds', 0):.2f}s")
        analysis_content.write(f"Target TPS:        {load_result.get('target_tps', 0)}")
        analysis_content.write(f"Actual Avg TPS:    {load_result.get('actual_avg_tps', 0):.2f}")
        tps_achievement = (load_result.get('actual_avg_tps', 0) / load_result.get('target_tps', 1) * 100) if load_result.get('target_tps', 0) > 0 else 0
        analysis_content.write(f"TPS Achievement:   {tps_achievement:.1f}%")
        analysis_content.write("")
        
        # Request Summary
        analysis_content.write("═══ REQUEST SUMMARY ═══")
        analysis_content.write(f"Total Requests:    {load_result.get('total_requests', 0)}")
        analysis_content.write(f"✓ Successful:      {load_result.get('successful_requests', 0)}")
        analysis_content.write(f"✗ Failed:          {load_result.get('failed_requests', 0)}")
        analysis_content.write(f"⚠ Errors:          {load_result.get('error_requests', 0)}")
        analysis_content.write(f"Success Rate:      {load_result.get('success_rate', 0):.2f}%")
        analysis_content.write("")
        
        # Response Time Metrics
        response_times = load_result.get('response_times', [])
        if response_times:
            sorted_times = sorted(response_times)
            avg = statistics.mean(sorted_times)
            p50 = statistics.median(sorted_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            p95 = sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1]
            p99 = sorted_times[p99_idx] if p99_idx < len(sorted_times) else sorted_times[-1]
            
            analysis_content.write("═══ RESPONSE TIME METRICS ═══")
            analysis_content.write(f"Average:           {avg:.2f}ms")
            analysis_content.write(f"Min:               {min(sorted_times):.2f}ms")
            analysis_content.write(f"Max:               {max(sorted_times):.2f}ms")
            analysis_content.write(f"P50 (median):      {p50:.2f}ms")
            analysis_content.write(f"P95:               {p95:.2f}ms")
            analysis_content.write(f"P99:               {p99:.2f}ms")
            analysis_content.write("")
        
        # Status Code Distribution
        status_dist = load_result.get('status_code_distribution', {})
        if status_dist:
            analysis_content.write("═══ STATUS CODE DISTRIBUTION ═══")
            for code, count in sorted(status_dist.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0):
                percentage = (count / load_result.get('total_requests', 1) * 100) if load_result.get('total_requests', 0) > 0 else 0
                analysis_content.write(f"  {code}:  {count:>6}  ({percentage:.1f}%)")
            analysis_content.write("")
        
        # Error Distribution
        error_dist = load_result.get('error_distribution', {})
        if error_dist:
            analysis_content.write("═══ ERROR DISTRIBUTION ═══")
            for error, count in sorted(error_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
                error_short = error[:100] + "..." if len(error) > 100 else error
                analysis_content.write(f"  {count:>4}x  {error_short}")
            if len(error_dist) > 10:
                analysis_content.write(f"  ... and {len(error_dist) - 10} more errors")
            analysis_content.write("")
        
        analysis_content.write("")
        analysis_content.write("Type 'back' to return to results list")
        
        # === RIGHT PANEL TOP: TPS Timeline ===
        api_flow.write("╔" + "═" * 58 + "╗")
        api_flow.write("║" + " " * 18 + "TPS TIMELINE GRAPH" + " " * 20 + "║")
        api_flow.write("╚" + "═" * 58 + "╝")
        api_flow.write("")
        
        metrics_timeline = load_result.get('metrics_timeline', [])
        if metrics_timeline:
            target_tps = load_result.get('target_tps', 100)
            max_display = 60  # Show first 60 seconds
            
            for i, metrics in enumerate(metrics_timeline[:max_display], 1):
                current_tps = metrics.get('current_tps', 0)
                bar_length = int((current_tps / target_tps) * 40) if target_tps > 0 else 0
                bar_length = min(bar_length, 40)
                bar = "█" * bar_length
                
                # Color indicator
                if current_tps >= target_tps * 0.9:
                    indicator = "✓"
                elif current_tps >= target_tps * 0.7:
                    indicator = "~"
                else:
                    indicator = "↓"
                
                api_flow.write(f"{i:3}s {indicator} │{bar:<40}│ {current_tps:.1f}")
            
            if len(metrics_timeline) > max_display:
                api_flow.write(f"... ({len(metrics_timeline) - max_display} more seconds)")
            
            api_flow.write("")
            api_flow.write(f"Target: {target_tps} TPS")
            api_flow.write(f"Legend: ✓ ≥90%  ~ ≥70%  ↓ <70%")
        else:
            api_flow.write("No timeline data available")
        
        # === RIGHT PANEL BOTTOM: Detailed Metrics Log ===
        log_output.write("═" * 58)
        log_output.write("LOAD TEST DETAILED METRICS")
        log_output.write("═" * 58)
        log_output.write("")
        
        log_output.write(f"Test Name:         {load_result.get('test_name', 'N/A')}")
        log_output.write(f"Start Time:        {load_result.get('start_time', 'N/A')}")
        log_output.write(f"End Time:          {load_result.get('end_time', 'N/A')}")
        log_output.write(f"Duration:          {load_result.get('duration_seconds', 0):.3f}s")
        log_output.write("")
        
        log_output.write("Performance:")
        log_output.write(f"  Target TPS:      {load_result.get('target_tps', 0)}")
        log_output.write(f"  Actual TPS:      {load_result.get('actual_avg_tps', 0):.2f}")
        log_output.write(f"  Achievement:     {tps_achievement:.1f}%")
        log_output.write("")
        
        log_output.write("Requests:")
        log_output.write(f"  Total:           {load_result.get('total_requests', 0)}")
        log_output.write(f"  Successful:      {load_result.get('successful_requests', 0)}")
        log_output.write(f"  Failed:          {load_result.get('failed_requests', 0)}")
        log_output.write(f"  Errors:          {load_result.get('error_requests', 0)}")
        log_output.write(f"  Success Rate:    {load_result.get('success_rate', 0):.2f}%")
        log_output.write("")
        
        if response_times:
            log_output.write("Response Times (ms):")
            log_output.write(f"  Average:         {avg:.2f}")
            log_output.write(f"  Minimum:         {min(sorted_times):.2f}")
            log_output.write(f"  Maximum:         {max(sorted_times):.2f}")
            log_output.write(f"  Median (P50):    {p50:.2f}")
            log_output.write(f"  P95:             {p95:.2f}")
            log_output.write(f"  P99:             {p99:.2f}")
            log_output.write("")
        
        # Metrics timeline summary (show every 10 seconds)
        if metrics_timeline:
            log_output.write("TPS Over Time (10s intervals):")
            log_output.write("─" * 58)
            for i, metrics in enumerate(metrics_timeline[::10], 1):
                elapsed = metrics.get('elapsed_seconds', 0)
                tps = metrics.get('current_tps', 0)
                active = metrics.get('active_connections', 0)
                log_output.write(f"  {elapsed:.0f}s: TPS={tps:.1f}, Active={active}")
            log_output.write("")
        
        log_output.write("═" * 58)
        log_output.write("END OF REPORT")
        log_output.write("═" * 58)
        
        self.update_status(f"Analyzing: {result_path}")
        
        # Focus input
        self.query_one("#user_input", Input).focus()
    
    def handle_uml_input(self, user_input: str):
        """Handle UML generation"""
        if not self.current_project:
            self.show_error("No project selected")
            return
        
        scenarios = self.project_manager.list_scenarios(self.current_project)
        
        # Check if number input
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(scenarios):
                scenario_name = scenarios[idx]
                self.generate_uml_for_scenario(scenario_name)
            else:
                self.show_error(f"Invalid scenario number: {user_input}")
            return
        
        # Check if scenario name
        if user_input in scenarios:
            self.generate_uml_for_scenario(user_input)
        else:
            self.show_error(f"Scenario not found: {user_input}")
    
    def generate_uml_for_scenario(self, scenario_name: str):
        """Generate UML diagrams for a scenario"""
        try:
            from datetime import datetime
            
            # Load scenario
            scenario = self.project_manager.load_scenario(self.current_project, scenario_name)
            
            # Generate diagrams
            sequence = UMLGenerator.generate_sequence_diagram(scenario)
            flowchart = UMLGenerator.generate_flowchart(scenario)
            text_diagram = UMLGenerator.generate_text_diagram(scenario)
            
            # Save diagrams
            date_str = datetime.now().strftime("%Y%m%d")
            results_dir = self.project_manager.get_results_dir(self.current_project)
            uml_dir = results_dir / "uml" / date_str
            uml_dir.mkdir(parents=True, exist_ok=True)
            
            scenario_name_safe = scenario.name.replace(" ", "_").replace("/", "_")
            UMLGenerator.save_diagram(sequence, str(uml_dir / f"{scenario_name_safe}_sequence.puml"))
            UMLGenerator.save_diagram(flowchart, str(uml_dir / f"{scenario_name_safe}_flowchart.puml"))
            UMLGenerator.save_diagram(text_diagram, str(uml_dir / f"{scenario_name_safe}_diagram.txt"))
            
            self.update_status(f"✓ Generated UML for {scenario_name} in {uml_dir}")
            
            # Show success in content area
            content = self.query_one("#content_area", Static)
            text = f"╔═ UML GENERATED - {scenario_name} ══════════════════╗\n\n"
            text += f"✓ UML diagrams generated successfully!\n\n"
            text += f"Location: {uml_dir}\n\n"
            text += f"Files:\n"
            text += f"  • {scenario_name_safe}_sequence.puml\n"
            text += f"  • {scenario_name_safe}_flowchart.puml\n"
            text += f"  • {scenario_name_safe}_diagram.txt\n\n"
            text += "─" * 60 + "\n"
            text += "\nYou can view these files with PlantUML viewer\n"
            content.update(text)
            
        except Exception as e:
            self.show_error(f"Failed to generate UML: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_scenario_detail(self, scenario_name: str):
        """Show scenario details"""
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        
        # Find scenario file (try yaml, yml, json)
        base_path = Path("projects") / self.current_project / "scenario"
        scenario_path = None
        for ext in ['.yaml', '.yml', '.json']:
            candidate = base_path / f"{scenario_name}{ext}"
            if candidate.exists():
                scenario_path = candidate
                break
        
        if not scenario_path:
            content.update(f"[red]Scenario file not found: {scenario_name}[/red]")
            return
        
        try:
            # Load based on extension
            if scenario_path.suffix in ['.yaml', '.yml']:
                with open(scenario_path, 'r', encoding='utf-8') as f:
                    scenario_data = yaml.safe_load(f)
            else:
                with open(scenario_path, 'r') as f:
                    scenario_data = json.load(f)
            
            text = f"╔═ SCENARIO DETAIL - {scenario_name} ═══════════════════════╗\n\n"
            text += f"Name: {scenario_data.get('name', scenario_name)}\n"
            text += f"Description: {scenario_data.get('description', 'N/A')}\n\n"
            
            steps = scenario_data.get('steps', [])
            text += f"Steps: {len(steps)}\n\n"
            
            for idx, step in enumerate(steps[:10], 1):  # Show first 10 steps
                text += f"  {idx}. {step.get('method', 'GET')} {step.get('path', '/')}\n"
                if step.get('description'):
                    text += f"     {step['description']}\n"
            
            if len(steps) > 10:
                text += f"\n  ... and {len(steps) - 10} more steps\n"
            
            text += "\n" + "─" * 60 + "\n"
            text += "\nActions:\n"
            text += "• Type 'run' to execute this scenario\n"
            text += "• Type 'back' to return to scenario list\n"
            
            content.update(text)
            self.update_status(f"Viewing: {scenario_name}")
            
            # Focus input
            self.query_one("#user_input", Input).focus()
            
        except Exception as e:
            self.show_error(f"Failed to load scenario: {str(e)}")
    
    @work(thread=True)
    def run_scenario(self, scenario_name: str):
        """Execute scenario test"""
        
        def update_ui(callback):
            """Helper to update UI from thread"""
            self.call_from_thread(callback)
        
        # Show panels and initialize
        def init_ui():
            # Show main content during execution
            content = self.query_one("#content_area", Static)
            content.display = True
            
            analysis_container = self.query_one("#analysis_container")
            analysis_container.remove_class("visible")
            
            log_output = self.query_one("#log_output", RichLog)
            api_flow = self.query_one("#api_flow", RichLog)
            
            log_output.clear()
            api_flow.clear()
            
            text = f"╔═ RUNNING TEST - {scenario_name} ═══════════════════════════╗\n\n"
            text += "Initializing test...\n"
            content.update(text)
            
            log_output.write(f"Starting test: {scenario_name}")
        
        update_ui(init_ui)
        
        try:
            # Load scenario first to check if environment is needed
            scenario = self.project_manager.load_scenario(self.current_project, scenario_name)
            
            # Load environment if scenario specifies one and not already loaded
            if scenario.environment and not self.current_environment:
                env = self.project_manager.load_environment(self.current_project, scenario.environment)
                if env:
                    self.current_environment = env
                    def log_env_loaded():
                        log_output = self.query_one("#log_output", RichLog)
                        log_output.write(f"✓ Auto-loaded environment: {env.name}")
                    update_ui(log_env_loaded)
            
            # Load hosts configuration with environment variable substitution
            hosts = self.project_manager.load_hosts_config(
                self.current_project, 
                self.current_environment
            )
            if not hosts:
                def show_err():
                    self.show_error("No hosts configured in hosts.json")
                update_ui(show_err)
                return
            
            # Use first host by default
            host_name = list(hosts.keys())[0]
            host_config = hosts[host_name]
            
            # Update UI with host info
            def update_host_info():
                log_output = self.query_one("#log_output", RichLog)
                api_flow = self.query_one("#api_flow", RichLog)
                content = self.query_one("#content_area", Static)
                
                log_output.write(f"Host: {host_name} ({host_config.base_url})")
                log_output.write(f"Scenario: {len(scenario.steps)} steps")
                log_output.write("")
                
                # Draw initial flow diagram
                source_name = "CLIENT"
                target_name = host_config.base_url.replace("https://", "").replace("http://", "")
                if len(target_name) > 50:
                    target_name = target_name[:47] + "..."
                
                api_flow.write("=" * 80)
                api_flow.write(f"{source_name:<25}     {target_name:>50}")
                api_flow.write("=" * 80)
                api_flow.write("")
                
                text = f"╔═ RUNNING TEST - {scenario_name} ═══════════════════════════╗\n\n"
                text += f"Target: {host_config.base_url}\n"
                text += f"Starting test execution...\n\n"
                content.update(text)
            
            update_ui(update_host_info)
            
            # Check if this is a load test or regular scenario
            import asyncio
            
            if scenario.load_test_config:
                # Load test mode
                from app.core.load_test_engine import LoadTestEngine
                
                def update_load_test_info():
                    log_output = self.query_one("#log_output", RichLog)
                    content = self.query_one("#content_area", Static)
                    
                    log_output.write("⚡ LOAD TEST MODE ENABLED")
                    log_output.write(f"Duration: {scenario.load_test_config.duration_seconds}s")
                    log_output.write(f"Target TPS: {scenario.load_test_config.target_tps}")
                    log_output.write(f"Ramp-up: {scenario.load_test_config.ramp_up_seconds}s")
                    log_output.write(f"Max Concurrent: {scenario.load_test_config.max_concurrent}")
                    log_output.write(f"Distribution: {scenario.load_test_config.distribution}")
                    log_output.write("")
                    
                    text = f"╔═ LOAD TEST - {scenario_name} ═══════════════════════════╗\n\n"
                    text += f"Target: {host_config.base_url}\n"
                    text += f"Duration: {scenario.load_test_config.duration_seconds}s | "
                    text += f"Target TPS: {scenario.load_test_config.target_tps}\n\n"
                    text += "Test in progress...\n"
                    content.update(text)
                
                update_ui(update_load_test_info)
                
                # Metrics callback
                def on_metrics(metrics):
                    def update_metrics():
                        content = self.query_one("#content_area", Static)
                        log_output = self.query_one("#log_output", RichLog)
                        
                        elapsed = int(metrics.elapsed_seconds)
                        text = f"╔═ LOAD TEST - {scenario_name} ═══════════════════════════╗\n\n"
                        text += f"Target: {host_config.base_url}\n"
                        text += f"Elapsed: {elapsed}s / {scenario.load_test_config.duration_seconds}s\n\n"
                        text += f"📊 Real-time Metrics:\n"
                        text += f"  TPS: {metrics.current_tps:.1f} / {scenario.load_test_config.target_tps}\n"
                        text += f"  Total Requests: {metrics.total_requests}\n"
                        text += f"  Success: {metrics.successful_requests} | "
                        text += f"Failed: {metrics.failed_requests} | "
                        text += f"Errors: {metrics.error_requests}\n"
                        text += f"  Active Connections: {metrics.active_connections}\n\n"
                        text += f"⏱️  Response Times:\n"
                        text += f"  Avg: {metrics.avg_response_time_ms:.0f}ms\n"
                        text += f"  P50: {metrics.p50_response_time_ms:.0f}ms\n"
                        text += f"  P95: {metrics.p95_response_time_ms:.0f}ms\n"
                        text += f"  P99: {metrics.p99_response_time_ms:.0f}ms\n"
                        content.update(text)
                    
                    update_ui(update_metrics)
                
                engine = LoadTestEngine(host_config)
                result = asyncio.run(engine.execute_load_test(
                    scenario, 
                    scenario.load_test_config,
                    progress_callback=on_metrics
                ))
                
            else:
                # Regular scenario mode
                project_path = str(self.project_manager.get_project_path(self.current_project))
                engine = ScenarioEngine(host_config, project_path=project_path, environment=self.current_environment)
                
                # Progress callback
                def on_progress(step_name: str, current: int, total: int):
                    def update_progress():
                        log_output = self.query_one("#log_output", RichLog)
                        log_output.write(f"Step {current}/{total}: {step_name}")
                    update_ui(update_progress)
                
                # Check for pre-request script/config
                pre_request_script = None
                if self.current_environment:
                    # Look for pre_request.json or pre_request.py in package_library
                    package_lib = self.project_manager.get_package_library_path(self.current_project)
                    
                    # Prefer JSON config over Python script
                    if (package_lib / "pre_request.json").exists():
                        pre_request_script = "pre_request.json"
                    elif (package_lib / "pre_request.py").exists():
                        pre_request_script = "pre_request.py"
                    
                    if pre_request_script:
                        def log_pre_request():
                            log_output = self.query_one("#log_output", RichLog)
                            log_output.write(f"Environment: {self.current_environment.name}")
                            log_output.write(f"")
                            log_output.write(f"🔧 Package Library: {pre_request_script}")
                            log_output.write(f"{'─'*60}")
                            log_output.write("")
                        update_ui(log_pre_request)
                
                # Execute scenario
                result = asyncio.run(engine.execute_scenario(scenario, progress_callback=on_progress, pre_request_script=pre_request_script))
            
            # Display results based on test type
            if scenario.load_test_config:
                # Load test results
                def show_load_test_results():
                    log_output = self.query_one("#log_output", RichLog)
                    content = self.query_one("#content_area", Static)
                    api_flow = self.query_one("#api_flow", RichLog)
                    
                    log_output.write("")
                    log_output.write("✓ Load test completed")
                    log_output.write("")
                    log_output.write("Summary:")
                    log_output.write("-" * 60)
                    log_output.write(f"Duration: {result.duration_seconds:.2f}s")
                    log_output.write(f"Target TPS: {result.target_tps} | Actual: {result.actual_avg_tps:.2f}")
                    log_output.write(f"Total Requests: {result.total_requests}")
                    log_output.write(f"Success: {result.successful_requests} | Failed: {result.failed_requests} | Errors: {result.error_requests}")
                    log_output.write(f"Success Rate: {result.success_rate:.1f}%")
                    log_output.write("")
                    
                    if result.response_times:
                        import statistics
                        sorted_times = sorted(result.response_times)
                        avg = statistics.mean(sorted_times)
                        p50 = statistics.median(sorted_times)
                        p95_idx = int(len(sorted_times) * 0.95)
                        p99_idx = int(len(sorted_times) * 0.99)
                        p95 = sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1]
                        p99 = sorted_times[p99_idx] if p99_idx < len(sorted_times) else sorted_times[-1]
                        
                        log_output.write("Response Times:")
                        log_output.write(f"  Avg: {avg:.0f}ms | Min: {min(sorted_times):.0f}ms | Max: {max(sorted_times):.0f}ms")
                        log_output.write(f"  P50: {p50:.0f}ms | P95: {p95:.0f}ms | P99: {p99:.0f}ms")
                        log_output.write("")
                    
                    if result.status_code_distribution:
                        log_output.write("Status Code Distribution:")
                        for code, count in sorted(result.status_code_distribution.items()):
                            log_output.write(f"  {code}: {count}")
                        log_output.write("")
                    
                    # Display summary
                    text = f"╔═ LOAD TEST COMPLETED - {scenario_name} ═════════════════╗\n\n"
                    text += f"✓ Load test completed!\n\n"
                    text += f"📊 Performance Metrics:\n"
                    text += f"  Target TPS: {result.target_tps}\n"
                    text += f"  Actual TPS: {result.actual_avg_tps:.2f}\n"
                    text += f"  Duration: {result.duration_seconds:.2f}s\n\n"
                    text += f"📈 Requests:\n"
                    text += f"  Total: {result.total_requests}\n"
                    text += f"  Success: {result.successful_requests}\n"
                    text += f"  Failed: {result.failed_requests}\n"
                    text += f"  Errors: {result.error_requests}\n"
                    text += f"  Success Rate: {result.success_rate:.1f}%\n\n"
                    
                    if result.response_times:
                        text += f"⏱️  Response Times:\n"
                        text += f"  Avg: {avg:.0f}ms | P50: {p50:.0f}ms\n"
                        text += f"  P95: {p95:.0f}ms | P99: {p99:.0f}ms\n\n"
                    
                    text += "─" * 60 + "\n"
                    text += "\nType 'back' to return to scenario list\n"
                    
                    content.update(text)
                    
                    # Show TPS timeline in API flow
                    api_flow.write("")
                    api_flow.write("TPS Timeline (1-second intervals):")
                    api_flow.write("=" * 80)
                    for i, metrics in enumerate(result.metrics_timeline[:60], 1):  # Show first 60 seconds
                        bar_length = int(metrics.current_tps / result.target_tps * 40) if result.target_tps > 0 else 0
                        bar = "█" * min(bar_length, 40)
                        api_flow.write(f"{i:3}s │{bar:<40}│ {metrics.current_tps:.1f} TPS")
                    
                    self.update_status(f"Load test completed: {scenario_name}")
                
                update_ui(show_load_test_results)
                
            else:
                # Regular scenario results
                def visualize_results():
                    api_flow = self.query_one("#api_flow", RichLog)
                    log_output = self.query_one("#log_output", RichLog)
                    
                    for idx, step in enumerate(result.steps, 1):
                        status_icon = "OK" if step.status == "success" else "ERR"
                        status_code = step.status_code or "N/A"
                        
                        # Truncate URL if too long
                        url_path = step.url
                        if len(url_path) > 60:
                            url_path = url_path[:57] + "..."
                        
                        # Request arrow
                        api_flow.write(f"{step.method:>6} ───────────────► {url_path}")
                        
                        # Response arrow
                        api_flow.write(f"       ◄─────────────── [{status_icon}] {status_code} | {step.response_time_ms:.0f}ms")
                        
                        if idx < len(result.steps):
                            api_flow.write("       │")
                    
                    api_flow.write("")
                    api_flow.write("✓ Communication completed")
                    log_output.write("")
                
                update_ui(visualize_results)
                
                # Calculate metrics
                avg_response_time_ms = 0
                if result.steps:
                    total_response_time = sum(step.response_time_ms for step in result.steps)
                    avg_response_time_ms = total_response_time / len(result.steps)
                
                avg_response_time_s = avg_response_time_ms / 1000.0
                success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
                
                # Update final results
                def show_results():
                    log_output = self.query_one("#log_output", RichLog)
                    content = self.query_one("#content_area", Static)
                    
                    log_output.write("✓ Test completed successfully")
                    log_output.write("")
                    
                    # Log step details
                    log_output.write("Step Results:")
                    log_output.write("-" * 60)
                    for idx, step in enumerate(result.steps, 1):
                        status_icon = "✓" if step.status == "success" else "✗"
                        log_output.write(
                            f"{status_icon} {idx}. {step.step_name} - {step.response_time_ms:.0f}ms (HTTP {step.status_code or 'N/A'})"
                        )
                        if step.error_message:
                            error_msg = step.error_message
                            # Check error type by prefix
                            if '[PACKAGE_LIBRARY_ERROR]' in error_msg:
                                clean_msg = error_msg.replace('[PACKAGE_LIBRARY_ERROR]', '').strip()
                                log_output.write(f"   ❌ PACKAGE LIBRARY: {clean_msg}")
                            elif '[API_REQUEST_ERROR]' in error_msg:
                                clean_msg = error_msg.replace('[API_REQUEST_ERROR]', '').strip()
                                log_output.write(f"   ⚠ API Error: {clean_msg}")
                            else:
                                # Fallback for backward compatibility
                                if 'package_library' in error_msg.lower() or 'pre-request' in error_msg.lower() or 'pre_request' in error_msg.lower():
                                    log_output.write(f"   ❌ PACKAGE LIBRARY: {error_msg}")
                                else:
                                    log_output.write(f"   ⚠ Error: {error_msg}")
                    
                    log_output.write("")
                    log_output.write("Summary:")
                    log_output.write("-" * 60)
                    log_output.write(f"Total: {result.total_requests} requests")
                    log_output.write(f"Success: {result.successful_requests} | Failed: {result.failed_requests} | Errors: {result.error_requests}")
                    log_output.write(f"Avg Response: {avg_response_time_s:.3f}s ({avg_response_time_ms:.0f}ms)")
                    log_output.write(f"Success Rate: {success_rate:.1f}%")
                    log_output.write(f"Duration: {result.duration_seconds:.2f}s")
                    log_output.write(f"Status: {result.status.value.upper()}")
                    
                    # Display results
                    text = f"╔═ TEST COMPLETED - {scenario_name} ════════════════════════╗\n\n"
                    text += f"✓ Test completed!\n\n"
                    text += f"Total requests: {result.total_requests}\n"
                    text += f"Successful: {result.successful_requests}\n"
                    text += f"Failed: {result.failed_requests}\n"
                    if result.error_requests > 0:
                        text += f"Errors: {result.error_requests}\n"
                    text += f"Average response time: {avg_response_time_s:.3f}s ({avg_response_time_ms:.0f}ms)\n"
                    text += f"Success rate: {success_rate:.1f}%\n"
                    text += f"Duration: {result.duration_seconds:.2f}s\n\n"
                    text += "─" * 60 + "\n"
                    text += "\nType 'back' to return to scenario list\n"
                    text += "Log content can be selected and copied\n"
                    
                    content.update(text)
                    self.update_status(f"Test completed: {scenario_name}")
                
                update_ui(show_results)
            
            # Save report to results directory
            report_path = None
            try:
                results_dir = self.project_manager.get_results_dir(self.current_project)
                
                # Save appropriate report type
                if scenario.load_test_config:
                    report_path = ReportGenerator.save_load_test_report(result, results_dir, self.current_project)
                else:
                    report_path = ReportGenerator.save_scenario_report(result, results_dir, self.current_project)
                
                def log_saved():
                    log_output = self.query_one("#log_output", RichLog)
                    log_output.write("")
                    log_output.write(f"💾 Report saved: {report_path.name}")
                update_ui(log_saved)
                
                # Generate UML diagrams (only for regular scenarios)
                if not scenario.load_test_config:
                    try:
                        from datetime import datetime
                        date_str = datetime.now().strftime("%Y%m%d")
                        uml_dir = results_dir / "uml" / date_str
                        uml_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Generate diagrams
                        sequence = UMLGenerator.generate_sequence_diagram(scenario)
                        flowchart = UMLGenerator.generate_flowchart(scenario)
                        text_diagram = UMLGenerator.generate_text_diagram(scenario)
                        
                        # Save diagrams
                        scenario_name_safe = scenario.name.replace(" ", "_").replace("/", "_")
                        UMLGenerator.save_diagram(sequence, str(uml_dir / f"{scenario_name_safe}_sequence.puml"))
                        UMLGenerator.save_diagram(flowchart, str(uml_dir / f"{scenario_name_safe}_flowchart.puml"))
                        UMLGenerator.save_diagram(text_diagram, str(uml_dir / f"{scenario_name_safe}_diagram.txt"))
                        
                        def log_uml_saved():
                            log_output = self.query_one("#log_output", RichLog)
                            log_output.write(f"🎨 UML diagrams saved to: {uml_dir}")
                        update_ui(log_uml_saved)
                    except Exception as uml_err:
                        def log_uml_error():
                            log_output = self.query_one("#log_output", RichLog)
                            log_output.write(f"⚠️  Warning: Failed to generate UML: {str(uml_err)}")
                        update_ui(log_uml_error)
                
            except Exception as save_err:
                def log_save_error():
                    log_output = self.query_one("#log_output", RichLog)
                    log_output.write(f"⚠️  Warning: Failed to save report: {str(save_err)}")
                update_ui(log_save_error)
            
            # Auto-navigate to result detail view after execution
            if report_path:
                # Get relative path from results directory
                relative_path = report_path.relative_to(results_dir)
                
                def auto_show_result():
                    # Switch to results screen first
                    self.current_screen = "results"
                    # Show the result detail
                    self.show_result_detail(str(relative_path))
                
                # Wait a moment before switching to results
                import time
                time.sleep(1.5)
                update_ui(auto_show_result)
            
        except Exception as e:
            def show_error_msg():
                log_output = self.query_one("#log_output", RichLog)
                content = self.query_one("#content_area", Static)
                
                error_str = str(e)
                
                # Check error type by prefix
                if '[PACKAGE_LIBRARY_ERROR]' in error_str:
                    clean_error = error_str.replace('[PACKAGE_LIBRARY_ERROR]', '').strip()
                    
                    log_output.write("")
                    log_output.write("=" * 60)
                    log_output.write("❌ PACKAGE LIBRARY EXECUTION FAILED")
                    log_output.write("=" * 60)
                    log_output.write(f"Error: {clean_error}")
                    log_output.write("=" * 60)
                    log_output.write("")
                    
                    text = f"╔═ TEST FAILED - {scenario_name} ════════════════════════╗\n\n"
                    text += f"❌ Package Library Execution Failed\n\n"
                    text += f"Error: {clean_error}\n\n"
                    text += "─" * 60 + "\n"
                    text += "\nPlease check:\n"
                    text += "• Package library script/config syntax\n"
                    text += "• Pre-request API endpoint availability\n"
                    text += "• Environment variables\n"
                    text += "• Authentication tokens\n"
                    content.update(text)
                    
                elif '[API_REQUEST_ERROR]' in error_str:
                    clean_error = error_str.replace('[API_REQUEST_ERROR]', '').strip()
                    
                    log_output.write(f"✗ API Request Error: {clean_error}")
                    
                    text = f"╔═ TEST FAILED - {scenario_name} ════════════════════════╗\n\n"
                    text += f"❌ API Request Failed\n\n"
                    text += f"Error: {clean_error}\n\n"
                    text += "─" * 60 + "\n"
                    content.update(text)
                    
                else:
                    # Fallback for backward compatibility
                    if 'package_library' in error_str.lower() or 'pre-request' in error_str.lower() or 'pre_request' in error_str.lower():
                        log_output.write("")
                        log_output.write("=" * 60)
                        log_output.write("❌ PACKAGE LIBRARY EXECUTION FAILED")
                        log_output.write("=" * 60)
                        log_output.write(f"Error: {error_str}")
                        log_output.write("=" * 60)
                        log_output.write("")
                        
                        text = f"╔═ TEST FAILED - {scenario_name} ════════════════════════╗\n\n"
                        text += f"❌ Package Library Execution Failed\n\n"
                        text += f"Error: {error_str}\n\n"
                        text += "─" * 60 + "\n"
                        text += "\nPlease check:\n"
                        text += "• Package library script/config syntax\n"
                        text += "• Pre-request API endpoint availability\n"
                        text += "• Environment variables\n"
                        text += "• Authentication tokens\n"
                        content.update(text)
                    else:
                        log_output.write(f"✗ Test Error: {error_str}")
                        
                        text = f"╔═ TEST FAILED - {scenario_name} ════════════════════════╗\n\n"
                        text += f"❌ Test Failed\n\n"
                        text += f"Error: {error_str}\n\n"
                        text += "─" * 60 + "\n"
                        content.update(text)
                
                self.update_status(f"Test failed: {scenario_name}")
            update_ui(show_error_msg)

