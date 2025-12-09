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
        height: 20;
        scrollbar-gutter: stable;
        margin: 1 0;
    }
    
    #log_panel {
        height: auto;
        display: none;
    }
    
    #log_panel.visible {
        display: block;
    }
    
    #api_visualizer {
        height: 30;
        border: solid $primary;
        display: none;
    }
    
    #api_visualizer.visible {
        display: block;
    }
    
    .api_flow {
        height: 100%;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("p", "show_projects", "Projects"),
        Binding("s", "show_scenarios", "Scenarios"),
        Binding("l", "show_load_test", "Load Test"),
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
                yield Label("📋 Main Menu", classes="section_title")
                yield Button("📁 Projects", id="btn_projects", classes="menu_button")
                yield Button("📝 Scenarios", id="btn_scenarios", classes="menu_button")
                yield Button("⚡ Load Test", id="btn_load_test", classes="menu_button")
                yield Button("📊 Results", id="btn_results", classes="menu_button")
                yield Button("🎨 UML Generator", id="btn_uml", classes="menu_button")
                yield Button("⚙️  Settings", id="btn_settings", classes="menu_button")
                yield Button("❌ Exit", id="btn_exit", classes="menu_button")
            
            # Right content panel
            with Vertical(id="content_panel"):
                yield Static("Welcome to REST API Simulator", id="content_area")
                with Container(id="api_visualizer"):
                    yield RichLog(id="api_flow", wrap=False, classes="api_flow")
                with Container(id="log_panel"):
                    yield Label("📋 Execution Log:", classes="section_title")
                    yield RichLog(id="log_output", wrap=True, highlight=True)
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
        • ⚡ TPS & Load Testing
        • 📊 Detailed Results & Reports
        • 🎨 UML Diagram Generation
        
        Quick Start:
        1. Select or create a project
        2. Create or select a scenario
        3. Run tests and view results
        
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
        elif button_id == "btn_load_test":
            self.show_load_test_screen()
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
        content = self.query_one("#content_area", Static)
        
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
        
        # Hide panels when returning to scenario list
        log_panel = self.query_one("#log_panel")
        api_visualizer = self.query_one("#api_visualizer")
        log_panel.remove_class("visible")
        api_visualizer.remove_class("visible")
        
        content = self.query_one("#content_area", Static)
        
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
    
    def show_load_test_screen(self):
        """Show load test configuration screen"""
        if not self.current_project:
            self.show_error("Please select a project first")
            return
        
        content = self.query_one("#content_area", Static)
        
        text = f"╔═ LOAD TEST - {self.current_project} ═══════════════════════╗\n\n"
        text += "Load Test Configuration:\n\n"
        text += "1. Select a scenario\n"
        text += "2. Configure test parameters:\n"
        text += "   • Duration (seconds)\n"
        text += "   • Target TPS (transactions per second)\n"
        text += "   • Ramp-up time (seconds)\n"
        text += "   • Max concurrent requests\n"
        text += "   • Load distribution (constant/linear/exponential)\n"
        text += "\n3. Start test and monitor real-time metrics\n"
        
        content.update(text)
        self.update_status("Load Test Configuration")
    
    def show_results_screen(self):
        """Show test results screen"""
        if not self.current_project:
            self.show_error("Please select a project first")
            return
        
        self.current_screen = "results"
        
        # Hide panels
        log_panel = self.query_one("#log_panel")
        api_visualizer = self.query_one("#api_visualizer")
        log_panel.remove_class("visible")
        api_visualizer.remove_class("visible")
        
        content = self.query_one("#content_area", Static)
        
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
        content = self.query_one("#content_area", Static)
        
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
        content = self.query_one("#content_area", Static)
        
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
    
    def action_show_load_test(self) -> None:
        """Show load test screen"""
        self.show_load_test_screen()
    
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
        
        content = self.query_one("#content_area", Static)
        full_path = self.project_manager.get_results_dir(self.current_project) / result_path
        
        try:
            with open(full_path, 'r') as f:
                result_data = json.load(f)
            
            text = f"╔═ RESULT DETAIL - {result_path} ═══════════════════════════╗\n\n"
            
            # Show summary
            if "scenario_name" in result_data:
                text += f"Scenario: {result_data['scenario_name']}\n"
            if "status" in result_data:
                text += f"Status: {result_data['status']}\n"
            if "duration_seconds" in result_data:
                text += f"Duration: {result_data['duration_seconds']:.2f}s\n"
            
            text += f"\nRequests:\n"
            text += f"  Total: {result_data.get('total_requests', 0)}\n"
            text += f"  Successful: {result_data.get('successful_requests', 0)}\n"
            text += f"  Failed: {result_data.get('failed_requests', 0)}\n"
            text += f"  Errors: {result_data.get('error_requests', 0)}\n"
            
            if "steps" in result_data:
                text += f"\nSteps ({len(result_data['steps'])}):\n"
                for idx, step in enumerate(result_data['steps'][:10], 1):
                    status_icon = "✓" if step.get('status') == 'success' else "✗"
                    text += f"  {status_icon} {idx}. {step.get('step_name', 'Unknown')}"
                    text += f" - {step.get('response_time_ms', 0):.0f}ms\n"
                
                if len(result_data['steps']) > 10:
                    text += f"\n  ... and {len(result_data['steps']) - 10} more steps\n"
            
            text += "\n" + "─" * 60 + "\n"
            text += "\nType 'back' to return to results list\n"
            
            content.update(text)
            self.update_status(f"Viewing: {result_path}")
            
            # Focus input
            self.query_one("#user_input", Input).focus()
            
        except Exception as e:
            self.show_error(f"Failed to load result: {str(e)}")
    
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
            uml_gen = UMLGenerator(self.current_project)
            result = uml_gen.generate_from_scenario(scenario_name)
            self.update_status(f"Generated UML for {scenario_name}: {result}")
        except Exception as e:
            self.show_error(f"Failed to generate UML: {str(e)}")
    
    def show_scenario_detail(self, scenario_name: str):
        """Show scenario details"""
        import json
        
        # Hide panels in detail view
        log_panel = self.query_one("#log_panel")
        api_visualizer = self.query_one("#api_visualizer")
        log_panel.remove_class("visible")
        api_visualizer.remove_class("visible")
        
        content = self.query_one("#content_area", Static)
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
            content = self.query_one("#content_area", Static)
            log_panel = self.query_one("#log_panel")
            log_output = self.query_one("#log_output", RichLog)
            api_visualizer = self.query_one("#api_visualizer")
            api_flow = self.query_one("#api_flow", RichLog)
            
            log_panel.add_class("visible")
            api_visualizer.add_class("visible")
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
            
            # Initialize scenario engine and execute
            engine = ScenarioEngine(host_config)
            
            # Progress callback
            def on_progress(step_name: str, current: int, total: int):
                def update_progress():
                    log_output = self.query_one("#log_output", RichLog)
                    log_output.write(f"Step {current}/{total}: {step_name}")
                update_ui(update_progress)
            
            # Execute scenario
            import asyncio
            result = asyncio.run(engine.execute_scenario(scenario, progress_callback=on_progress))
            
            # Visualize each step
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
            
        except Exception as e:
            def show_error_msg():
                log_output = self.query_one("#log_output", RichLog)
                log_output.write(f"✗ Error: {str(e)}")
                self.show_error(f"Test failed: {str(e)}")
            update_ui(show_error_msg)

