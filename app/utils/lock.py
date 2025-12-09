"""Process lock manager to prevent duplicate execution"""

import os
import sys
import psutil
from pathlib import Path
from typing import Optional


class ProcessLock:
    """Prevents multiple instances of the application from running"""
    
    def __init__(self, lock_file: str = ".app.lock"):
        self.lock_file = Path(lock_file).resolve()
        self.pid: Optional[int] = None
    
    def acquire(self) -> bool:
        """
        Acquire lock. Returns True if successful, False if another instance is running.
        """
        if self.lock_file.exists():
            # Check if the process is still running
            try:
                with open(self.lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if process exists
                if psutil.pid_exists(old_pid):
                    try:
                        process = psutil.Process(old_pid)
                        # Check if it's our application
                        cmdline = ' '.join(process.cmdline())
                        if 'main.py' in cmdline or 'RestApiSimulator' in cmdline:
                            return False
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Old PID doesn't exist, remove stale lock
                self.lock_file.unlink()
            except (ValueError, IOError):
                # Corrupted lock file, remove it
                self.lock_file.unlink()
        
        # Create lock file
        try:
            self.pid = os.getpid()
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
            return True
        except IOError:
            return False
    
    def release(self):
        """Release the lock"""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Only remove if it's our lock
                if pid == self.pid:
                    self.lock_file.unlink()
            except (ValueError, IOError):
                pass
    
    def __enter__(self):
        if not self.acquire():
            print("⚠️  Another instance of REST API Simulator is already running!")
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

