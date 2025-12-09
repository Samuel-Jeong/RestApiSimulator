"""Main TUI application"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Label, Input, TextLog, Select
from textual.binding import Binding
from textual import work
from pathlib import Path
import asyncio

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
    
    TextLog {
        border: solid $primary;
        height: 1fr;
        scrollbar-gutter: stable;
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
        text += "• Type project name to select\n"
        text += "• Type 'new:<name>' to create new project\n"
        
        content.update(text)
        self.update_status("Projects screen")
    
    def show_scenarios_screen(self):
        """Show scenarios management screen"""
        if not self.current_project:
            self.show_error("Please select a project first")
            return
        
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
        text += "• Type scenario name to view/run\n"
        text += "• Type 'new:<name>' to create new scenario\n"
        
        content.update(text)
        self.update_status(f"Scenarios | Project: {self.current_project}")
    
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
        
        content = self.query_one("#content_area", Static)
        
        results = self.project_manager.list_results(self.current_project)
        
        text = f"╔═ TEST RESULTS - {self.current_project} ═══════════════════╗\n\n"
        
        if results:
            text += "Recent Test Results:\n\n"
            for idx, result in enumerate(results[:20], 1):  # Show last 20
                text += f"  {idx}. {result}\n"
        else:
            text += "No test results found.\n"
        
        text += "\n" + "─" * 60 + "\n"
        text += "\nType result name to view details\n"
        
        content.update(text)
        self.update_status(f"Results | Project: {self.current_project}")
    
    def show_uml_screen(self):
        """Show UML generator screen"""
        if not self.current_project:
            self.show_error("Please select a project first")
            return
        
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
            text += "\nType scenario name to generate diagram\n"
        else:
            text += "No scenarios available.\n"
        
        content.update(text)
        self.update_status("UML Generator")
    
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

