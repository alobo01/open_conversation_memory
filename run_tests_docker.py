#!/usr/bin/env python3
"""
Docker-based test runner for EmoRobCare
"""
import subprocess
import sys
import os
from pathlib import Path

def build_test_image():
    """Build the Docker test image"""
    print("🏗️ Building test Docker image...")

    try:
        result = subprocess.run([
            'docker', 'build',
            '-f', 'Dockerfile.test',
            '-t', 'emorobcare-test',
            '.'
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("✅ Test image built successfully")
            return True
        else:
            print("❌ Failed to build test image")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("❌ Test image build timed out")
        return False
    except Exception as e:
        print(f"❌ Error building test image: {e}")
        return False

def run_tests_in_docker(test_path=None):
    """Run tests in the Docker container"""
    print("🧪 Running tests in Docker...")

    cmd = ['docker', 'run', '--rm', 'emorobcare-test']

    if test_path:
        cmd.extend(['python', '-m', 'pytest', test_path, '-v', '--tb=short'])
    else:
        cmd.extend(['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'])

    try:
        result = subprocess.run(cmd, text=True, timeout=300)

        if result.returncode == 0:
            print("✅ All tests passed")
        else:
            print("❌ Some tests failed")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Test execution timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test_files():
    """Run specific test files one by one"""
    test_files = [
        'tests/unit/test_memory_service.py',
        'tests/unit/test_extraction_service.py',
        'tests/unit/test_background_tasks.py',
        'tests/unit/test_emotion_service_comprehensive.py',
        'tests/unit/test_safety_service_comprehensive.py',
        'tests/unit/test_knowledge_graph_router_comprehensive.py',
        'tests/unit/test_asr_router_comprehensive.py',
        'tests/unit/test_llm_service.py',
        'tests/e2e/test_conversation_flow_comprehensive.py'
    ]

    results = {}

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🧪 Running {test_file}...")
            success = run_tests_in_docker(test_file)
            results[test_file] = success
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} {test_file}")
        else:
            print(f"⚠️ Test file not found: {test_file}")
            results[test_file] = None

    return results

def main():
    """Main test runner"""
    print("🚀 EmoRobCare Docker Test Runner")
    print("=" * 50)

    # Build test image
    if not build_test_image():
        return 1

    # Run tests
    print("\n📋 Running test suite...")
    results = run_specific_test_files()

    # Summary
    print(f"\n📊 Test Summary:")
    passed = sum(1 for success in results.values() if success is True)
    failed = sum(1 for success in results.values() if success is False)
    missing = sum(1 for success in results.values() if success is None)
    total = len(results)

    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Missing: {missing}")

    if failed == 0 and missing == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed or missing")
        return 1

if __name__ == "__main__":
    sys.exit(main())