#!/usr/bin/env python3
"""
Test runner script for EmoRobCare comprehensive testing
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main test runner"""
    print("EmoRobCare Comprehensive Test Suite")
    print("="*60)

    # Check if we're in the right directory
    if not Path("tests").exists():
        print("ERROR: tests directory not found. Please run from project root.")
        sys.exit(1)

    # Count test files
    test_files = list(Path("tests").rglob("*.py"))
    print(f"Found {len(test_files)} test files with {sum(f.stat().st_size for f in test_files)} bytes of test code")

    # Try different Python commands
    python_cmds = ["python", "python3", "py"]
    python_cmd = None

    for cmd in python_cmds:
        try:
            result = subprocess.run(f"{cmd} --version", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                python_cmd = cmd
                print(f"Using Python: {result.stdout.strip()}")
                break
        except:
            continue

    if not python_cmd:
        print("ERROR: No Python interpreter found")
        sys.exit(1)

    # Install pytest if not available
    print("\nChecking pytest availability...")
    if not run_command(f"{python_cmd} -m pytest --version", "Check pytest"):
        print("Installing pytest...")
        if not run_command(f"{python_cmd} -m pip install pytest pytest-mock pytest-asyncio pytest-cov", "Install pytest"):
            print("ERROR: Failed to install pytest")
            sys.exit(1)

    # Run tests with different strategies
    test_strategies = [
        {
            "name": "Unit Tests",
            "cmd": f"{python_cmd} -m pytest tests/unit/ -v --tb=short",
            "description": "Run all unit tests"
        },
        {
            "name": "LLM Service Tests",
            "cmd": f"{python_cmd} -m pytest tests/unit/test_llm_service.py -v --tb=short",
            "description": "Test LLM service functionality"
        },
        {
            "name": "Emotion Service Tests",
            "cmd": f"{python_cmd} -m pytest tests/unit/test_emotion_service_comprehensive.py -v --tb=short",
            "description": "Test emotion service functionality"
        },
        {
            "name": "Safety Service Tests",
            "cmd": f"{python_cmd} -m pytest tests/unit/test_safety_service_comprehensive.py -v --tb=short",
            "description": "Test safety service functionality"
        },
        {
            "name": "Router Tests",
            "cmd": f"{python_cmd} -m pytest tests/unit/test_*router*.py -v --tb=short",
            "description": "Test API routers"
        },
        {
            "name": "Integration Tests",
            "cmd": f"{python_cmd} -m pytest tests/integration/ -v --tb=short",
            "description": "Run integration tests"
        },
        {
            "name": "E2E Tests",
            "cmd": f"{python_cmd} -m pytest tests/e2e/ -v --tb=short",
            "description": "Run end-to-end tests"
        }
    ]

    # Run test strategies
    results = {}
    for strategy in test_strategies:
        print(f"\n{'#'*60}")
        print(f"TEST STRATEGY: {strategy['name']}")
        print('#'*60)

        success = run_command(strategy['cmd'], strategy['description'])
        results[strategy['name']] = success

        if success:
            print(f"[PASSED] {strategy['name']}: PASSED")
        else:
            print(f"[FAILED] {strategy['name']}: FAILED")

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUITE SUMMARY")
    print('='*60)

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    for name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        try:
            print(f"{name:<30} {status}")
        except UnicodeEncodeError:
            print(f"{name:<30} {status.encode('ascii', 'ignore').decode('ascii')}")

    print(f"\nOverall: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! The app is working and functional.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
