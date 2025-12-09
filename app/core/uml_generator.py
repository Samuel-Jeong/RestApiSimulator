"""UML diagram generator for scenarios"""

from typing import List
from ..models.scenario import Scenario, ScenarioStep


class UMLGenerator:
    """Generates UML diagrams from scenarios"""
    
    @staticmethod
    def generate_sequence_diagram(scenario: Scenario) -> str:
        """
        Generate PlantUML sequence diagram from scenario
        
        Returns:
            PlantUML diagram as string
        """
        lines = ["@startuml"]
        lines.append(f"title {scenario.name}")
        
        if scenario.description:
            lines.append(f"note over Client: {scenario.description}")
        
        lines.append("")
        lines.append("actor User")
        lines.append("participant Client")
        lines.append("participant \"API Server\" as API")
        lines.append("")
        
        # Generate sequence for each step
        for idx, step in enumerate(scenario.steps, 1):
            lines.append(f"== Step {idx}: {step.name} ==")
            
            # Delay before
            if step.delay_before > 0:
                lines.append(f"Client -> Client: Wait {step.delay_before}s")
            
            # Request
            method_color = UMLGenerator._get_method_color(step.method.value)
            lines.append(f"User -> Client: Initiate {step.name}")
            lines.append(f"Client -> API: {step.method.value} {step.path}")
            
            # Response
            if step.assertions:
                expected_status = next(
                    (a.value for a in step.assertions if a.field == "status"),
                    "2XX"
                )
                lines.append(f"API --> Client: {expected_status} Response")
            else:
                lines.append(f"API --> Client: Response")
            
            # Assertions
            if step.assertions:
                lines.append("Client -> Client: Validate assertions")
                for assertion in step.assertions[:3]:  # Show first 3 assertions
                    lines.append(f"note right: {assertion.field} {assertion.operator.value} {assertion.value}")
            
            # Extract variables
            if step.extract:
                lines.append("Client -> Client: Extract variables")
                for var_name in step.extract.keys():
                    lines.append(f"note right: {var_name}")
            
            # Delay after
            if step.delay_after > 0:
                lines.append(f"Client -> Client: Wait {step.delay_after}s")
            
            lines.append("")
        
        lines.append("@enduml")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_flowchart(scenario: Scenario) -> str:
        """
        Generate PlantUML activity diagram (flowchart) from scenario
        
        Returns:
            PlantUML diagram as string
        """
        lines = ["@startuml"]
        lines.append(f"title {scenario.name} - Flowchart")
        lines.append("")
        lines.append("start")
        lines.append("")
        
        for idx, step in enumerate(scenario.steps, 1):
            # Step action
            lines.append(f":{step.name};")
            lines.append(f"note right")
            lines.append(f"  {step.method.value} {step.path}")
            lines.append(f"end note")
            
            # Assertions check
            if step.assertions:
                lines.append(f"if (Assertions pass?) then (yes)")
                
                if step.extract:
                    lines.append(f"  :Extract variables;")
                
                if not step.skip_on_failure:
                    lines.append(f"else (no)")
                    lines.append(f"  :Fail scenario;")
                    lines.append(f"  stop")
                    lines.append(f"endif")
                else:
                    lines.append(f"else (no)")
                    lines.append(f"  :Log failure;")
                    lines.append(f"  :Continue;")
                    lines.append(f"endif")
            
            lines.append("")
        
        lines.append("stop")
        lines.append("@enduml")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_text_diagram(scenario: Scenario) -> str:
        """
        Generate simple text-based diagram (ASCII art)
        
        Returns:
            ASCII diagram as string
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"  Scenario: {scenario.name}")
        if scenario.description:
            lines.append(f"  Description: {scenario.description}")
        lines.append("=" * 70)
        lines.append("")
        
        for idx, step in enumerate(scenario.steps, 1):
            lines.append(f"[{idx}] {step.name}")
            lines.append(f"    │")
            lines.append(f"    ├─► Method: {step.method.value}")
            lines.append(f"    ├─► Path: {step.path}")
            
            if step.delay_before > 0:
                lines.append(f"    ├─► Delay Before: {step.delay_before}s")
            
            if step.body:
                lines.append(f"    ├─► Body: {len(str(step.body))} bytes")
            
            if step.assertions:
                lines.append(f"    ├─► Assertions: {len(step.assertions)}")
                for assertion in step.assertions:
                    lines.append(f"    │   • {assertion.field} {assertion.operator.value} {assertion.value}")
            
            if step.extract:
                lines.append(f"    ├─► Extract Variables:")
                for var_name, field in step.extract.items():
                    lines.append(f"    │   • {var_name} ← {field}")
            
            if step.delay_after > 0:
                lines.append(f"    └─► Delay After: {step.delay_after}s")
            else:
                lines.append(f"    └─►")
            
            if idx < len(scenario.steps):
                lines.append(f"        │")
                lines.append(f"        ▼")
            
            lines.append("")
        
        lines.append("=" * 70)
        lines.append(f"  Total Steps: {len(scenario.steps)}")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_method_color(method: str) -> str:
        """Get color for HTTP method"""
        colors = {
            "GET": "#00AA00",
            "POST": "#0000AA",
            "PUT": "#AA8800",
            "PATCH": "#AA8800",
            "DELETE": "#AA0000"
        }
        return colors.get(method, "#000000")
    
    @staticmethod
    def save_diagram(diagram: str, output_path: str, format: str = "puml"):
        """Save diagram to file"""
        from pathlib import Path
        
        # Ensure parent directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(diagram)

