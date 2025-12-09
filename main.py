#!/usr/bin/env python3
"""REST API Simulator - Main Entry Point"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.lock import ProcessLock
from app.ui.app import RestApiSimulatorApp


def main():
    """Main entry point"""
    
    # Prevent duplicate execution
    with ProcessLock():
        # Run TUI application
        app = RestApiSimulatorApp()
        app.run()


if __name__ == "__main__":
    main()

