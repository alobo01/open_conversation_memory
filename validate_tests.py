#!/usr/bin/env python3
"""
Test validation script for EmoRobCare
Validates test files for common issues without executing them
"""
import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

class TestValidator:
    def __init__(self):
        self.issues = []
        self.test_files = []

    def validate_imports(self, file_path: str, tree: ast.AST) -> List[str]:
        """Check if imports are valid"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    if self.is_problematic_import(module):
                        issues.append(f"Problematic import: {module}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if self.is_problematic_import(node.module):
                        issues.append(f"Problematic import: {node.module}")
        return issues

    def is_problematic_import(self, module: str) -> bool:
        """Check if module import might cause issues"""
        problematic_modules = [
            'vllm',  # Heavy ML dependency
            'torch',  # Heavy ML dependency
            'transformers',  # Heavy ML dependency
            'whisper',  # Heavy ML dependency
            'faster_whisper',  # Heavy ML dependency
        ]
        return any(module.startswith(problem) for problem in problematic_modules)

    def validate_test_structure(self, file_path: str, tree: ast.AST) -> List[str]:
        """Check test file structure"""
        issues = []
        has_test_class = False
        has_test_function = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith('Test'):
                    has_test_class = True
                    # Check if test methods exist
                    test_methods = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
                    if not test_methods:
                        issues.append(f"Test class {node.name} has no test methods")

            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    has_test_function = True

        if not has_test_class and not has_test_function:
            issues.append("No test functions or test classes found")

        return issues

    def validate_mock_usage(self, file_path: str, tree: ast.AST) -> List[str]:
        """Check if mocks are used correctly"""
        issues = []
        has_mock_import = False
        mock_usage = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if 'mock' in alias.name.lower():
                        has_mock_import = True
            elif isinstance(node, ast.ImportFrom):
                if node.module and 'mock' in node.module.lower():
                    has_mock_import = True
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'Mock' or node.func.attr == 'AsyncMock':
                        mock_usage = True

        if has_mock_import and not mock_usage:
            issues.append("Mock imported but not used")

        return issues

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a single test file"""
        result = {
            'file': file_path,
            'issues': [],
            'size': os.path.getsize(file_path),
            'lines': 0
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                result['lines'] = len(content.splitlines())

            tree = ast.parse(content)

            # Run various validations
            result['issues'].extend(self.validate_imports(file_path, tree))
            result['issues'].extend(self.validate_test_structure(file_path, tree))
            result['issues'].extend(self.validate_mock_usage(file_path, tree))

        except SyntaxError as e:
            result['issues'].append(f"Syntax error: {e}")
        except Exception as e:
            result['issues'].append(f"Error reading file: {e}")

        return result

    def validate_directory(self, test_dir: str) -> Dict[str, Any]:
        """Validate all test files in directory"""
        results = {
            'total_files': 0,
            'total_issues': 0,
            'files': []
        }

        for py_file in Path(test_dir).rglob("*.py"):
            if py_file.name.startswith('test_'):
                results['total_files'] += 1
                file_result = self.validate_file(str(py_file))
                results['files'].append(file_result)
                results['total_issues'] += len(file_result['issues'])

        return results

def main():
    validator = TestValidator()

    print("🔍 Validating EmoRobCare Test Files")
    print("=" * 50)

    # Validate unit tests
    print("\n📁 Validating unit tests...")
    unit_results = validator.validate_directory("tests/unit")

    print(f"Found {unit_results['total_files']} test files")

    for file_result in unit_results['files']:
        filename = os.path.basename(file_result['file'])
        if file_result['issues']:
            print(f"\n❌ {filename} ({file_result['lines']} lines, {file_result['size']} bytes)")
            for issue in file_result['issues']:
                print(f"   • {issue}")
        else:
            print(f"✅ {filename} ({file_result['lines']} lines)")

    # Summary
    print(f"\n📊 Summary:")
    print(f"Total files: {unit_results['total_files']}")
    print(f"Total issues: {unit_results['total_issues']}")

    if unit_results['total_issues'] == 0:
        print("🎉 All test files passed validation!")
        return 0
    else:
        print("⚠️  Some issues found. Please review and fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())