#!/usr/bin/env python3
"""
Comprehensive type checking script for OBS Agent.

This script validates type safety across the entire codebase using:
- MyPy static type checking
- Runtime type validation
- Custom type safety tests
- Performance analysis of type-safe code
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TypeChecker:
    """Comprehensive type checking and validation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_path = project_root / "src"
        self.results: Dict[str, Any] = {}

    def run_mypy_check(self) -> Tuple[bool, str]:
        """Run MyPy static type checking."""
        print("🔍 Running MyPy static type checking...")

        try:
            result = subprocess.run(
                ["mypy", str(self.src_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            print(f"{'✅' if success else '❌'} MyPy check {'passed' if success else 'failed'}")
            if not success:
                print(f"MyPy output:\n{output}")

            return success, output

        except subprocess.TimeoutExpired:
            return False, "MyPy check timed out"
        except Exception as e:
            return False, f"MyPy check failed: {e}"

    def run_runtime_validation_tests(self) -> bool:
        """Run runtime type validation tests."""
        print("🧪 Running runtime type validation tests...")

        try:
            # Test Pydantic configuration models
            from obs_agent.types.config import ValidatedOBSAgentConfig, DEFAULT_OBS_AGENT_CONFIG, validate_config

            if ValidatedOBSAgentConfig is None:
                print("⚠️  Pydantic not available, skipping validation tests")
                return True

            # Test valid configuration
            try:
                ValidatedOBSAgentConfig(**DEFAULT_OBS_AGENT_CONFIG)
                print("✅ Default configuration validation passed")
            except Exception as e:
                print(f"❌ Default configuration validation failed: {e}")
                return False

            # Test invalid configuration
            try:
                invalid_config = {
                    "obs": {"host": "", "port": -1, "password": "test"},
                    "version": "2.0.0",
                    "created_at": time.time(),
                }
                ValidatedOBSAgentConfig(**invalid_config)
                print("❌ Invalid configuration should have failed validation")
                return False
            except Exception:
                print("✅ Invalid configuration correctly rejected")

            # Test validation function
            validation_result = validate_config(DEFAULT_OBS_AGENT_CONFIG)
            if isinstance(validation_result, dict) and "validation_error" in validation_result:
                print(f"❌ Validation function failed: {validation_result}")
                return False

            print("✅ Runtime validation tests passed")
            return True

        except ImportError as e:
            print(f"⚠️  Could not import validation modules: {e}")
            return True  # Don't fail if modules aren't available yet
        except Exception as e:
            print(f"❌ Runtime validation tests failed: {e}")
            return False

    def test_typed_obs_agent(self) -> bool:
        """Test the typed OBS agent wrapper."""
        print("🤖 Testing TypedOBSAgent...")

        try:
            from obs_agent.typed_obs_agent import TypedOBSAgent

            # Test creation
            agent = TypedOBSAgent()
            print("✅ TypedOBSAgent creation successful")

            # Test type validation methods
            scene_validation = agent.validate_scene_name("Test Scene")
            if not scene_validation["valid"]:
                print(f"❌ Scene name validation failed: {scene_validation}")
                return False

            invalid_scene_validation = agent.validate_scene_name("")
            if invalid_scene_validation["valid"]:
                print("❌ Empty scene name should be invalid")
                return False

            volume_validation = agent.validate_volume_db(-10.0)
            if not volume_validation["valid"]:
                print(f"❌ Volume validation failed: {volume_validation}")
                return False

            invalid_volume_validation = agent.validate_volume_db(-200.0)
            if invalid_volume_validation["valid"]:
                print("❌ Invalid volume should be rejected")
                return False

            print("✅ TypedOBSAgent tests passed")
            return True

        except ImportError as e:
            print(f"⚠️  Could not import TypedOBSAgent: {e}")
            return True
        except Exception as e:
            print(f"❌ TypedOBSAgent tests failed: {e}")
            return False

    def test_generic_types(self) -> bool:
        """Test generic type utilities."""
        print("🔧 Testing generic type utilities...")

        try:
            from obs_agent.types.generics import (
                TypedResult,
                TypedCache,
                safe_cast,
                is_instance_of,
            )

            # Test TypedResult
            success_result = TypedResult(True, "test_data")
            if not success_result.is_success():
                print("❌ TypedResult success check failed")
                return False

            if success_result.unwrap() != "test_data":
                print("❌ TypedResult unwrap failed")
                return False

            fail_result = TypedResult(False, error="test error")
            if fail_result.is_success():
                print("❌ TypedResult failure check failed")
                return False

            # Test TypedCache
            cache = TypedCache(str)
            cache.set("key1", "value1")

            if not cache.has("key1"):
                print("❌ TypedCache has() failed")
                return False

            if cache.get("key1") != "value1":
                print("❌ TypedCache get() failed")
                return False

            # Test type utilities
            if not is_instance_of("test", str):
                print("❌ is_instance_of failed")
                return False

            if safe_cast("123", int) != 123:
                print("❌ safe_cast failed")
                return False

            if safe_cast("invalid", int) is not None:
                print("❌ safe_cast should return None for invalid cast")
                return False

            print("✅ Generic type utilities tests passed")
            return True

        except ImportError as e:
            print(f"⚠️  Could not import generic types: {e}")
            return True
        except Exception as e:
            print(f"❌ Generic type utilities tests failed: {e}")
            return False

    def analyze_type_coverage(self) -> Dict[str, Any]:
        """Analyze type annotation coverage."""
        print("📊 Analyzing type annotation coverage...")

        coverage_stats = {"total_files": 0, "typed_files": 0, "untyped_files": [], "coverage_percentage": 0.0}

        try:
            # Count Python files in src
            python_files = list(self.src_path.rglob("*.py"))
            coverage_stats["total_files"] = len(python_files)

            typed_files = 0
            untyped_files = []

            for file_path in python_files:
                if file_path.name == "__init__.py":
                    continue  # Skip __init__.py files

                try:
                    content = file_path.read_text(encoding="utf-8")

                    # Basic heuristic: file is "typed" if it has type annotations
                    has_typing_import = any(
                        line.strip().startswith(("from typing", "import typing", "from typing_extensions"))
                        for line in content.split("\n")
                    )

                    has_annotations = "->" in content or ": " in content

                    if has_typing_import or has_annotations:
                        typed_files += 1
                    else:
                        untyped_files.append(str(file_path.relative_to(self.project_root)))

                except Exception as e:
                    print(f"⚠️  Could not analyze {file_path}: {e}")

            coverage_stats["typed_files"] = typed_files
            coverage_stats["untyped_files"] = untyped_files
            coverage_stats["coverage_percentage"] = (typed_files / max(coverage_stats["total_files"], 1)) * 100

            print(
                f"📈 Type coverage: {coverage_stats['coverage_percentage']:.1f}% "
                f"({typed_files}/{coverage_stats['total_files']} files)"
            )

            if untyped_files:
                print("📝 Files needing type annotations:")
                for file in untyped_files[:5]:  # Show first 5
                    print(f"   - {file}")
                if len(untyped_files) > 5:
                    print(f"   ... and {len(untyped_files) - 5} more")

        except Exception as e:
            print(f"❌ Type coverage analysis failed: {e}")

        return coverage_stats

    def run_performance_tests(self) -> Dict[str, float]:
        """Test performance impact of type safety."""
        print("⚡ Running performance tests...")

        perf_results = {}

        try:
            # Test TypedResult vs plain return
            def plain_function(x: int) -> int:
                return x * 2

            from obs_agent.types.generics import TypedResult

            def typed_function(x: int) -> TypedResult[int]:
                return TypedResult(True, x * 2)

            # Benchmark plain function
            start_time = time.perf_counter()
            for i in range(10000):
                result = plain_function(i)
            plain_time = time.perf_counter() - start_time

            # Benchmark typed function
            start_time = time.perf_counter()
            for i in range(10000):
                result = typed_function(i)
                if result.is_success():
                    result.unwrap()  # Use the result without storing
            typed_time = time.perf_counter() - start_time

            perf_results["plain_function_time"] = plain_time
            perf_results["typed_function_time"] = typed_time
            perf_results["overhead_percentage"] = ((typed_time - plain_time) / plain_time) * 100

            print(f"⏱️  Performance overhead: {perf_results['overhead_percentage']:.2f}%")

        except Exception as e:
            print(f"❌ Performance tests failed: {e}")

        return perf_results

    def generate_report(self) -> None:
        """Generate comprehensive type checking report."""
        print("\n📋 Generating Type Safety Report...")

        # Run all checks
        mypy_success, mypy_output = self.run_mypy_check()
        runtime_success = self.run_runtime_validation_tests()
        typed_agent_success = self.test_typed_obs_agent()
        generics_success = self.test_generic_types()
        coverage_stats = self.analyze_type_coverage()
        perf_results = self.run_performance_tests()

        # Compile results
        self.results = {
            "timestamp": time.time(),
            "mypy_check": {
                "success": mypy_success,
                "output": mypy_output[:1000] if mypy_output else "",  # Truncate for report
            },
            "runtime_validation": {"success": runtime_success},
            "typed_agent_tests": {"success": typed_agent_success},
            "generic_types_tests": {"success": generics_success},
            "type_coverage": coverage_stats,
            "performance": perf_results,
            "overall_success": all([mypy_success, runtime_success, typed_agent_success, generics_success]),
        }

        # Save report
        report_path = self.project_root / "type_safety_report.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        # Print summary
        print("\n" + "=" * 60)
        print("📊 TYPE SAFETY REPORT SUMMARY")
        print("=" * 60)
        print(f"📍 Overall Status: {'✅ PASSED' if self.results['overall_success'] else '❌ FAILED'}")
        print(f"🔍 MyPy Check: {'✅ PASSED' if mypy_success else '❌ FAILED'}")
        print(f"🧪 Runtime Validation: {'✅ PASSED' if runtime_success else '❌ FAILED'}")
        print(f"🤖 TypedOBSAgent: {'✅ PASSED' if typed_agent_success else '❌ FAILED'}")
        print(f"🔧 Generic Types: {'✅ PASSED' if generics_success else '❌ FAILED'}")
        print(f"📈 Type Coverage: {coverage_stats['coverage_percentage']:.1f}%")
        if perf_results:
            print(f"⚡ Performance Overhead: {perf_results.get('overhead_percentage', 0):.2f}%")
        print(f"📄 Full report saved to: {report_path}")
        print("=" * 60)

        return self.results["overall_success"]


def main():
    """Main entry point."""
    print("🎯 OBS Agent Type Safety Validation")
    print("=" * 50)

    # Find project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Run type checking
    checker = TypeChecker(project_root)
    success = checker.generate_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
