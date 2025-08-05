#!/usr/bin/env python3
"""
Test runner script
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run command and handle results"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*50}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with return code {result.returncode}")
        return False
    else:
        print(f"✅ {description} passed")
        return True


def main():
    """Main function"""
    # Ensure we're in the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 Base Agent Engineering - Test Suite")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Test command list
    test_commands = [
        ("python -m pytest tests/unit/ -v", "Unit Tests"),
        ("python -m pytest tests/unit/test_config.py -v", "Config Tests"),
        ("python -m pytest tests/unit/test_rag_workflow.py -v", "RAG Workflow Tests"),
        ("python -m pytest tests/unit/test_app.py -v", "FastAPI App Tests"),
        ("python -m pytest --cov=config --cov=src --cov=app --cov-report=term", "Coverage Report"),
    ]
    
    # Optional code quality checks
    quality_commands = [
        ("python -m black --check .", "Code Formatting Check"),
        ("python -m isort --check-only .", "Import Sorting Check"),
        ("python -m flake8 .", "Code Style Check"),
    ]
    
    success_count = 0
    total_count = len(test_commands)
    
    # Run tests
    for command, description in test_commands:
        if run_command(command, description):
            success_count += 1
    
    # Run code quality checks (optional)
    print(f"\n{'='*50}")
    print("Running Code Quality Checks (Optional)")
    print(f"{'='*50}")
    
    for command, description in quality_commands:
        try:
            run_command(command, description)
        except Exception as e:
            print(f"⚠️  {description} skipped: {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Passed: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())