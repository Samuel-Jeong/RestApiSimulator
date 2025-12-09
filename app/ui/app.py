"""Main TUI application"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Label, Input, RichLog, Select
from textual.binding import Binding
from textual import work
from pathlib import Path
import asyncio
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
    }
    
    #content_panel {
        width: 1fr;
        padding: 1;
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
    }
    
    #uml_section {
        height: 50%;
        min-height: 20;
        max-height: 50%;
    }
    
    #log_section {
        height: 50%;
        min-height: 20;
        max-height: 50%;
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
        self.log_widget = None
        self.current_screen = "welcome"  # Track current screen
        self.selected_scenario = None  # Track selected scenario
    
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
    
    def show_projects_screen(self):
        """Show projects management screen"""
        self.current_screen = "projects"
        
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        
        projects = self.project_manager.list_projects()
        
        text = "╔═ PROJECT MANAGEMENT ═══════════════════════════════════╗\n\n"
        
        if projects:
            text += "Available Projects:\n\n"
            for idx, project in enumerate(projects, 1):
                marker = "▶" if project == self.current_project else " "
                text += f"{marker} {idx}. {project}\n"
        else:
            text += "No projects found. Create a new project to get started.\n"
        
        text += "\n" + "─" * 60 + "\n"
        text += "\nActions:\n"
        text += "• Type project number or name to select\n"
        text += "• Type 'new:<name>' to create new project\n"
        
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
        
        scenarios = self.project_manager.list_scenarios(self.current_project)
        
        text = f"╔═ SCENARIOS - {self.current_project} ═══════════════════════╗\n\n"
        
        if scenarios:
            text += "Available Scenarios:\n\n"
            for idx, scenario in enumerate(scenarios, 1):
                text += f"  {idx}. {scenario}\n"
        else:
            text += "No scenarios found in this project.\n"
        
        text += "\n" + "─" * 60 + "\n"
        text += "\nActions:\n"
        text += "• Type scenario number or name to view/run\n"
        text += "• Type 'new:<name>' to create new scenario\n"
        
        content.update(text)
        self.update_status(f"Scenarios | Project: {self.current_project}")
        
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
        
        results = self.project_manager.list_results(self.current_project)
        
        text = f"╔═ TEST RESULTS - {self.current_project} ═══════════════════╗\n\n"
        
        if results:
            text += "Recent Test Results:\n\n"
            for idx, result in enumerate(results[:20], 1):  # Show last 20
                text += f"  {idx}. {result}\n"
        else:
            text += "No test results found.\n"
            text += "\nRun some scenarios to generate results.\n"
        
        text += "\n" + "─" * 60 + "\n"
        text += "\nType result number to view details\n"
        text += "Example: 1 (to view first result)\n"
        
        content.update(text)
        self.update_status(f"Results | Project: {self.current_project}")
        
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
            
            hosts = self.project_manager.load_hosts_config(self.current_project)
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
        
        # Check if creating new project
        if user_input.startswith("new:"):
            project_name = user_input[4:].strip()
            if project_name:
                self.project_manager.create_project(project_name)
                self.current_project = project_name
                self.update_status(f"Created and selected project: {project_name}")
                self.show_projects_screen()
            else:
                self.show_error("Project name cannot be empty")
            return
        
        # Check if number input
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(projects):
                self.current_project = projects[idx]
                self.update_status(f"Selected project: {self.current_project}")
                self.show_projects_screen()
            else:
                self.show_error(f"Invalid project number: {user_input}")
            return
        
        # Check if project name
        if user_input in projects:
            self.current_project = user_input
            self.update_status(f"Selected project: {self.current_project}")
            self.show_projects_screen()
        else:
            self.show_error(f"Project not found: {user_input}")
    
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
                # Create basic scenario file
                scenario_path = Path("projects") / self.current_project / "scenario" / f"{scenario_name}.json"
                scenario_path.parent.mkdir(parents=True, exist_ok=True)
                
                basic_scenario = {
                    "name": scenario_name,
                    "description": "New scenario",
                    "steps": []
                }
                
                import json
                with open(scenario_path, 'w') as f:
                    json.dump(basic_scenario, f, indent=2)
                
                self.update_status(f"Created scenario: {scenario_name}")
                self.show_scenarios_screen()
            else:
                self.show_error("Scenario name cannot be empty")
            return
        
        # Check if number input
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(scenarios):
                scenario_name = scenarios[idx]
                self.selected_scenario = scenario_name
                self.show_scenario_detail(scenario_name)
            else:
                self.show_error(f"Invalid scenario number: {user_input}")
            return
        
        # Check if scenario name
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
        
        # Check if back command
        if user_input.lower() == "back":
            # Hide analysis container
            analysis_container = self.query_one("#analysis_container")
            analysis_container.remove_class("visible")
            self.show_results_screen()
            return
        
        # Check if number input
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(results):
                result_path = results[idx]
                self.show_result_detail(result_path)
            else:
                self.show_error(f"Invalid result number: {user_input}")
            return
        
        self.show_error(f"Unknown command: {user_input}")
    
    def show_result_detail(self, result_path: str):
        """Show detailed result information"""
        import json
        import statistics
        
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
            with open(full_path, 'r') as f:
                result_data = json.load(f)
            
            # Get scenario result
            scenario_result = result_data.get('scenario_results', [{}])[0]
            steps = scenario_result.get('steps', [])
            
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
            
            # Header
            analysis_content.write("╔═ RESULT ANALYSIS ══════════════════════════════╗")
            analysis_content.write(f"{scenario_result.get('scenario_name', 'Test')}")
            analysis_content.write("")
            
            status_emoji = "✓" if scenario_result.get('status') == 'success' else "✗"
            analysis_content.write(f"{status_emoji} Status: {scenario_result.get('status', 'unknown').upper()}")
            analysis_content.write(f"⏱  Duration: {scenario_result.get('duration_seconds', 0):.3f}s")
            analysis_content.write(f"📅 Time: {result_data.get('created_at', 'N/A')}")
            analysis_content.write("")
            
            # Request Summary
            analysis_content.write("═══ REQUEST SUMMARY ═══")
            analysis_content.write(f"Total Requests:    {scenario_result.get('total_requests', 0)}")
            analysis_content.write(f"✓ Successful:      {scenario_result.get('successful_requests', 0)}")
            analysis_content.write(f"✗ Failed:          {scenario_result.get('failed_requests', 0)}")
            analysis_content.write(f"⚠ Errors:          {scenario_result.get('error_requests', 0)}")
            analysis_content.write("")
            
            # Response Time Metrics
            analysis_content.write("═══ RESPONSE TIME METRICS ═══")
            analysis_content.write(f"Average:           {avg_response:.2f}ms")
            analysis_content.write(f"Min:               {min_response:.2f}ms")
            analysis_content.write(f"Max:               {max_response:.2f}ms")
            analysis_content.write(f"P50 (median):      {p50:.2f}ms")
            analysis_content.write(f"P95:               {p95:.2f}ms")
            analysis_content.write(f"P99:               {p99:.2f}ms")
            analysis_content.write("")
            
            # Assertion Results
            analysis_content.write("═══ ASSERTION RESULTS ═══")
            analysis_content.write(f"Total Assertions:  {total_assertions}")
            analysis_content.write(f"✓ Passed:          {passed_assertions}")
            analysis_content.write(f"✗ Failed:          {failed_assertions}")
            analysis_content.write("")
            
            # Variables
            variables = scenario_result.get('variables', {})
            if variables:
                analysis_content.write("═══ EXTRACTED VARIABLES ═══")
                for key, value in variables.items():
                    analysis_content.write(f"  {key:<20} = {value}")
                analysis_content.write("")
            
            # Step Summary
            analysis_content.write("═══ STEP SUMMARY ═══")
            analysis_content.write("─" * 60)
            analysis_content.write(f"{'#':<3} {'Step Name':<32} {'Status':<6} {'Time':<10}")
            analysis_content.write("─" * 60)
            
            for idx, step in enumerate(steps, 1):
                status_icon = "✓" if step.get('status') == 'success' else "✗"
                step_name = step.get('step_name', 'Unknown')
                if len(step_name) > 32:
                    step_name = step_name[:29] + "..."
                response_time = f"{step.get('response_time_ms', 0):.1f}ms"
                analysis_content.write(f"{idx:<3} {step_name:<32} {status_icon:<6} {response_time:<10}")
            
            analysis_content.write("─" * 60)
            analysis_content.write("")
            analysis_content.write("Type 'back' to return to results list")
            
            # Clear right panel
            api_flow.clear()
            log_output.clear()
            
            # Generate UML in API visualizer
            api_flow.write("╔" + "═" * 58 + "╗")
            api_flow.write("║" + " " * 20 + "API FLOW DIAGRAM" + " " * 22 + "║")
            api_flow.write("╚" + "═" * 58 + "╝")
            api_flow.write("")
            
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
                api_flow.write(f"[{idx}] {step_name}")
                api_flow.write(f"    │")
                api_flow.write(f"    ├─► {method}")
                
                # Response
                api_flow.write(f"    │")
                api_flow.write(f"    ◄─┤ [{status_icon}] {status_code} | {response_time:.1f}ms")
                
                # Assertions
                if step.get('assertion_details'):
                    passed = step.get('assertions_passed', 0)
                    failed = step.get('assertions_failed', 0)
                    api_flow.write(f"    │   ✓{passed} ✗{failed}")
                
                # Extracted variables
                if step.get('extracted_variables'):
                    vars_str = ", ".join(f"{k}={v}" for k, v in step['extracted_variables'].items())
                    if len(vars_str) > 40:
                        vars_str = vars_str[:37] + "..."
                    api_flow.write(f"    │   Var: {vars_str}")
                
                api_flow.write(f"    │")
            
            api_flow.write("")
            api_flow.write("✓ Flow completed")
            
            # Detailed logs
            log_output.write("═" * 58)
            log_output.write(f"STEP-BY-STEP DETAILS")
            log_output.write("═" * 58)
            log_output.write("")
            
            for idx, step in enumerate(steps, 1):
                status_icon = "✓" if step.get('status') == 'success' else "✗"
                
                log_output.write("─" * 58)
                log_output.write(f"{status_icon} [{idx}] {step.get('step_name', 'Unknown Step')}")
                log_output.write("─" * 58)
                
                log_output.write(f"Method:      {step.get('method', 'GET')}")
                url = step.get('url', 'N/A')
                if len(url) > 50:
                    url = url[:47] + "..."
                log_output.write(f"URL:         {url}")
                log_output.write(f"Status:      {step.get('status_code', 'N/A')}")
                log_output.write(f"Time:        {step.get('response_time_ms', 0):.2f}ms")
                
                # Request body (compact)
                if step.get('request_body'):
                    log_output.write("")
                    log_output.write("Request:")
                    import json as json_lib
                    body_str = json_lib.dumps(step['request_body'], indent=2)
                    lines = body_str.split('\n')
                    if len(lines) > 8:
                        log_output.write('\n'.join(lines[:8]))
                        log_output.write(f"  ... ({len(lines) - 8} lines)")
                    else:
                        log_output.write(body_str)
                
                # Response body (compact)
                if step.get('response_body'):
                    log_output.write("")
                    log_output.write("Response:")
                    import json as json_lib
                    body_str = json_lib.dumps(step['response_body'], indent=2)
                    lines = body_str.split('\n')
                    if len(lines) > 10:
                        log_output.write('\n'.join(lines[:10]))
                        log_output.write(f"  ... ({len(lines) - 10} lines)")
                    else:
                        log_output.write(body_str)
                
                # Assertions
                if step.get('assertion_details'):
                    log_output.write("")
                    log_output.write("Assertions:")
                    for assertion in step['assertion_details']:
                        icon = "✓" if assertion.get('passed') else "✗"
                        msg = assertion.get('message', 'N/A')
                        if len(msg) > 50:
                            msg = msg[:47] + "..."
                        log_output.write(f"  {icon} {msg}")
                
                # Extracted variables
                if step.get('extracted_variables'):
                    log_output.write("")
                    log_output.write("Variables:")
                    for key, value in step['extracted_variables'].items():
                        log_output.write(f"  {key} = {value}")
                
                # Error message
                if step.get('error_message'):
                    log_output.write("")
                    log_output.write(f"⚠ Error: {step['error_message']}")
                
                log_output.write("")
            
            log_output.write("═" * 58)
            log_output.write("END OF LOG")
            log_output.write("═" * 58)
            
            self.update_status(f"Analyzing: {result_path}")
            
            # Focus input
            self.query_one("#user_input", Input).focus()
            
        except Exception as e:
            self.show_error(f"Failed to load result: {str(e)}")
            import traceback
            traceback.print_exc()
    
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
        import json
        
        # Hide analysis container
        analysis_container = self.query_one("#analysis_container")
        analysis_container.remove_class("visible")
        
        # Show main content
        content = self.query_one("#content_area", Static)
        content.display = True
        scenario_path = Path("projects") / self.current_project / "scenario" / f"{scenario_name}.json"
        
        try:
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
            # Load hosts configuration
            hosts = self.project_manager.load_hosts_config(self.current_project)
            if not hosts:
                def show_err():
                    self.show_error("No hosts configured in hosts.json")
                update_ui(show_err)
                return
            
            # Use first host by default
            host_name = list(hosts.keys())[0]
            host_config = hosts[host_name]
            
            # Load scenario
            scenario = self.project_manager.load_scenario(self.current_project, scenario_name)
            
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
                engine = ScenarioEngine(host_config)
                
                # Progress callback
                def on_progress(step_name: str, current: int, total: int):
                    def update_progress():
                        log_output = self.query_one("#log_output", RichLog)
                        log_output.write(f"Step {current}/{total}: {step_name}")
                    update_ui(update_progress)
                
                # Execute scenario
                result = asyncio.run(engine.execute_scenario(scenario, progress_callback=on_progress))
            
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
                            log_output.write(f"   Error: {step.error_message}")
                    
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
            
        except Exception as e:
            def show_error_msg():
                log_output = self.query_one("#log_output", RichLog)
                log_output.write(f"✗ Error: {str(e)}")
                self.show_error(f"Test failed: {str(e)}")
            update_ui(show_error_msg)

