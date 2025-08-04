#!/usr/bin/env python3
"""
Drone Application Startup Script
This script automatically cleans up any existing Tello processes before starting the main application.
"""

import subprocess
import sys
import os

def run_cleanup():
    """Run the Tello cleanup utility."""
    print("Running Tello cleanup...")
    try:
        result = subprocess.run(
            [sys.executable, 'utils/tello_cleanup.py'],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Cleanup failed: {e}")
        print(e.stderr)
        return False

def main():
    """Main startup function."""
    print("Drone Application Startup")
    print("=" * 30)
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("❌ Error: main.py not found. Please run this script from the drone_project directory.")
        sys.exit(1)
    
    # Run cleanup
    if not run_cleanup():
        print("❌ Cleanup failed. Please run manually: python3 utils/tello_cleanup.py")
        sys.exit(1)
    
    print("\n" + "=" * 30)
    print("Starting drone application...")
    print("=" * 30)
    
    # Start the main application
    try:
        subprocess.run([sys.executable, 'main.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Application failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✅ Application stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 